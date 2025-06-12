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
import os, json, requests
from typing import Dict, List, Any


# ─────────── CONFIG ─────────── #
API_KEY = os.getenv("APOLLO_API_KEY")
BASE    = "https://api.apollo.io/api/v1"
PEOPLE_SEARCH_ENDPOINT = "/mixed_people/search"
PEOPLE_MATCH_ENDPOINT = "/people/match"

class ApolloClient():
    """
    Specialist agent for interacting with the Apollo API and enriching contact info.
    """

    def request_people_enrichment(self, name: str, title: str, company: str) -> Dict:
        """Request Apollo to get a person's data https://docs.apollo.io/reference/people-enrichment"""
        url = f"{BASE}{PEOPLE_MATCH_ENDPOINT}"

        headers = {
            "x-api-key": API_KEY,
            "accept": "application/json",
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
        }

        params = {
            "name": name, 
            "organization_name": company,
            "reveal_personal_emails": "true",
            "reveal_personal_number": "false"
            # TODO: add webhook_url, you need this for the phone number, apollo will send it in JSON there
        }
        response = requests.post(url, headers=headers, params=params, timeout=30)

        try:
            response.raise_for_status()
        except requests.exceptions.Timeout as e:
            print(f"Apollo API => Request timed out: {response.text}. Status code: {response.status_code}")
        except requests.exceptions.HTTPError as e:
            print(f"Apollo API => HTTP error occurred: {response.text}. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Apollo API => Error during request: {response.text}. Status code: {response.status_code}")
        
        try:
            response_json = response.json()
        except json.JSONDecodeError as e:
            print(f"Apollo API => Invalid JSON response received. Error: {e}")
            return {}

        return response_json


    # ───────────────────────── main entrypoint ───────────────────────── #
    def enrich_contact_info(self, company: str, person: Any) -> List[Dict]:
        print("-------------------------------- enriching contact for ... --------------------------------")
        print(company)
        print(person)
        enrichedPerson = person.copy()

        apolloPerson = self.request_people_enrichment(person["name"], person["title"], company).get("person")
        print("-------------------------------- apolloPerson --------------------------------")
        print(apolloPerson)
        if apolloPerson:
            enrichedPerson["email"] = apolloPerson.get("contact", {}).get("email")
            enrichedPerson["twitter_url"] = apolloPerson.get("twitter_url")
            enrichedPerson["github_url"] = apolloPerson.get("github_url")
            enrichedPerson["facebook_url"] = apolloPerson.get("facebook_url")
            enrichedPerson["linkedin"] = apolloPerson.get("linkedin_url")
            enrichedPerson["phone"] = apolloPerson.get("phone_numbers") # TODO: this is a list of phone numbers? Doc says they should be sent to the webhook?
            enrichedPerson["is_likely_to_engage"] = apolloPerson.get("is_likely_to_engage")
            enrichedPerson["email_status"] = apolloPerson.get("email_status")

        print("-------------------------------- enrichedPerson --------------------------------")
        print(apolloPerson)

        return enrichedPerson

