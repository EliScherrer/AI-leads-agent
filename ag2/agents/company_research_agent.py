# agents/company_research_agent.py
import os
import json

from dotenv import load_dotenv
from autogen import Agent, config_list_from_json, ConversableAgent
from agents.prompts import PERPLEXITY_COMPANY_RESEARCH_SYSTEM_MESSAGE, COMPANY_LIST_FORMATTER_SYSTEM_MESSAGE

from agents.perplexity_agent import PerplexityAgent

load_dotenv()

COMPANY_RESEARCH_SYSTEM_MESSAGE = """
Role:
You are a helpful AI assistant. Your job is to take structured JSON input describing a company (company_info), their product (product_info), and their ideal customer profile (ICP), and craft a clear, specific user prompt to pass to the PerplexitySearchTool. The goal is to search for companies that closely match the ICP for a sales agent at company_info to sell product_info to.

Rules:
- Only output the user prompt to be sent to the PerplexitySearchTool. Do not include any explanations, intermediate steps, or markdown formatting.
- The prompt should be concise, search-friendly, and focused on finding companies that match the ICP.
- Do not include the company described in company_info in the search results.
- Avoid few-shot examples or multi-part instructions. Focus on a single, well-scoped search query.
- Use relevant context from company_info, product_info, and ICP to make the search as specific as possible.
- If any field is missing, only use the available information to make the best possible search prompt.


Output:
A single, well-formed user prompt string suitable for web search, e.g.:

Find companies in the United States or Canada in the automotive manufacturing or parts supply industry, with 20-200 employees and $5M-$50M annual revenue, that are undergoing digital transformation or operate multiple production sites. Exclude SupplyStream Technologies. The ideal companies should be a good fit for selling StreamERP, a cloud-based ERP solution for automotive suppliers.

The input JSON is in the following format:
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

        self.perplexity_agent = PerplexityAgent()
        
        self.formatter_agent = ConversableAgent(
            name="FormatterAgent",
            llm_config={"config_list": config_list},
            system_message=COMPANY_LIST_FORMATTER_SYSTEM_MESSAGE,
            human_input_mode="NEVER"  # Don't ask for human input since we're in API mode
        )

        # init agent
        super().__init__(
            name="CompanyResearchAgent",
            llm_config={"config_list": config_list},
            system_message=COMPANY_RESEARCH_SYSTEM_MESSAGE,
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
        
        # Get the prompt from the main agent
        self.receive(user_message, sender)
        reply = self.generate_reply([user_message], sender=sender)
        print("-------------CompanyResearchAgent reply-------------------")
        print(reply)

        # Search for companies using the PerplexityAgent
        searchResponse = self.perplexity_agent.search(PERPLEXITY_COMPANY_RESEARCH_SYSTEM_MESSAGE, reply)
        print("-------------perplexity_agent company response-------------------")
        print(searchResponse)

        # Format the response from the PerplexityAgent
        user_message = {
            "role": "user",
            "content": searchResponse
        }
        self.formatter_agent.receive(user_message, self)
        formattedResponse = self.formatter_agent.generate_reply([user_message], sender=sender)

        return formattedResponse
    