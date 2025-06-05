# agents/lead_scoring_agent.py
import json

from autogen import Agent, config_list_from_json, ConversableAgent

SYSTEM_MESSAGE = """
TODO - score all the people in the people list of each company and combining them into a single list of leads.
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