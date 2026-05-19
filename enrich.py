import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY", "")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "")
AIRTABLE_TABLE   = os.getenv("AIRTABLE_TABLE_NAME", "Emails")

# ── CORRECT URL FORMAT ────────────────────────────────────────────────────────
# Common mistake: using airtable.com instead of api.airtable.com
# Common mistake: missing /v0/ in the path
AIRTABLE_URL  = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE}"
META_URL      = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables"

REQUIRED_FIELDS = [
    "Name", "Title", "Company", "Industry",
    "Pain Point", "LinkedIn URL", "Subject Line",
    "Email Body", "Status", "Generated At"
]

def check_env():
    print("\n── Checking .env variables ──────────────────────────")
    ok = True
    for var in ["AIRTABLE_API_KEY", "AIRTABLE_BASE_ID", "AIRTABLE_TABLE_NAME"]:
        val = os.getenv(var, "")
        if val:
            print(f"  ✅ {var} = {val[:12]}...")
        else:
            print(f"  ❌ {var} is MISSING from .env")
            ok = False
    return ok

def check_connection():
    print("\n── Testing Airtable API connection ──────────────────")
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}

    # Test: list records (GET)
    res = requests.get(
        AIRTABLE_URL,
        headers=headers,
        params={"maxRecords": 1},
        timeout=10
    )

    print(f"  URL used : {AIRTABLE_URL}")
    print(f"  Status   : {res.status_code}")

    if res.status_code == 200:
        print("  ✅ Connection successful!")
        data = res.json()
        print(f"  Records in table: {len(data.get('records', []))}")
        return True
    elif res.status_code == 401:
        print("  ❌ UNAUTHORIZED — API key is wrong or expired")
        print("     Go to airtable.com/account → Developer hub → Personal access tokens")
        print("     Make sure the token has: data.records:read AND data.records:write")
    elif res.status_code == 404:
        print("  ❌ NOT FOUND — Base ID or Table name is wrong")
        print(f"     Base ID used: {AIRTABLE_BASE_ID}")
        print(f"     Table name  : {AIRTABLE_TABLE}")
        print("     Base ID should look like: appXXXXXXXXXXXXXX")
    else:
        print(f"  ❌ Error: {res.text[:300]}")
    return False

def check_fields():
    print("\n── Checking table fields ────────────────────────────")
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }

    res = requests.get(META_URL, headers=headers, timeout=10)

    if res.status_code != 200:
        print(f"  ⚠ Could not read table metadata: {res.status_code}")
        print(f"  Make sure your token has schema.bases:read permission")
        return

    tables = res.json().get("tables", [])
    target = next((t for t in tables if t["name"] == AIRTABLE_TABLE), None)

    if not target:
        print(f"  ❌ Table '{AIRTABLE_TABLE}' not found in base")
        print(f"  Tables found: {[t['name'] for t in tables]}")
        return

    existing = {f["name"] for f in target.get("fields", [])}
    print(f"  Existing fields: {sorted(existing)}")
    print()

    missing = []
    for field in REQUIRED_FIELDS:
        if field in existing:
            print(f"  ✅ {field}")
        else:
            print(f"  ❌ MISSING: {field}")
            missing.append(field)

    if missing:
        print(f"\n  ⚠  Add these fields manually in Airtable:")
        for f in missing:
            ftype = "Long text" if f in ("Email Body", "Pain Point") else "Single line text"
            print(f"     → '{f}' ({ftype})")
    else:
        print("\n  ✅ All fields present!")

def send_test_record():
    print("\n── Sending a test record ────────────────────────────")
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    record = {
        "fields": {
            "Name":         "TEST — Delete Me",
            "Title":        "Test Title",
            "Company":      "Test Company",
            "Industry":     "Healthcare",
            "Pain Point":   "This is a test record",
            "LinkedIn URL": "https://linkedin.com",
            "Subject Line": "Test Subject Line",
            "Email Body":   "This is a test email body. Delete this record.",
            "Status":       "Test",
            "Generated At": "2026-01-01T00:00:00Z"
        }
    }

    res = requests.post(AIRTABLE_URL, headers=headers, json=record, timeout=10)
    print(f"  Status: {res.status_code}")

    if res.status_code == 200:
        rec_id = res.json().get("id", "")
        print(f"  ✅ Test record created! ID: {rec_id}")
        print(f"  ✅ Go check your Airtable table — you should see 'TEST — Delete Me'")
        print(f"  Delete it manually after confirming.")
    else:
        print(f"  ❌ Failed: {res.text[:400]}")
        if "UNKNOWN_FIELD_NAME" in res.text:
            print("\n  ⚠  One or more field names don't match exactly.")
            print("     Field names are case-sensitive in Airtable.")
            print("     Check your table and make sure field names match exactly:")
            for f in REQUIRED_FIELDS:
                print(f"     → '{f}'")

def main():
    print("=" * 55)
    print("  Airtable Connection Diagnostic")
    print("=" * 55)

    if not check_env():
        print("\n❌ Fix .env first, then re-run.\n")
        return

    if not check_connection():
        print("\n❌ Fix connection error first, then re-run.\n")
        return

    check_fields()
    
    answer = input("\n  Send a test record to verify write access? (y/n): ").strip().lower()
    if answer == "y":
        send_test_record()

    print("\n" + "=" * 55)
    print("  If all green: run python main.py")
    print("  If errors: fix them above first")
    print("=" * 55 + "\n")

if __name__ == "__main__":
    main()