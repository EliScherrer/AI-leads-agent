# agents/company_research_agent.py
import json

from autogen import Agent, config_list_from_json, ConversableAgent

SYSTEM_MESSAGE_OLD = """
Role:
- You take in structured JSON from a previous agent and use it to find companies that match the ICP for a sales agent at company_info to sell product_info to.
- Use the web search agent tool to find companies that match the ICP. 
-Find the top (at least 3 and at most 5) most relevant companies.
- Along with each company, you should return a relevant_info field that details why the company matches the ICP and would be a good fit for company_info to sell product_info to 
- Also include a relevance_score [0-100] for how well the company matches.
- The company the sales agent works for is in company_info. And should not be returned in the company_list.
- The next agent will use the output of this agent to find contacts at the companies that match the ICP.
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

IMPORTANT OPERATING INSTRUCTIONS: 
- Leverage the company_google_research_agent to find companies that match the ICP.
- the company_google_research_agent should be able to find more relevant up to date companies that match the ICP than you can.
- pass the same input JSON you received as input to the company_google_research_agent
- Process the output of the company_google_research_agent and return the most relevant companies that match the ICP.


When you have complied all the data you can return ONLY a JSON object in this format, you can add more fields if you have more information that you think is relevant. Make no assumptions, and only return the data you have, fill in empty strings for any data that you don't have.
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
        "annual_revenue": "12M",
        "relevant_info": "This company is a good fit for the ICP because they are a mid-sized automotive manufacturer that is undergoing digital transformation and operating multiple production sites.",
        "relevance_score": 95
        }
    ]
}

Rules:
- No markdown fences.
- Nothing outside of the JSON object.
""".strip()

SYSTEM_MESSAGE = """
Role:
- You take in structured JSON from a previous agent and use it to find companies that match the ICP for a sales agent at company_info to sell product_info to.
- work with the company_google_research_agent to find companies that match the ICP and process the results from company_google_research_agent
- the company_google_research_agent should be able to find more relevant up to date companies that match the ICP than you can.
- pass the same input JSON you received as input to the company_google_research_agent
- Process the output of the company_google_research_agent and return the most relevant companies that match the ICP.

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



When you have complied all the data you can return ONLY a JSON object in this format, you can add more fields if you have more information that you think is relevant. Make no assumptions, and only return the data you have, fill in empty strings for any data that you don't have.
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
        "annual_revenue": "12M",
        "relevant_info": "This company is a good fit for the ICP because they are a mid-sized automotive manufacturer that is undergoing digital transformation and operating multiple production sites.",
        "relevance_score": 95
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
class CompanyResearchAgent(ConversableAgent):
    """
    Specialist agent for gathering company information given background information from the user.

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
            name="CompanyResearchAgent",
            llm_config={"config_list": config_list},
            system_message=SYSTEM_MESSAGE,
            human_input_mode="NEVER"  # Don't ask for human input since we're in API mode
        )

    async def process_message(self, sender: Agent, message: str) -> str:
        """Process a single message and return the agent's response."""

        if not message:
            return "no input available"

        # Create a message in the format expected by the agent
        user_message = {
            "role": "user",
            "content": message
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