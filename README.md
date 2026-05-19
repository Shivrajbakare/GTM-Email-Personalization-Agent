# GTM Email Personalization Agent
> Interactly.ai — GTM Automation & AI Engineer Internship Task

A 4-step pipeline that finds real healthcare prospects, enriches their data via website scraping,
generates hyper-personalized cold emails using Claude AI, and delivers a shareable HTML report.

---

## The 4-Step Pipeline

```
Step 1: You research 10 real prospects  (manual, 1–2 hrs)
           ↓
Step 2: python enrich.py               (scrapes websites → Claude extracts pain points)
           ↓
Step 3: python main.py                 (Claude generates emails → Airtable → Slack)
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
# Open .env — paste your ANTHROPIC_API_KEY (required)
# Optionally add Airtable + Slack credentials
```

**Get Anthropic API key:** [console.anthropic.com](https://console.anthropic.com) → API Keys → Create

**Get Airtable credentials (optional):**
1. Free account at [artable.com](https://airtable.com)
2. New Base → Table named `Emails` with these fields:
   - Name, Title, Company, Industry, Pain Point, LinkedIn URL (Single line text)
   - Subject Line, Email Body (Long text)
   - Status, Generated At (Single line text)
3. Developer hub → Personal access tokens → Create token
4. Base ID: click Help → API Documentation → copy from URL

**Get Slack webhook (optional):**
[api.slack.com/apps](https://api.slack.com/apps) → Create App → Incoming Webhooks → Add to channel

---

## Step 1 — Find 10 Real Prospects

Read `STEP1_FIND_PROSPECTS.md` for exact LinkedIn search strings and tips.

Fill `prospects.csv` with:
```
name,title,company,website,linkedin_url,industry,pain_point
Sarah Chen,CMO,WellBridge Medical Group,https://wellbridgemedical.com,https://linkedin.com/in/...,Healthcare,
```

**Leave pain_point blank** — the enrichment script fills it.

---

## Step 2 — Enrich Prospect Data

```bash
python enrich.py
```

Visits each company's website, scrapes public content, uses Claude Haiku to extract
their specific pain point. Outputs `prospects_enriched.csv`.

---

## Step 3 — Generate Emails

```bash
python main.py
```

For each prospect:
- Detects seniority from title (executive vs manager) → switches tone automatically
- Generates a personalized email via Claude Sonnet
- Logs to Airtable CRM
- Posts summary to Slack

Outputs `output_emails.csv`.

---

## Step 4 — Build HTML Report

```bash
python report.py
```

Outputs `report.html` — open in browser. This is what you screenshot for your submission.

---

## How the AI Works

### Role-Aware Prompt Logic

| Title Contains | Tone | Focus |
|---|---|---|
| CMO, CEO, VP, Director… | Strategic, concise | ROI, revenue impact, competitive edge |
| Manager, Coordinator… | Practical, empathetic | Time saved, workflow relief, team impact |

### Two-Stage Claude Usage

| Stage | Model | Why |
|---|---|---|
| Enrichment (enrich.py) | claude-3-5-haiku | Fast, cheap — high volume processing |
| Email generation (main.py) | claude-3-5-sonnet | Higher quality for final output |

---

## Sample Output

```
═══════════════════════════════════════════════════════════
  🚀 GTM Email Agent  —  10 prospects
═══════════════════════════════════════════════════════════

[1/10] Sarah Chen  |  CMO  |  WellBridge Medical Group
  ✉  Subject : "When Did Re-Engaging Patients Get This Hard?"
  📋 Airtable: ✓

[2/10] James Okafor  |  VP Operations  |  CareLink Urgent Care
  ✉  Subject : "Your Staff Spends 6 Hours/Day on Patient Calls"
  📋 Airtable: ✓
...
═══════════════════════════════════════════════════════════
  ✅ Done in 18.4s
  📊 10/10 emails generated  |  0 failed
  📁 Output → output_emails.csv
═══════════════════════════════════════════════════════════
```

---

## Project Structure

```
gtm-pipeline/
├── STEP1_FIND_PROSPECTS.md   # How to find real prospects
├── prospects.csv             # Input: fill with real people
├── enrich.py                 # Step 2: website scrape + Claude pain point extraction
├── main.py                   # Step 3: email generation → Airtable → Slack
├── report.py                 # Step 4: HTML report generator
├── requirements.txt
├── .env.example
└── README.md
─── Auto-generated ───────────────────────────────────────
├── prospects_enriched.csv    # After enrich.py
├── output_emails.csv         # After main.py
└── report.html               # After report.py
```

---

## Deliverables Coverage

| Interactly JD Deliverable | This Project |
|---|---|
| Claude Code agents personalizing emails | ✅ Claude Sonnet, role-aware prompting |
| Apollo → HubSpot sync | ✅ CSV (Apollo format) → Airtable (CRM) |
| Weekly pipeline report to Slack | ✅ Slack webhook with subject line preview |
| Stale deal alerts / triggers | 🔜 Easy to add with scheduled cron |
| LinkedIn monitor | 🔜 Foundation laid — enrichment reads LinkedIn URLs |

---

*Built by [Your Name] · [LinkedIn] · IIT Kanpur*
