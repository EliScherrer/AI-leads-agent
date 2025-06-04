# agents/intake_agent/old_agent.py
from autogen import UserProxyAgent, config_list_from_json, ConversableAgent

# ---------------------------------------------------------------------------
# Agent definition
# ---------------------------------------------------------------------------
class IntakeAgent():
    """
    Specialist agent for gathering background information from the user.

    Parameters TODO
    ----------
    prompt_key : {"dtrp", "lead_sourcing"}
        Chooses the system prompt *and* which internal tools are exposed.
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


        # Initialize agent once and store as global
        self.agent = ConversableAgent(
            name="ConversableAgent",
            llm_config={"config_list": config_list},
            system_message="You are an AI agent that can search the web to create a list of high quality sales leads for a product. The user will provide you with a product that they want to find leads for. After they provide you with the product, you will ask them for the necessary background information to find the leads. After you have the background information, you will use the web search or deep research agent to find the leads. Return the list of leads in a JSON format.",
            human_input_mode="NEVER"  # Don't ask for human input since we're in API mode
        )

        self.userProxy = UserProxyAgent(name="userProxy", code_execution_config=False)

    async def process_message(self, message: str, user: str) -> str:
        """Process a single message and return the agent's response."""
        # Create a message in the format expected by the agent
        user_message = {
            "role": "user",
            "content": message
        }
        
        # Send the message to the agent
        self.agent.receive(user_message, self.userProxy)

        # Get the message history
        if user not in self.message_history:
            self.message_history[user] = []
        self.message_history[user].append(user_message)

        # Get the agent's reply
        reply = self.agent.generate_reply(messages=self.message_history[user], sender=self.userProxy)
        
        if reply is None:
            return "I apologize, but I couldn't generate a response."
        
        return reply