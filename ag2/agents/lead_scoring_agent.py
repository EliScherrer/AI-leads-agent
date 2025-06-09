# agents/lead_scoring_agent.py
import json

from autogen import Agent, config_list_from_json, ConversableAgent

SYSTEM_MESSAGE = """
Role:
- you are an agent that scores and ranks leads for a sales agent
- the company_info for the sales agent is provided in a structured JSON object
- the product_info the sales agent sells is provided in a structured JSON object
- the companies and people that have been found as potential leads are provided in a structured JSON object
- These should be the best leads / the people should be the ones that are most likely to be the person a sales rep for company_info would contact to sell product_info to.
- use the deep research agent to determine what would make the best lead for the sales agent based on all of the information provided
- using this criteria, score the leads on a normal distribution from 0-100 and replace the previous relevance_score field with the new score
- a relevance_score of 0 means the lead is not relevant to the sales agent and should be removed from the leads_list
- a relevance_score of 25 means the lead is not a good match for the sales agent but not completely irrelevant
- a relevance_score of 50 means the lead is a fair match for the sales agent and should be considered for contact
- a relevance_score of 75 means the lead is a good match for the sales agent and should be considered for contact
- a relevance_score above 90 means the lead is an amazing match for the sales agent and should definitely be contacted
- a relevance_score of 100 means the lead is a perfect match for the sales agent and should be the first person the sales agent contacts


Evaluation Criteria:
- Functional role match
- Seniority
- Department (e.g., ops, supply chain, logistics)
- Region
- Title/keywords similarity
- how well the company the lead works for matches the ICP


- refine the relevant_info with the new information gained from the research
- refine the approach_reccomendation field that details how you would approach the lead to sell product to them.
- The next agent after you will take the output of this agent and create a CSV file with the leads list.
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
                  "notes": "I found this information on the company website. The phone number I'm not sure if it's still valid. the email might be John's or steve hammond's",
                  "source_url": "https://www.supplystreamtech.com/people/john-doe"
              }
          ]
        },
    ]
}


When you have complied all the data you can return ONLY a JSON object in this format. Taking all of the people_list objects and combining them into a single leads_list object including the data you've compiled. If you are confident that all of the leads have been scored and ranked, set the complete field to true.
this is an example of the JSON object you should return:
{
    "complete": true,
    "leads_list": [
        "lead_info": {
            "name": "John Doe",
            "title": "COO",
            "email": "john.doe@supplystreamtech.com",
            "phone": "123-456-7890",
            "linkedin": "https://www.linkedin.com/in/john-doe-1234567890",
            "relevant_info": "John Doe is the COO of SupplyStream Technologies and is responsible for the overall operations of the company.",
            "relevance_score": 95,
            "approach_reccomendation": "I would approach John Doe by saying 'Hello, I'm from SupplyStream Technologies and we provide AI-driven ERP solutions for mid-sized automotive manufacturers. We're looking for a COO like you who is interested in digital transformation and streamlining operations. Would you be interested in a demo?'",
            "notes": "I found this information on the company website. The phone number I'm not sure if it's still valid. the email might be John's or steve hammond's",
            "source_url": "https://www.supplystreamtech.com/people/john-doe",
            "company_info": {
                "name": "SupplyStream Technologies",
                "website": "https://www.supplystreamtech.com",
                "description": "SupplyStream Technologies provides AI-driven ERP solutions for mid-sized automotive manufacturers, streamlining operations from procurement to distribution.",
                "industry": "B2B SaaS",
                "relevant_info": "This company is a good fit for the ICP because they are a mid-sized automotive manufacturer that is undergoing digital transformation and operating multiple production sites."
            }
        }
    ]
}


Rules:
- No markdown fences.
- Nothing outside of the JSON object.
""".strip()

# ---------------------------------------------------------------------------
# Agent definition
# ---------------------------------------------------------------------------
class LeadScoringAgent(ConversableAgent):
    """
    Specialist agent for scoring the leads in the people list of each company and combining them into a single list of leads.

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
            name="LeadScoringAgent",
            llm_config={"config_list": config_list},
            system_message=SYSTEM_MESSAGE,
            human_input_mode="NEVER"  # Don't ask for human input since we're in API mode
        )

    async def process_message(self, sender: Agent, intakeInfoString: str, companyListString: str) -> str:
        """Process the intakeInfoString and companyListString and return the people list"""

        # TODO - do the work of the agent here

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

        # parse the AI response to JSON to confirm it is valid
        try:
            parsedReply = reply
            if parsedReply[0] != "{":
                start_index = parsedReply.find('{')
                if start_index != -1:  # If no '{' is found
                    parsedReply = parsedReply[start_index:]

            replyJson = json.loads(parsedReply)

            if "leads_list" in replyJson:
                print("-------------leads_list compiled successfully----------")
                print(replyJson)
                return parsedReply
        except Exception as e:
            print("-------------replyJson error-------------------")
            print(e)
            print(type(e))

        if reply is None:
            return "I apologize, but I couldn't generate a response."
        
        return reply