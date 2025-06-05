# agents/intake_agent.py
import json

from autogen import UserProxyAgent, config_list_from_json, ConversableAgent

# TODO: ADD in logic to force the AI to confirm any assumptions before proceeding
SYSTEM_MESSAGE = """
Role:
- You are Steve, head of intaking information from users

Data you are trying to intake:
- Company information (website, description, industry, location, employee count, annual revenue)
- Product information (name, description, key features, competitive advantages)
- ICP information (target title, company industry, employee range, revenue range, target regions, additional notes)

Context:
- The user is trying to find leads for a product.
- The user will try to provide you with information about their company, the product they are selling, and information about their ideal customer profile.
- if the information provided is not enough, you can ask the user specifically for what information you need.
- if you have a gap in the information you need and the user doesn't have any more information to provide, you can come up with reasonable guesses for the missing information and verify with the user if that is correct.
- if the user tells you that they don't have any more information to provide, check for gaps in information, and then return the final JSON object with the information you have so far.

General profile of the user:
- a sales rep for a B2B SaaS company selling erp (management) software to the automotive industry
- using the app to find good leads and their contact info

When you have complied all the data you can return ONLY a JSON object in exactly this format, even if you have to make assumptions, using empty strings for any data that you didn't get from the user and can't figure out on your own:
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

Rules:
- No markdown fences.
- at most four sentences if you must ask a clarifying question.
- JSON only for the final response.
""".strip()

# ---------------------------------------------------------------------------
# Agent definition
# ---------------------------------------------------------------------------
class IntakeAgent(ConversableAgent):
    """
    Specialist agent for gathering background information from the user.

    Parameters TODO
    ----------
    """

    def __init__(
        self,
    ):
        # Load config once at startup
        config_list = config_list_from_json(env_or_file="OAI_CONFIG_LIST")

        # Setup message history - key is a user id, value is a list of messages
        # all messages formatted as {
        #     "role": msg["role"],
        #     "content": msg["content"]
        # }
        self.message_history = {}

        # results of the intake agent
        self.intake_data = {}

        # init agent
        super().__init__(
            name="IntakeAgent",
            llm_config={"config_list": config_list},
            system_message=SYSTEM_MESSAGE,
            human_input_mode="NEVER"  # Don't ask for human input since we're in API mode
        )

        # init proxy for user
        self.userProxy = UserProxyAgent(name="userProxy", code_execution_config=False)

    async def process_message(self, message: str, userId: str):
        """Process a single message and return the agent's response."""
        # Create a message in the format expected by the agent
        user_message = {
            "role": "user",
            "content": message
        }
        
        # Send the message to the agent
        self.receive(user_message, self.userProxy)

        # Get the message history
        if userId not in self.message_history:
            self.message_history[userId] = []
        self.message_history[userId].append(user_message)

        # Get the agent's reply
        reply = self.generate_reply(messages=self.message_history[userId], sender=self.userProxy)
        print("-------------reply-------------------")
        print(reply)

        ai_message = {
            "role": "assistant",
            "content": reply
        }
        self.message_history[userId].append(ai_message)

        try:
            parsedReply = reply
            if parsedReply[0] != "{":
                start_index = parsedReply.find('{')
                if start_index != -1:  # If no '{' is found
                    parsedReply = parsedReply[start_index:]

            replyJson = json.loads(parsedReply)

            if "company_info" in replyJson and "product_info" in replyJson and "ICP" in replyJson:
                self.intake_data = parsedReply
                print("-------------intake data accuired successfully----------")
                print(replyJson)
                return { "response": "Intake data accuired successfully, please wait while I find leads for you", "complete": True }
        except Exception as e:
            print("-------------replyJson error-------------------")
            print(e)
            print(type(e))

        if reply is None:
            return { "response": "I apologize, but I couldn't generate a response.", "complete": False }
        
        return { "response": reply, "complete": False }