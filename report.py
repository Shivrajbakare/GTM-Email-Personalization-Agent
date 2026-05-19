"""
Step 4 — Report Generator
===========================
Reads output_emails.csv and generates a clean, shareable HTML report.
This is what you screenshot and attach to your submission email.

Run: python report.py
Output: report.html
"""

import csv
import os
from datetime import datetime, timezone


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GTM Email Agent — Pipeline Report</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #f4f6f9;
    color: #1a1a2e;
    padding: 32px 20px;
  }}

  /* ── Header ── */
  .header {{
    max-width: 860px;
    margin: 0 auto 36px;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%);
    border-radius: 16px;
    padding: 36px 40px;
    color: white;
  }}
  .header-tag {{
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #7ec8e3;
    margin-bottom: 10px;
  }}
  .header h1 {{
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 8px;
  }}
  .header p {{
    font-size: 14px;
    color: rgba(255,255,255,0.65);
    margin-bottom: 24px;
  }}
  .stats {{
    display: flex;
    gap: 24px;
    flex-wrap: wrap;
  }}
  .stat {{
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 10px;
    padding: 14px 20px;
    min-width: 110px;
  }}
  .stat-value {{
    font-size: 26px;
    font-weight: 700;
    color: #7ec8e3;
  }}
  .stat-label {{
    font-size: 11px;
    color: rgba(255,255,255,0.5);
    margin-top: 2px;
    text-transform: uppercase;
    letter-spacing: 1px;
  }}

  /* ── Cards ── */
  .cards {{
    max-width: 860px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }}
  .card {{
    background: white;
    border-radius: 14px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    overflow: hidden;
    border: 1px solid #e8ecf0;
  }}
  .card-header {{
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    padding: 22px 26px 16px;
    border-bottom: 1px solid #f0f2f5;
    gap: 16px;
  }}
  .prospect-info {{
    flex: 1;
  }}
  .prospect-name {{
    font-size: 17px;
    font-weight: 700;
    color: #1a1a2e;
  }}
  .prospect-meta {{
    font-size: 13px;
    color: #6b7280;
    margin-top: 3px;
  }}
  .prospect-meta span {{
    color: #0f3460;
    font-weight: 500;
  }}
  .badge {{
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
    padding: 4px 10px;
    border-radius: 20px;
    white-space: nowrap;
    flex-shrink: 0;
  }}
  .badge-exec {{
    background: #fff3e0;
    color: #e65100;
    border: 1px solid #ffcc80;
  }}
  .badge-manager {{
    background: #e8f5e9;
    color: #2e7d32;
    border: 1px solid #a5d6a7;
  }}

  /* ── Pain Point ── */
  .pain-point {{
    padding: 10px 26px;
    background: #fafbfc;
    font-size: 12.5px;
    color: #6b7280;
    border-bottom: 1px solid #f0f2f5;
  }}
  .pain-point strong {{
    color: #1a1a2e;
  }}

  /* ── Email Content ── */
  .email-section {{
    padding: 20px 26px 24px;
  }}
  .subject-label {{
    font-size: 10px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #9ca3af;
    margin-bottom: 6px;
  }}
  .subject-line {{
    font-size: 15px;
    font-weight: 700;
    color: #0f3460;
    margin-bottom: 18px;
    padding: 10px 14px;
    background: #f0f5ff;
    border-left: 3px solid #0f3460;
    border-radius: 0 8px 8px 0;
  }}
  .body-label {{
    font-size: 10px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #9ca3af;
    margin-bottom: 8px;
  }}
  .email-body {{
    font-size: 14px;
    line-height: 1.75;
    color: #374151;
    white-space: pre-wrap;
    background: #fafbfc;
    border: 1px solid #e8ecf0;
    border-radius: 10px;
    padding: 16px 18px;
  }}

  /* ── LinkedIn ── */
  .linkedin-row {{
    padding: 12px 26px;
    border-top: 1px solid #f0f2f5;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .linkedin-row a {{
    font-size: 12px;
    color: #0077b5;
    text-decoration: none;
    font-weight: 500;
  }}
  .linkedin-row a:hover {{ text-decoration: underline; }}

  /* ── Footer ── */
  .footer {{
    max-width: 860px;
    margin: 32px auto 0;
    text-align: center;
    font-size: 12px;
    color: #9ca3af;
    padding: 20px;
    border-top: 1px solid #e8ecf0;
  }}
</style>
</head>
<body>

<div class="header">
  <div class="header-tag">Interactly.ai · GTM Automation Task</div>
  <h1>📬 Email Personalization Pipeline</h1>
  <p>Groq Llama 3.3-powered cold outreach · Role-aware tone · Airtable CRM logged</p>
  <div class="stats">
    <div class="stat">
      <div class="stat-value">{total}</div>
      <div class="stat-label">Prospects</div>
    </div>
    <div class="stat">
      <div class="stat-value">{success}</div>
      <div class="stat-label">Emails Generated</div>
    </div>
    <div class="stat">
      <div class="stat-value">Llama 3.3</div>
      <div class="stat-label">AI Model</div>
    </div>
    <div class="stat">
      <div class="stat-value">{generated_at}</div>
      <div class="stat-label">Generated</div>
    </div>
  </div>
</div>

<div class="cards">
{cards}
</div>

<div class="footer">
  Built with Llama 3.3 (Groq Free Tier) · Airtable CRM · Slack Notifications<br>
  GTM Automation & AI Engineer — Internship Task Submission
</div>

</body>
</html>"""


CARD_TEMPLATE = """
  <div class="card">
    <div class="card-header">
      <div class="prospect-info">
        <div class="prospect-name">{name}</div>
        <div class="prospect-meta">
          <span>{title}</span> · {company} · {industry}
        </div>
      </div>
      <span class="badge {badge_class}">{badge_label}</span>
    </div>
    {pain_point_row}
    <div class="email-section">
      <div class="subject-label">Subject Line</div>
      <div class="subject-line">{subject}</div>
      <div class="body-label">Email Body</div>
      <div class="email-body">{body}</div>
    </div>
    {linkedin_row}
  </div>"""


EXEC_KEYWORDS = {
    "CMO", "CEO", "CTO", "CFO", "COO", "VP", "Vice President",
    "Chief", "Director", "President", "Founder", "Head", "Partner"
}


def main():
    input_file = "output_emails.csv"
    output_file = "report.html"

    if not os.path.exists(input_file):
        print(f"❌ {input_file} not found. Run main.py first.")
        return

    with open(input_file, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"\n  📊 Building report for {len(rows)} emails...")

    cards_html = ""
    success_count = 0

    for row in rows:
        title = row.get("title", "")
        is_exec = any(kw in title for kw in EXEC_KEYWORDS)
        badge_class = "badge-exec" if is_exec else "badge-manager"
        badge_label = "Executive" if is_exec else "Manager"

        pain = row.get("pain_point", "").strip()
        if pain:
            pain_point_row = f'<div class="pain-point"><strong>Pain point:</strong> {pain}</div>'
        else:
            pain_point_row = ""

        linkedin = row.get("linkedin_url", "").strip()
        if linkedin:
            linkedin_row = (
                f'<div class="linkedin-row">'
                f'<svg width="14" height="14" viewBox="0 0 24 24" fill="#0077b5">'
                f'<path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 '
                f'0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 '
                f'3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 '
                f'0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 '
                f'2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452z"/>'
                f'</svg> '
                f'<a href="{linkedin}" target="_blank">View LinkedIn Profile</a>'
                f'</div>'
            )
        else:
            linkedin_row = ""

        # Check variations of subject column names
        subject_content = row.get("subject_line", "").strip()
        if not subject_content:
            subject_content = row.get("subject", "").strip()

        # Check variations of body column names
        body_content = row.get("email_body", "").strip()
        if not body_content:
            body_content = row.get("body", "").strip()
            
        if subject_content and body_content:
            success_count += 1

        # Format cards securely
        cards_html += CARD_TEMPLATE.format(
            name=row.get("name", "N/A"),
            title=title if title else "N/A",
            company=row.get("company", "N/A"),
            industry=row.get("industry", "N/A"),
            badge_class=badge_class,
            badge_label=badge_label,
            pain_point_row=pain_point_row,
            subject=subject_content if subject_content else "No Subject Generated",
            body=body_content if body_content else "No Email Body Generated",
            linkedin_row=linkedin_row
        )

    # Get current timestamp for report header metadata
    generated_at_str = datetime.now(timezone.utc).strftime('%H:%M UTC')

    # Build final HTML content structure
    final_html = HTML_TEMPLATE.format(
        total=len(rows),
        success=success_count,
        generated_at=generated_at_str,
        cards=cards_html
    )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"  ✅ Report compile successful!")
    print(f"  📁 Output generated → {output_file}\n")


if __name__ == "__main__":
    main()
