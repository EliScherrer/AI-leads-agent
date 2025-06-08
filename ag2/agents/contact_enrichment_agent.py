# agents/contact_enrichment_agent.py
import json

from autogen import Agent, config_list_from_json, ConversableAgent



        #   3. Use of Tools and Verification
        #   Encourage Use of Multiple Sources:
        #   Instruct the agent to cross-check LinkedIn, company websites, and reputable directories.
        #   Verification Step:
        #   Add a step to verify that the email/phone is not generic or outdated.
        #   Citation:
        #   Always cite the source for each piece of contact info.


#         # Edge cases / negative examples:
# - linkedin urls that are just their name like this for "george allen" "https://www.linkedin.com/in/george-allen" are usually not valid, double check the url to make sure it's a valid linkedin url.
# - linkedin urls that are just firstname.lastname@company.com like this for "george allen" "george.allen@supplystreamtech.com" are usually not valid, double check the email to make sure it's a valid email.


SYSTEM_MESSAGE = """
Role:
- You are a contact information enrichment specialist. Your job is to find and verify the most reliable direct contact information for every person in the people_list of each company in the company_list.


Context to know:
- You are receiving input from the people_finder_agent that has already found the best leads for the sales agent to contact.
- you are outputting the enriched contact information for each person and passing it onto a lead_scoring_agent to score the leads.
- You are encouraged to use Multiple, Recent, and Authoritative Sources to verify the contact information.


Rules:
- No markdown fences.
- Nothing outside of the JSON object.
- Never invent contact details. If you cannot find a reliable contact, return an empty string for that field.
- Use only verifiable sources (company websites, LinkedIn, reputable business directories).
- Do not include generic emails (info@, sales@, etc.) unless no other option exists.
- If you find multiple possible emails/phones/linkedins, return them in an array for that field.
- If you make an assumption, add it to the notes field and lower the relevance_score. Always append to the notes field, do not overwrite it.
- If possible, cross-check contact info across at least two independent sources
- Always cite the source for each contact method.


Steps:
1. Do the following for each person in the people list of each company:
2. Use the internet or other sources you have to verify the phone number - If it can not be verified use the internet or other sources to find the correct phone number
3. Use the internet to verify the email adrress - If it can not be verified use the internet or other sources to find the correct email address
4. use the internet to verify the linkedin URL - If it can not be verified use the internet or other sources to find the correct linkedin URL
5. update the contact information when applicable, 
6. record a source for every contact you found in source_url field, update to an array of urls if you used more than one source
7. append to the notes field to explain why you made changes and any assumptions you made.


Edge cases / negative examples:
- linkedin urls that are just their name like this for "george allen" "https://www.linkedin.com/in/george-allen" are usually not valid, double check the url to make sure it's a valid linkedin url.
- emails that are just firstname.lastname@company.com like this for "george allen" "george.allen@supplystreamtech.com" are usually not valid, double check the email to make sure it's a valid email.


Input and Output:
- The input JSON and the output JSON should be in the same format.
- this is an example of the JSON object you will receive and should return:
{
    "company_list": [
        "company_info": {
          "name": "SupplyStream Technologies",
          "website": "https://www.supplystreamtech.com",
          "description": "SupplyStream Technologies provides AI-driven ERP solutions for mid-sized automotive manufacturers, streamlining operations from procurement to distribution.",
          "industry": "B2B SaaS",
          "location": "Detroit, MI",
          "employee_count": 45,
          "annual_revenue": "12M"
          "relevant_info": "This company is a good fit for the ICP because they are a mid-sized automotive manufacturer that is undergoing digital transformation and operating multiple production sites.",
          "relevance_score": 56,
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
                  "notes": "I found this information on the company website. The phone number I'm not sure if it's still valid. the email might be John's or steve hammond's"
                  "source_url": "https://www.supplystreamtech.com/people/john-doe"
              }
          ]
        },
    ]
}


Rules:
- No markdown fences.
- Nothing outside of the JSON object.
""".strip()

# ---------------------------------------------------------------------------
# Agent definition
# ---------------------------------------------------------------------------
class ContactEnrichmentAgent(ConversableAgent):
    """
    Specialist agent for verifying and enriching the contact information for each person in the people list of each company.

    Parameters TODO
    ----------
    """

    def __init__(
        self,
    ):
        # Load config once at startup
        config_list = config_list_from_json(env_or_file="OAI_CONFIG_LIST")

        # init agent
        super().__init__(
            name="ContactEnrichmentAgent",
            llm_config={"config_list": config_list},
            system_message=SYSTEM_MESSAGE,
            human_input_mode="NEVER"  # Don't ask for human input since we're in API mode
        )

    async def process_message(self, sender: Agent,  companyListAndPeopleString: str) -> str:
        """Process the intakeInfoString and companyListString and return the people list"""

        if not companyListAndPeopleString:
            return "no companyListAndPeopleString available"

        # Create a message in the format expected by the agent
        user_message = {
            "role": "user",
            "content": companyListAndPeopleString
        }

        print("-------------message-------------------")
        print(user_message)
        
        # Send the message to the agent
        self.receive(user_message, sender)

        # Get the agent's reply
        reply = self.generate_reply([user_message], sender=sender)

        print("-------------reply-------------------")
        print(reply)

        # parse the AI response to JSON to confirm it is valid
        try:
            parsedReply = reply
            if parsedReply[0] != "{":
                start_index = parsedReply.find('{')
                if start_index != -1:  # If no '{' is found
                    parsedReply = parsedReply[start_index:]

            replyJson = json.loads(parsedReply)

            if "company_list" in replyJson:
                print("-------------company_list compiled successfully----------")
                print(replyJson)
                return parsedReply
        except Exception as e:
            print("-------------replyJson error-------------------")
            print(e)
            print(type(e))

        if reply is None:
            return "I apologize, but I couldn't generate a response."
        
        return reply