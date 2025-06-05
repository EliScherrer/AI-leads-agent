# agents/people_finder_agent.py
import json

from autogen import Agent, config_list_from_json, ConversableAgent

SYSTEM_MESSAGE = """
Role:
- You take in two structured JSON objects from previous agents and use it to find people at each company in company_list that match the ICP.
- These should be the best leads / the people should be the ones that are most likely to be the person a sales rep for company_info would contact to sell product_info to.
- use the web search tool to find people
- find the top (at least 3 and at most 5) people at each company
- Along with each person, you should return a relevant_info field that details why the person matches the ICP and would be a good fit for company_info to sell product_info to.
- Also include a approach_reccomendation field that details how you would approach the person to sell product_info to them.
- Also include a relevance_score [0-100] for how well the person matches.
- The company the sales agent works for is in company_info. And should not be returned in the company_list.
- The next agent after you will take the output of this agent and verify and enrich the contact information, therefore you don't need to get all of the contact information for each person the priority is to find the best leads.
- The input JSON is in the following format:
{
    "company_info": {
      "name": "SupplyStream Technologies",
      "website": "https://www.supplystreamtech.com",
      "description": "SupplyStream Technologies provides AI-driven ERP solutions for mid-sized automotive manufacturers, streamlining operations from procurement to distribution.",
      "industry": "B2B SaaS",
      "location": "Detroit, MI",
      "employee_count": 45,
      "annual_revenue": "12M"
    },
    "product_info": {
      "name": "StreamERP",
      "description": "StreamERP is a cloud-based ERP solution designed for automotive suppliers. It includes modules for inventory optimization, supplier integration, predictive maintenance, and production scheduling.",
      "key_features": [
        "Automated inventory forecasting",
        "Supplier API integrations",
        "Predictive equipment maintenance",
        "Real-time production dashboards",
        "Compliance reporting for ISO/TS standards"
      ],
      "competitive_advantages": [
        "Tailored specifically for automotive supply chain",
        "Easy integration with legacy systems",
        "Rapid 6-week deployment model"
      ]
    },
    "ICP": {
      "target_titles": ["COO", "CFO", "VP of Operations", "VP of IT", "VP of Supply Chain", "VP of Manufacturing", "VP of Engineering", "VP of Quality", "VP of Sales", "VP of Marketing"],
      "company_industry": "Automotive manufacturing or parts supply",
      "employee_range": {
        "min": 20,
        "max": 200
      },
      "revenue_range_million_usd": {
        "min": 5,
        "max": 50
      },
      "target_regions": ["United States", "Canada"],
      "additional_notes": "Prioritize companies currently undergoing digital transformation or operating multiple production sites."
    }
}
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
        "relevance_score": 0.95,
        },
    ]
}


When you have complied all the data you can return ONLY a JSON object in this format. Attaching the list of people you find at each company to their corresponding company_info object. Make no assumptions, and only return the data you can verify, fill in empty strings for any data that you don't have.
this is an example of the JSON object you should return:
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
          "relevance_score": 0.95,
          "people_list": [
              "person_info": {
                  "name": "John Doe",
                  "title": "COO",
                  "email": "john.doe@supplystreamtech.com",
                  "phone": "123-456-7890",
                  "linkedin": "https://www.linkedin.com/in/john-doe-1234567890",
                  "relevant_info": "John Doe is the COO of SupplyStream Technologies and is responsible for the overall operations of the company.",
                  "relevance_score": 0.95,
                  "approach_reccomendation": "I would approach John Doe by saying 'Hello, I'm from SupplyStream Technologies and we provide AI-driven ERP solutions for mid-sized automotive manufacturers. We're looking for a COO like you who is interested in digital transformation and streamlining operations. Would you be interested in a demo?'",
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
class PeopleFinderAgent(ConversableAgent):
    """
    Specialist agent for gather a list of people at a list of companies that match the ICP for company_info to sell product_info to.

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
            name="PeopleFinderAgent",
            llm_config={"config_list": config_list},
            system_message=SYSTEM_MESSAGE,
            human_input_mode="NEVER"  # Don't ask for human input since we're in API mode
        )

    async def process_message(self, sender: Agent, intakeInfoString: str, companyListString: str) -> str:
        """Process the intakeInfoString and companyListString and return the people list"""

        if not intakeInfoString:
            return "no intakeInfoString available"
        if not companyListString:
            return "no companyListString available"

        # Create a message in the format expected by the agent
        user_message = {
            "role": "user",
            "content": intakeInfoString + "\n" + companyListString
        }

        print("-------------message-------------------")
        print(user_message)
        
        # Send the message to the agent
        self.receive(user_message, sender)

        # Get the agent's reply
        reply = self.generate_reply([user_message], sender=sender)

        print("-------------reply-------------------")
        print(reply)

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