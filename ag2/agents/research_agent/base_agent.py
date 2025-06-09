# agents/research_agent/base_agent.py
from typing import Any, Optional, Union

from dotenv import load_dotenv
from autogen import ConversableAgent, config_list_from_json
from autogen.llm_config import LLMConfig

from agents.research_agent.tools_common import (
    list_agents_and_keys,
    get_agent_variable,
    update_agent_variable,
    find_entry,
)

load_dotenv()

class BaseAgent(ConversableAgent):
    """
    Common foundation for all agents.
    • Injects core tools.
    • Logs every user / assistant turn into
        orchard › <agent_name> › chat_details › chat_history
      (skips the driver-prompt that boots the conversation).
    """

    # TOOL_USE_PROMPT = """
    # Your agent name is {agent_name}.

    # General Tool use instructions for context variables management:
    # - Prioritize using your own data store using your agent name as the key for agent_name {agent_name}.
    # - All information you need should be given as input from previous agents.
    
    
    # """.strip()

    TOOL_USE_PROMPT = """
    Your agent name is {agent_name}.

    General Tool use instructions for context variables management:
    - Immediately call list_agents_and_keys() to get your schema and other available agent's data store to know where to get certain information and where to update certain information.
    
    ***DO NOT continue the conversation until you have the schema from the above step.***
        
    - When you need to get specific information within an agent's data store, use 'get_agent_variable' tool with YOUR agent name only {agent_name}.
    - Priotirize using your own data store using your agent name as the key for agent_name {agent_name}.
    - When you need to update specific information within an agent's data store, use 'update_agent_variable' tool.
    
    
    """.strip()

    ADDITIONAL_INSTRUCTIONS_PROMPT = """
    *** Additional Instructions (Prioritize these over the above instructions at all times) ***:
    {additional_instructions}
    """

    # ───────────────────────────────────────── ctor ─────────────────────────────────────────
    def __init__(
        self,
        name: str = "base_agent",
        llm_config: Optional[Union[LLMConfig, dict[str, Any]]] = None,
        system_message: Optional[str] = None,
        additional_instructions: Optional[str] = "",
        additional_functions: Optional[list] = None,
        excluded_functions: Optional[list] = None,
        log_chat: bool = True,
        chat_technical_name: str = "chat_details",
        **kwargs: Any,
    ):
        self._history_started = False  # first driver prompt is ignored
        self._chat_technical_name = chat_technical_name

        header = self.TOOL_USE_PROMPT.format(agent_name=name)

        custom = (system_message or "").strip()

        footer = self.ADDITIONAL_INSTRUCTIONS_PROMPT.format(additional_instructions=additional_instructions or "").strip()

        # stitch the three blocks together, skipping any empties
        system_message = "\n\n".join(part for part in (header, custom, footer) if part)

        # final_cfg = LLMConfig.get_current_llm_config(llm_config)
        config_list = config_list_from_json(env_or_file="OAI_CONFIG_LIST")

        builtin_funcs = [
            list_agents_and_keys,
            get_agent_variable,
            update_agent_variable,
        ]
        
        if excluded_functions:
            builtin_funcs = [f for f in builtin_funcs if f not in excluded_functions]
            
        all_funcs = builtin_funcs + (additional_functions or [])

        super().__init__(
            name=name,
            system_message=system_message,
            llm_config={"config_list": config_list},
            functions=all_funcs,
            **kwargs,
        )

        if log_chat:
            # tap every inbound message before normal routing
            self.register_reply(
                trigger=[ConversableAgent],
                reply_func=self._capture_inbound,
                position=0,
            )

    # ────────────────────────────── logging helpers (shared by all subclasses) ──────────────
    @staticmethod
    def _should_log(msg: dict) -> bool:
        """Only keep real user / assistant text (no tool scaffolding)."""
        if not msg:
            return False
        if msg.get("role") not in ("user", "assistant"):
            return False
        if not msg.get("content"):
            return False
        # ignore function / tool call wrappers
        if msg.get("tool_calls") or msg.get("function_call"):
            return False
        return True

    def _append_to_chat_history(self, msg: dict):
        """Persist a turn to orchard › <agent_name> › chat_details › chat_history."""
        try:
            _, _, chat_entry = find_entry(
                self.context_variables,
                agent_name=self.name,
                technical_name=self._chat_technical_name,
            )
            chat_entry.data.setdefault("chat_history", []).append(msg)
        except KeyError:
            # store not initialised yet → silently ignore
            pass

    # ───────────────────────────────────── inbound tap ──────────────────────────────────────
    def _capture_inbound(
        self,
        recipient,
        messages=None,
        sender=None,
        config=None,
    ):
        if not messages:
            return False, None

        latest = messages[-1]

        # skip the very first driver line once
        if not self._history_started:
            self._history_started = True
            return False, None

        if self._should_log(latest):
            self._append_to_chat_history(latest)

        return False, None  # let normal flow continue

    # ───────────────────────────────────── outbound hook ─────────────────────────────────────
    def generate_reply(  # type: ignore[override]
        self,
        messages=None,
        sender=None,
        **kwargs,
    ):
        reply = super().generate_reply(messages=messages, sender=sender, **kwargs)

        if reply:
            msg_dict = (
                {"role": "assistant", "name": self.name, "content": reply}
                if isinstance(reply, str)
                else reply
            )
            if self._should_log(msg_dict):
                self._append_to_chat_history(msg_dict)

        return reply
