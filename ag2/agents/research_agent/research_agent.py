# agents/research_agent/research_agent.py
from typing import Any, Optional, Union

from autogen.llm_config import LLMConfig
from agents.research_agent.base_agent import BaseAgent
from agents.research_agent.qra_tools import (
    confirm_research,
    google_research,
    scrape_urls,
)
from agents.research_agent.tools_common import update_agent_variable

# ───────────────────────── prompt templates ─────────────────────────
ROLE_PROMPT_SEARCH_TMPL = """
YOU MUST USE YOUR AGENT NAME ONLY WHEN CALLING TOOLS.

Task:
- Call **get_agent_variable** with **your own agent name** to see if `research_completed`
  is already true. If so, transfer immediately to the next agent.
- Perform research by calling **google_research exactly once**
  with `number_of_queries_per_search = {queries}`.
- After researching, call **confirm_research** *only if* `research_completed`
  is still false, then hand off to the next agent.
- Operate strictly within your own scope; never research on behalf of another agent.
""".strip()

ROLE_PROMPT_SCRAPE = """
YOU MUST USE YOUR AGENT NAME ONLY WHEN CALLING TOOLS.

Critical for KEYS in the data store:
- Ignore any `research` or `research-profile` keys.
- Never access `scraped_results_per_agent`; only read `scraped_status_per_agent`.

Critical for `technical_name`:
- Use `scraping-results` for your own data-store entries.

Task:
- Call **get_agent_variable** to verify whether `scraping_complete` is true for the
  required **target_qra_name_for_scraping** (must include `industry_`) *and*
  that scraping is finished for every listed research agent.
  · If true, transfer immediately to the next agent.
- Otherwise, run **scrape_urls** (pass the requesting agent) to harvest final
  page content into Orchard, then transfer.
- Operate strictly within your own scope; never scrape for another agent.
""".strip()

# ───────────────────────────── agent class ────────────────────────────
class ResearchAgent(BaseAgent):
    """
    Quick-turnaround research agent.

    Modes
    -----
    search_mode  → `google_research`  + `confirm_research`
                   (queries_per_search controls query count)
    scrape_mode  → `scrape_urls`

    Exactly one of `search_mode` or `scrape_mode` must be True.
    """

    def __init__(
        self,
        name: str = "research_agent",
        llm_config: Optional[Union[LLMConfig, dict[str, Any]]] = None,
        additional_instructions: str = "",
        *,
        search_mode: bool = True,
        scrape_mode: bool = False,
        queries_per_search: int = 24,
        additional_functions: Optional[list] = None,  # caller-supplied tools
        **kwargs: Any,
    ):
        # Ensure only one mode is active
        if search_mode == scrape_mode:
            raise ValueError("Exactly one of 'search_mode' or 'scrape_mode' must be True.")

        # Prompt + internal tool selection
        if search_mode:
            system_msg = ROLE_PROMPT_SEARCH_TMPL.format(queries=queries_per_search)
            internal_funcs = [google_research, confirm_research]
        else:  # scrape_mode
            system_msg = ROLE_PROMPT_SCRAPE
            internal_funcs = [scrape_urls]

        # Merge internal tools with any caller-supplied tools
        merged_funcs = internal_funcs + (additional_functions or [])

        # Remove duplicate key if it exists in **kwargs**
        kwargs.pop("additional_functions", None)

        super().__init__(
            name=name,
            llm_config=llm_config,
            system_message=system_msg,
            additional_instructions=additional_instructions,
            additional_functions=merged_funcs,
            excluded_functions=[update_agent_variable],
            **kwargs,
        )
