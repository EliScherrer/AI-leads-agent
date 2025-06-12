# agents/people_research_agent.py
import json
from autogen import Agent, config_list_from_json, ConversableAgent
from agents.apollo_client import ApolloClient
from agents.perplexity_client import PerplexityClient
from agents.prompts import PERPLEXITY_PEOPLE_FINDER_SYSTEM_MESSAGE, PERPLEXITY_PEOPLE_ENRICHMENT_SYSTEM_MESSAGE
from dotenv import load_dotenv


load_dotenv()

SYSTEM_MESSAGE = """
You are a helpful AI assistant. Your task is to take structured JSON input containing companies and people. Your job is to combine them into a single JSON object.

Rules:
- Only output the final answer as a JSON object. Do not include any explanations, intermediate steps, or markdown formatting.
- Do not include anything outside the JSON object.
- Do not modify any of the data in the input JSON objects, except to remove any people without a name value or if the name value == title value remove them as well.

- You can merge people objects together if they are the same person (same name and at the same company), there should be no duplicates (two people at the same company with the same name and title). Prefer to keep data over empty strings.


Return a JSON object in the following format:
output example =
{
    "company_list": [
        "company_info": {
          "name": "SupplyStream Technologies",
          "website": "https://www.supplystreamtech.com",
          "description": "SupplyStream Technologies provides AI-driven ERP solutions for mid-sized automotive manufacturers, streamlining operations from procurement to distribution.",
          "industry": "B2B SaaS",
          "location": "Detroit, MI",
          "employee_count": 45,
          "annual_revenue": "12M",
          "relevant_info": "This company is a good fit for the ICP because they are a mid-sized automotive manufacturer that is undergoing digital transformation and operating multiple production sites.",
          "relevance_score": 83,
          "people_list": [
              "person_info": {
                  "name": "John Doe",
                  "title": "COO",
                  "email": "john.doe@supplystreamtech.com",
                  "phone": "123-456-7890",
                  "linkedin": "https://www.linkedin.com/in/john-doe-1234567890",
                  "relevant_info": "John Doe is the COO of SupplyStream Technologies and is responsible for the overall operations of the company.",
                  "relevance_score": 95,
                  "approach_reccomendation": "I would approach John Doe by saying 'Hello, I'm from SupplyStream Technologies and we provide AI-driven ERP solutions for mid-sized automotive manufacturers. We're looking for a COO like you who is interested in digital transformation and streamlining operations. Would you be interested in a demo?'",
                  "notes": "I found this information on the company website. The phone number I'm not sure if it's still valid. the email might be John's or steve hammond's",
                  "source_urls": ["https://www.supplystreamtech.com/people/john-doe"]
              }
          ]
        }
    ]
}
""".strip()

# ---------------------------------------------------------------------------
# Agent definition
# ---------------------------------------------------------------------------
class PeopleResearchAgent(ConversableAgent):
    """
    Specialist agent for gathering a list of people at a list of companies that match the ICP for company_info to sell product_info to.

    Parameters TODO
    ----------
    """

    def __init__(
        self,
    ):
        # Load config once at startup
        config_list = config_list_from_json(env_or_file="OAI_CONFIG_LIST")

        # init PerplexityClient
        self.perplexity_client = PerplexityClient()
        self.apollo_client = ApolloClient()

        # init self agent that will act as the formatting agent
        super().__init__(
            name="PeopleResearchAgent",
            llm_config={"config_list": config_list},
            system_message=SYSTEM_MESSAGE,
            human_input_mode="NEVER"  # Don't ask for human input since we're in API mode
        )

    async def process_message(self, sender: Agent, intakeInfoString: str, companyListString: str) -> str:
        """For each company in company_list, search for people matching the ICP and return the results as a JSON object."""
        
        # validate input
        if not intakeInfoString:
            return "no intakeInfoString available"
        if not companyListString:
            return "no companyListString available"

        try:
            intake_info = json.loads(intakeInfoString)
            company_list_obj = json.loads(companyListString)
        except Exception as e:
            return f"Input JSON parsing error: {e}"

        # 1. search for people
        # findPeopleOutput = self.search_for_people(company_list_obj, intake_info)

        # 2. format the found people results
        # companyListWithPeopleResults = self.format_people_results(sender, json.dumps(findPeopleOutput))
        companyListWithPeopleResults = companyListString # TODO: REPLACE WHEN DONE TESTING
        print("-------------------------------- companyListWithPeopleResults --------------------------------")
        print(companyListWithPeopleResults)

        # 3. enrich the contact info
        # enrichedContactInfoOutput = self.enrich_contact_info_perplexity(companyListWithPeopleResults)
        enrichedContactInfoOutput = self.enrich_contact_info_apollo(companyListWithPeopleResults)
        print("-------------------------------- enrichedContactInfoOutput --------------------------------")
        print(enrichedContactInfoOutput)

        # 4.format the enriched people results
        companyListWithEnrichedPeopleResults = self.format_people_results(sender, json.dumps(enrichedContactInfoOutput))
        # TODO: do we need another formatter? companyListWithEnrichedPeopleResults = self.format_enriched_people_results(sender, json.dumps(enrichedContactInfoOutput))
        print("-------------------------------- companyListWithEnrichedPeopleResults --------------------------------")
        print(companyListWithEnrichedPeopleResults)

        # return companyListWithPeopleResults
        return companyListWithEnrichedPeopleResults
    
    def search_for_people(self, company_list_obj, intake_info):
        # loop over the companies and get people
        company_list = company_list_obj.get("company_list", [])
        output = {"company_list": []}

        for company in company_list:
            company_info = company.get("company_info", company) if isinstance(company, dict) else company
            prompt = self.build_people_search_prompt(intake_info, company_info)
            print("-------------------------------- People Finder Prompt--------------------------------")
            print(f"Prompt: {prompt}")

            try:
                # Use PerplexityClient to search for people at this company
                people_results = self.perplexity_client.search(PERPLEXITY_PEOPLE_FINDER_SYSTEM_MESSAGE, prompt)
                print(f"People results: {people_results}")
            except Exception as e:
                print(f"Error searching for people at {company_info.get('name', '')}: {e}")
                people_results = ""
            output["company_list"].append({
                "company_info": company_info,
                "people_list": people_results
            })

        return output

    def enrich_contact_info_apollo(self, companyListWithPeople):
        try:
            companyListWithPeople_obj = json.loads(companyListWithPeople)
        except Exception as e:
            print(f"Error parsing formatted company/people results: {e}")
            return companyListWithPeople  # fallback to un-enriched results

        company_list = companyListWithPeople_obj.get("company_list", [])
        output = {"company_list": []}

        # TODO: remove this to stop limiting the number of companies and people to reduce apollo usage
        for company in company_list:
            company_info = company["company_info"]
            people_list = company_info.get("people_list", [])
            enriched_people_list = []
            for person in people_list:
                person = person.get("person_info", person)
                if not person.get("name"):
                    print(f"No name found for person {person} ??")
                    continue
                
                print("-------------------------------- checking person --------------------------------")
                print(person.get("name"))

                companyName = company_info.get("name", "")
                enriched_person = self.apollo_client.enrich_contact_info(companyName, person)
                enriched_people_list.append(enriched_person)

            # update the company with the new people_list, and append to the new company_list
            company_info["people_list"] = enriched_people_list
            company["company_info"] = company_info
            output["company_list"].append(company)
        
        return output

    def enrich_contact_info_perplexity(self, companyListWithPeople):
        try:
            companyListWithPeople_obj = json.loads(companyListWithPeople)
        except Exception as e:
            print(f"Error parsing formatted company/people results: {e}")
            return companyListWithPeople  # fallback to un-enriched results

        company_list = companyListWithPeople_obj.get("company_list", [])
        output = {"company_list": []}

        for company in company_list:
            company_info = company["company_info"]
            people_list = company_info.get("people_list", [])
            enriched_people_list = []
            for person in people_list:
                if not person.get("name"):
                    print(f"No name found for person {person} ??")
                    continue

                enrichment_prompt = self.build_contact_enrichment_prompt(company_info, person)
                print("-------------------------------- Contact Enrichment Prompt--------------------------------")
                print(f"Prompt: {enrichment_prompt}")

                try:
                    enrichment_result = self.perplexity_client.search(PERPLEXITY_PEOPLE_ENRICHMENT_SYSTEM_MESSAGE, enrichment_prompt)
                    print(f"Enrichment result: {enrichment_result}")
                except Exception as e:
                    print(f"Error enriching contact info for {person.get('name', '')}: {e}")
                
                # create an object with the old person info and the new contact info and append to new people_list
                enriched_people_list.append({
                    "person_info": person,
                    "contact_info": enrichment_result
                })

            # update the company with the new people_list
            company_info["people_list"] = enriched_people_list
            company["company_info"] = company_info
            output["company_list"].append(company)
        
        return output


    def format_people_results(self, sender, rawCompanyInfoAndPeopleResults):
        # Create a message in the format expected by the formatter agent
        user_message = {
            "role": "user",
            "content": rawCompanyInfoAndPeopleResults
        }

        # Send the message to the formatter agent
        self.receive(user_message, sender)
        reply = self.generate_reply([user_message], sender=sender)

        return reply

    def build_people_search_prompt(self, intake_info, company_info):
        icp = intake_info.get("ICP", {})
        product = intake_info.get("product_info", {})
        company_name = company_info.get("name", "")
        industry = company_info.get("industry", "")
        target_titles = ", ".join(icp.get("target_titles", []))
        product_name = product.get("name", "")
        product_desc = product.get("description", "")
        
        # f"Find current executives or decision makers at {company_name} ({industry}) "
        # f"Find current employees at {company_name} ({industry}) "
        # f"with titles such as {target_titles} who would be good leads for selling {product_name}, {product_desc}. "
        # f"Provide for each person: name, title, email, phone, LinkedIn, and a source URL for each field. "
        prompt = (
            f"Find current employees at {company_name} ({industry}) with job titles such as {target_titles} who are likely decision makers or good leads for selling {product_name}, {product_desc}. "
            f"For each person, provide their name and job title. If available, also include their email, phone, and LinkedIn profile as a bonus. Always include a source URL for each field you provide. "
            f"Prioritize accuracy and recency. If a field is not available, leave it blank."
        )
        return prompt

    def build_contact_enrichment_prompt(self, company_info, person_info):
        company_name = company_info.get("name", "")
        person_name = person_info.get("name", "")
        person_title = person_info.get("title", "")
        prompt = (
            f"Find the most accurate and up-to-date contact information for {person_name}, {person_title} at {company_name}. "
            f"Return their email, phone number, LinkedIn profile, and any other relevant contact details. "
            f"Provide source URLs for each field. If a field is not available, leave it as an empty string."
        )
        return prompt