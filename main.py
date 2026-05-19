import csv
import os
import json
import time
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY", "")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "")
AIRTABLE_TABLE   = os.getenv("AIRTABLE_TABLE_NAME", "Emails")
SLACK_WEBHOOK    = os.getenv("SLACK_WEBHOOK_URL", "")

# ── FIXED URL ─────────────────────────────────────────────────────────────────
# ❌ Old (broken): f"https://airtable.com{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE}"
# ✅ Fixed:        f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE}"
AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE}"

EXEC_KEYWORDS = {
    "CMO", "CEO", "CTO", "CFO", "CHRO", "COO",
    "VP", "Vice President", "Chief", "Director",
    "President", "Founder", "Head", "Partner", "Senior Director"
}

GENERIC_SUBJECTS = {
    "inefficient follow-ups", "follow-up workflow challenges",
    "patient engagement overhaul", "optimizing labor sourcing",
    "solving admin overhead", "quick question", "following up",
    "checking in", "touching base"
}


# ── 1. Email Generator ────────────────────────────────────────────────────────

def generate_email(prospect: dict, attempt: int = 1) -> dict:
    name         = prospect.get("name", "").strip()
    title        = prospect.get("title", "")
    company      = prospect.get("company", "")
    industry     = prospect.get("industry", "Healthcare")
    pain_point   = prospect.get("pain_point", "operational inefficiencies")
    company_desc = prospect.get("company_description", "")
    why_fit      = prospect.get("why_interactly_fits", "")
    first_name   = name.split()[0] if name else "there"

    is_exec = any(kw in title for kw in EXEC_KEYWORDS)

    if is_exec:
        tone  = "Direct and strategic. Max 2 sentences per paragraph. No filler."
        cta   = "15-min executive briefing"
        focus = "ROI, cost-per-patient-interaction, revenue recovery"
    else:
        tone  = "Warm and practical. Show you understand their day-to-day grind."
        cta   = "15-min live demo"
        focus = "hours saved per week, staff workload, simpler follow-ups"

    context = ""
    if company_desc:
        context += f"\nWhat they do: {company_desc}"
    if why_fit:
        context += f"\nWhy Interactly fits: {why_fit}"

    retry_note = ""
    if attempt == 2:
        retry_note = (
            "\n\nCRITICAL: Be MORE specific. Your last attempt was too generic. "
            f"The subject line MUST mention '{company}' or a specific number or a specific outcome. "
            "Do NOT use vague phrases."
        )

    prompt = f"""You are a senior SDR at Interactly.ai, a US healthcare AI startup.
Interactly.ai automates patient engagement and cuts admin overhead for US healthcare providers.

Write a cold outreach email to:
  Name:       {name}
  Title:      {title}
  Company:    {company}
  Pain point: {pain_point}{context}

Tone: {tone}
Focus: {focus}{retry_note}

STRICT RULES:
1. Subject: must feel written SPECIFICALLY for {company} — reference company name OR a number OR a specific outcome. Under 9 words.
   ❌ BAD: "Inefficient Follow-ups", "Patient Engagement Overhaul", "Quick Question"
   ✅ GOOD: "{company} Losing Patients Between Visits?", "Cutting {company}'s Admin Load in Half", "Why {company}'s Follow-ups Are Falling Through"
2. First sentence: must say the company name or something specific to their situation
3. Paragraph 1 (2 sentences): Make them feel understood — their exact pain
4. Paragraph 2 (2 sentences): One specific thing Interactly does that solves it
5. Paragraph 3 (1-2 sentences): Soft CTA — offer a {cta}, suggest a specific weekday
6. Body word count: 90–120 words
7. Sign off: Best, [Your Name] | Interactly.ai
8. BANNED words: revolutionize, cutting-edge, leverage, synergy, streamline, seamless, game-changer

Return ONLY a JSON object, nothing else:
{{"subject": "...", "body": "..."}}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.65 if attempt == 1 else 0.88,
        response_format={"type": "json_object"}
    )

    raw = response.choices[0].message.content.strip()
    if "```" in raw:
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else parts[0]
        if raw.lower().startswith("json"):
            raw = raw[4:]
    result = json.loads(raw.strip())

    # Quality check — retry if subject is generic or body is too short
    subject_lower = result.get("subject", "").lower()
    body_words    = len(result.get("body", "").split())
    is_generic    = any(g in subject_lower for g in GENERIC_SUBJECTS)
    is_too_short  = body_words < 55

    if (is_generic or is_too_short) and attempt == 1:
        print(f"\n      ⚠  Generic output (subject: \"{result.get('subject','')}\"), retrying...", end=" ", flush=True)
        time.sleep(1.5)
        return generate_email(prospect, attempt=2)

    return result


# ── 2. Airtable Logger ────────────────────────────────────────────────────────

def log_to_airtable(prospect: dict, email: dict) -> bool:
    if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
        print("skipped (no credentials)")
        return False

    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type":  "application/json"
    }
    record = {
        "fields": {
            "Name":         prospect.get("name", ""),
            "Title":        prospect.get("title", ""),
            "Company":      prospect.get("company", ""),
            "Industry":     prospect.get("industry", ""),
            "Pain Point":   prospect.get("pain_point", ""),
            "LinkedIn URL": prospect.get("linkedin_url", ""),
            "Subject Line": email["subject"],
            "Email Body":   email["body"],
            "Status":       "Ready to Send",
            "Generated At": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        }
    }

    try:
        res = requests.post(AIRTABLE_URL, headers=headers, json=record, timeout=10)
        if res.status_code == 200:
            print("logged ✓")
            return True

        # Show exact error
        print(f"\n      ❌ Airtable HTTP {res.status_code}")
        try:
            err = res.json()
            print(f"      Error: {json.dumps(err)[:300]}")
        except Exception:
            print(f"      Error: {res.text[:300]}")

        if res.status_code == 401:
            print("      → Fix: API key is wrong. Get a new one from airtable.com/account")
        elif res.status_code == 404:
            print(f"      → Fix: Base ID wrong. URL tried: {AIRTABLE_URL}")
        elif res.status_code == 422:
            print("      → Fix: A field name doesn't exist in your table.")
            print("      → Run: python test_airtable.py  to find which fields are missing")
        return False

    except Exception as e:
        print(f"\n      ❌ Airtable exception: {e}")
        return False


# ── 3. Slack Summary ──────────────────────────────────────────────────────────

def post_slack_summary(total, success, failed, duration, samples):
    if not SLACK_WEBHOOK:
        return

    subjects = "\n".join(
        f"  • _{e['company']}_ → *\"{e['subject']}\"*"
        for e in samples[:3]
    )
    message = {
        "blocks": [
            {"type": "header",
             "text": {"type": "plain_text", "text": "📬 GTM Email Agent — Pipeline Complete"}},
            {"type": "section",
             "fields": [
                 {"type": "mrkdwn", "text": f"*Prospects:*\n`{total}`"},
                 {"type": "mrkdwn", "text": f"*Generated:*\n`{success}`"},
                 {"type": "mrkdwn", "text": f"*Failed:*\n`{failed}`"},
                 {"type": "mrkdwn", "text": f"*Duration:*\n`{duration:.1f}s`"}
             ]},
            {"type": "section",
             "text": {"type": "mrkdwn", "text": f"*Sample subjects:*\n{subjects}"}},
            {"type": "section",
             "text": {"type": "mrkdwn",
                      "text": f"✅ Airtable logged | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"}}
        ]
    }
    try:
        res = requests.post(SLACK_WEBHOOK, json=message, timeout=10)
        if res.status_code != 200:
            print(f"  [Slack] ❌ {res.status_code}: {res.text[:100]}")
    except Exception as e:
        print(f"  [Slack] ❌ {e}")


# ── 4. Main ───────────────────────────────────────────────────────────────────

def main():
    input_file = "prospects_enriched.csv" if os.path.exists("prospects_enriched.csv") else "prospects.csv"
    print(f"\n  📂 Input: {input_file}")

    with open(input_file, newline="", encoding="utf-8") as f:
        prospects = list(csv.DictReader(f))

    total   = len(prospects)
    success = 0
    failed  = 0
    results = []
    samples = []
    start   = time.time()

    print(f"\n{'═'*60}")
    print(f"  🚀 GTM Email Agent (Groq)  ·  {total} prospects")
    print(f"{'═'*60}\n")

    for i, prospect in enumerate(prospects, 1):
        name    = prospect.get("name", "")
        company = prospect.get("company", "")
        title   = prospect.get("title", "")

        print(f"[{i}/{total}] {name}  ·  {title}  ·  {company}")

        try:
            print(f"      ✉  Generating email ...", end=" ", flush=True)
            email = generate_email(prospect)
            print(f"done")
            print(f"      📌 Subject: \"{email['subject']}\"")

            print(f"      📋 Airtable: ", end="", flush=True)
            log_to_airtable(prospect, email)

            results.append({
                "name":       name,
                "title":      title,
                "company":    company,
                "industry":   prospect.get("industry", ""),
                "linkedin":   prospect.get("linkedin_url", ""),
                "pain_point": prospect.get("pain_point", ""),
                "subject":    email["subject"],
                "body":       email["body"]
            })

            if len(samples) < 3:
                samples.append({"company": company, "subject": email["subject"]})

            success += 1

        except json.JSONDecodeError as e:
            print(f"\n      ❌ JSON error: {e}")
            failed += 1
        except Exception as e:
            print(f"\n      ❌ Error: {e}")
            failed += 1

        print()
        time.sleep(1.2)  # Groq free tier rate limit buffer

    if results:
        with open("output_emails.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
            writer.writeheader()
            writer.writerows(results)

    duration = time.time() - start

    print(f"{'═'*60}")
    print(f"  ✅ Done in {duration:.1f}s")
    print(f"  📊 {success}/{total} generated  |  {failed} failed")
    print(f"  📁 Saved → output_emails.csv")
    print(f"{'═'*60}\n")

    post_slack_summary(total, success, failed, duration, samples)
    if SLACK_WEBHOOK:
        print("  📣 Slack posted!\n")
    print("  ▶  Next: python report.py\n")


if __name__ == "__main__":
    main()