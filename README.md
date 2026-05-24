# GTM Email Personalization Agent
> Interactly.ai — GTM Automation & AI Engineer Internship Task

A 4-step pipeline that finds real healthcare prospects, enriches their data via website scraping,
generates hyper-personalized cold emails using **Groq (Llama 3.3-70b)**, and delivers a shareable HTML report.

---

## The 4-Step Pipeline

```
Step 1: You research 10+ real prospects  (manual, 1–2 hrs)
           ↓
Step 2: python enrich.py               (scrapes websites → Groq extracts pain points)
           ↓
Step 3: python main.py                 (Groq generates emails → Airtable CRM → Slack)
           ↓
Step 4: python report.py               (builds HTML report to screenshot & share)
```

---

## Setup (10 minutes)

### Install dependencies
```bash
pip install -r requirements.txt
```

### Configure environment
```bash
cp .env.example .env
```

**Required:**
- `GROQ_API_KEY` — free at [console.groq.com](https://console.groq.com) → API Keys → Create

**Optional (for CRM + alerts):**
- `AIRTABLE_API_KEY`, `AIRTABLE_BASE_ID`, `AIRTABLE_TABLE_NAME`
- `SLACK_WEBHOOK_URL`

**Get Airtable credentials:**
1. Free account at [airtable.com](https://airtable.com)
2. New Base → Table named `Emails` with these fields:

| Field Name | Type |
|---|---|
| Name, Title, Company, Industry, LinkedIn URL, Status, Generated At | Single line text |
| Pain Point, Subject Line, Email Body | Long text |

3. Developer hub → Personal access tokens → Create token (needs `data.records:read` + `data.records:write`)
4. Base ID: Help → API Documentation → copy `appXXXXXXXXXXXXXX` from URL

**Get Slack webhook:**
[api.slack.com/apps](https://api.slack.com/apps) → Create App → Incoming Webhooks → Add to channel

---

## Step 1 — Find Real Prospects

Read `STEP1_FIND_PROSPECTS.md` for LinkedIn search strings and tips.

Fill `prospects.csv`:
```
name,title,company,website,linkedin_url,industry,pain_point
Sarah Chen,CMO,WellBridge Medical Group,https://wellbridgemedical.com,https://linkedin.com/in/...,Healthcare,
```

**Leave `pain_point` blank** — enrich.py fills it automatically.

> You can use more than 10 prospects — the pipeline handles any number. 10 is the minimum for the task.

---

## Step 2 — Enrich Prospect Data

```bash
python enrich.py
```

Visits each company's website, scrapes public content, uses **Groq Llama 3.3** to extract:
- What the company actually does
- Their specific pain point for Interactly.ai's pitch
- Why Interactly fits them

Outputs `prospects_enriched.csv`. Skips prospects where `pain_point` is already filled.

---

## Step 3 — Generate Emails

```bash
python main.py
```

For each prospect:
- Detects seniority from title (executive vs manager) → switches tone automatically
- Generates personalized email via **Groq Llama 3.3-70b**
- Auto-retries if subject line is too generic
- Logs to Airtable CRM
- Posts summary to Slack

Outputs `output_emails.csv`.

---

## Step 4 — Build HTML Report

```bash
python report.py
```

Outputs `report.html` — open in browser and screenshot for your submission.

## How the AI Works

### Role-Aware Prompt Logic

| Title Contains | Tone | Focus |
|---|---|---|
| CMO, CEO, VP, Director, Chief… | Direct and strategic, max 2 sentences/paragraph | ROI, revenue impact, competitive edge |
| Manager, Coordinator… | Warm and practical | Hours saved, workflow relief, team impact |

### Email Quality Guard

Every generated email is checked automatically:
- Subject line must reference company name, a number, or a specific outcome
- Body must be 90–120 words
- If output is too generic → auto-retries with higher temperature and stricter instructions

### Model Used

| Stage | Model | Why |
|---|---|---|
| Enrichment (enrich.py) | Groq Llama 3.3-70b | Fast, free, good at structured JSON extraction |
| Email generation (main.py) | Groq Llama 3.3-70b | High quality, free tier, handles role-aware prompting well |

> **Note:** Originally designed with Claude (Anthropic). Groq is used here as a free-tier alternative with equivalent output quality for this use case.

---

## Sample Terminal Output

```
═══════════════════════════════════════════════════════════
   GTM Email Agent (Groq)  ·  10 prospects
═══════════════════════════════════════════════════════════

[1/10] Sarah Chen  ·  CMO  ·  WellBridge Medical Group
        Generating email ... done
       Subject: "WellBridge Losing Patients Between Visits?"
       Airtable: logged ✓

[2/10] James Okafor  ·  VP Operations  ·  CareLink Urgent Care
       Generating email ... done
       Subject: "CareLink's Staff Spends 6 Hours/Day on Calls"
       Airtable: logged ✓
...
═══════════════════════════════════════════════════════════
  Done in 18.4s
  10/10 generated  |  0 failed
  Saved → output_emails.csv
═══════════════════════════════════════════════════════════
```

---

## Project Structure

```
gtm-pipeline/
├── prospects.csv                # Input: fill with real people
├── enrich.py                    # Step 2: website scrape + Groq pain point extraction
├── main.py                      # Step 3: email generation → Airtable → Slack
├── report.py                    # Step 4: HTML report generator
├── requirements.txt
└── README.md
─── Auto-generated ──────────────────────────────────────────
├── prospects_enriched.csv       # After enrich.py
├── output_emails.csv            # After main.py
└── report.html                  # After report.py
```

---

## Deliverables Coverage

| Interactly JD Deliverable | This Project |
|---|---|
| AI agents personalizing emails |  Groq Llama 3.3, role-aware prompting, quality guard |
| Apollo → HubSpot sync | CSV (Apollo format) → Airtable (CRM) |
| Weekly pipeline report to Slack |  Slack webhook with subject line previews |
| Stale deal alerts / triggers | Easy to add with scheduled cron + status field |
| LinkedIn monitor |  Foundation laid — enrichment reads LinkedIn URLs |

---

*Built for Interactly.ai GTM Automation Internship · IIT Kanpur*"# GTM-Email-Personalization-Agent" 
