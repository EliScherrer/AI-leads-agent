"""
Search Apollo, enrich **MAX_PROSPECTS** people, then store a *slim* record that
keeps only the business-relevant fields you care about.

ENV
----
  APOLLO_API_KEY

TWEAK
-----
  • Change MAX_PROSPECTS to control how many contacts you process per run.
  • Edit `wanted_top`, `wanted_employment`, … if you need more/less fields.
"""
import os, sys, time, json, requests

from pathlib import Path
from typing import Dict, List

# ─────────── CONFIG ─────────── #
MAX_PROSPECTS      = 1
DEFAULT_COMPANY    = "CrewAI"
DEFAULT_TITLE      = "Software Engineer"
OUTFILE_TEMPLATE   = "{company}_{title}_slim.json"
API_KEY = os.getenv("APOLLO_API_KEY")
BASE    = "https://api.apollo.io/api/v1"
HDRS    = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json",
    "Cache-Control": "no-cache",
}


# ───────────────────────── helpers ───────────────────────── #
def _post_json(endpoint: str, payload: Dict, retries: int = 3) -> Dict:
    url = f"{BASE}/{endpoint.lstrip('/')}"
    for backoff in (0, 2, 4)[:retries]:
        r = requests.post(url, json=payload, headers=HDRS, timeout=30)
        if r.ok:
            return r.json()
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(backoff or 1)
            continue
        r.raise_for_status()
    r.raise_for_status()


def _match(person_id: str) -> Dict:
    """Return a FULL Apollo payload (with emails unlocked)."""
    url = f"{BASE}/people/match"
    params = {"id": person_id, "reveal_personal_emails": "true"}
    r = requests.post(url, headers=HDRS, params=params, timeout=30)
    r.raise_for_status()
    return r.json()["person"]


# ───────────────────── field slim-down logic ───────────────────── #
wanted_top = {
    "id",
    "first_name",
    "last_name",
    "name",
    "headline",
    "email",
    "personal_emails",
    "linkedin_url",
    "twitter_url",
    "github_url",
    "facebook_url",
    "title",            # current title
    "city",
    "state",
    "country",
    "seniority",
    "departments",
    "subdepartments",
    "functions",
}

wanted_employment_fields = {
    "organization_name",
    "title",
    "start_date",
    "end_date",
    "current",
}

wanted_org_fields = {
    "name",
    "estimated_num_employees",
    "industry",
    "industry_tag_id",
}

def slim_person(p: Dict) -> Dict:
    slim: Dict = {k: p.get(k) for k in wanted_top}

    # ── employment history (slimmed records) ──
    emp_hist = p.get("employment_history", [])
    slim["employment_history"] = [
        {k: eh.get(k) for k in wanted_employment_fields} for eh in emp_hist
    ]

    # ── convenience: current company / role ──
    current = next((eh for eh in emp_hist if eh.get("current")), None)
    if current:
        slim["current_company"] = current.get("organization_name")
        slim["current_title"]   = current.get("title")
        slim["current_start"]   = current.get("start_date")

    # ── organization snapshot (headcount, industry) ──
    org = p.get("organization", {})
    slim["organization"] = {k: org.get(k) for k in wanted_org_fields}

    # ── education if present ──
    if "education" in p:
        slim["education"] = p["education"]

    # ── certifications if present ──
    if "certifications" in p:
        slim["certifications"] = p["certifications"]

    return slim


# ───────────────────────── main workflow ───────────────────────── #
def search_people(company: str, title: str, limit: int) -> List[Dict]:
    people, page = [], 1
    while len(people) < limit:
        payload = {
            "person_titles": [title],
            "include_similar_titles": True,
            "q_organization_name": company,
            "page": page,
            "per_page": 25,
        }
        data = _post_json("mixed_people/search", payload)
        people.extend(data.get("people", []))
        if page >= data.get("pagination", {}).get("total_pages", 1):
            break
        page += 1
        time.sleep(0.25)
    return people[:limit]


def enrich(company: str, title: str) -> List[Dict]:
    prospects = search_people(company, title, MAX_PROSPECTS)
    if not prospects:
        sys.exit("No matching people found.")

    print(f"Found {len(prospects)} prospect(s) – enriching…\n")

    slim_records = []
    for i, p in enumerate(prospects, 1):
        full = _match(p["id"])
        slim = slim_person(full)
        slim_records.append(slim)

        email = slim.get("email") or "—"
        tag   = "[OK]" if email != "—" else "[NO]"
        print(f"{tag} {i:>3}/{len(prospects)}  {slim['name']:<30} → {email}")
        time.sleep(0.3)

    return slim_records


# ──────────────────────────────── run ──────────────────────────────── #
if __name__ == "__main__":
    company = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_COMPANY
    title   = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_TITLE

    data = enrich(company, title)

    outfile = OUTFILE_TEMPLATE.format(company=company, title=title).replace(" ", "_")
    Path(outfile).write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"\nSlimmed data saved to {outfile}")
