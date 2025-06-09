# qra_tools.py

import asyncio
from typing import Annotated, Any
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
import time

from autogen.agentchat.group import ReplyResult
from autogen.agents.experimental.websurfer import WebSurferAgent
from autogen.agentchat import initiate_group_chat
from autogen.agentchat.group.patterns import AutoPattern
from autogen import ConversableAgent, LLMConfig

from agents.research_agent.tools_common import find_entry
from agents.research_agent.google_utils import _rate_limit_guard, google_search

load_dotenv()

GS_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GSCX_ID = os.getenv("GOOGLE_SEARCH_CX")

def confirm_research(
    agent_name: str,
    context_variables: Any,
) -> ReplyResult:
    """
    Mark this agent’s research-profile as complete by setting
    data["research_completed"] = True.
    """
    # locate the research-profile entry for this agent
    orchard, _, research_entry = find_entry(
        context_variables,
        agent_name=agent_name,
        technical_name="research-profile",
    )

    research_entry.data["research_completed"] = True

    # re-insert orchard back into the context (AG2 requirement)
    context_variables["orchestration_context"] = orchard

    return ReplyResult(
        message=f"Research phase for '{agent_name}' marked COMPLETE.",
        context_variables=context_variables,
    )


def google_research(
    agent_name: str,
    technical_name: str,
    number_of_queries_per_search: Annotated[int, "Number of queries the agent should search for via Google Search."] = 10,
    research_goal: Annotated[str, "The research goal the user is trying to attempt."] = "",
    context_variables: Any = None,
) -> ReplyResult:
    orchard, _, research_entry = find_entry(
        context_variables, agent_name, technical_name
    )
    _, _, metrics_entry = find_entry(
        context_variables, agent_name, "google-search-metrics"
    )
    # Build Query Agent
    llm_cfg = LLMConfig(api_type="openai", model="gpt-4o")
    
    research_queries_critic_agent = ConversableAgent(
        name="research_queries_critic_agent",
        system_message=(
            f""""
            You are the Critic. If the search queries are not good, ask for improvement from the search_query_agent.
            
            Ensure there is no duplication in the search queries.
            
            If acceptable, finalize with confirm_search_queries.
            
            ONLY come up with {number_of_queries_per_search} search queries. If the writer comes up with more, ASK to reduce to {number_of_queries_per_search}.
            
            DO NOT call confirm_search_queries with MORE than the instructed number of queries.
            """
        ),
        llm_config=llm_cfg,
        human_input_mode="NEVER",
        is_termination_msg=lambda m: (m.get("content") or "").startswith(
            "ANSWER_CONFIRMED:"
        ),
    )

    search_query_agent = ConversableAgent(
        name="search_query_agent",
        system_message=(
        f"""
        You are tasked with taking the user's research goal and coming up with {number_of_queries_per_search} search queries to use in Google Search that will best help the user find the information they are looking for.             
        """
        ),
        llm_config=llm_cfg,
        human_input_mode="NEVER",
        is_termination_msg=lambda m: (m.get("content") or "").startswith(
            "ANSWER_CONFIRMED:"
        ),
    )

    @search_query_agent.register_for_execution()
    @research_queries_critic_agent.register_for_llm(
        description="Critic finalizes the search queries."
    )
    def confirm_search_queries(queries: list) -> str:
        ANSWER_CONFIRMED_PREFIX = "ANSWER_CONFIRMED:"

        orchard, _, research_entry = find_entry(
            context_variables,
            agent_name=agent_name,
            technical_name="research-profile",
        )

        # ensure key exists, then bulk-append
        research_entry.data.setdefault("search_queries", []).extend(queries)

        context_variables["orchestration_context"] = orchard
        return f"{ANSWER_CONFIRMED_PREFIX}\nSearch queries: {queries}"

    # Kick off the sub-chat
    convo_result = research_queries_critic_agent.initiate_chat(
        search_query_agent,
        message=f"User's research goal:\n{research_goal}\n\n Search Query Agent, please analyze.",
    )

    final_text = convo_result.summary
    if final_text.startswith("ANSWER_CONFIRMED:"):
        final_text = final_text.replace("ANSWER_CONFIRMED:", "", 1).strip()

    # Get the search queries from the orchard
    search_queries = research_entry.data.get("search_queries", [])
    
    # Search them with google one by one
    
    all_results: list[dict] = []             # keeps every result (may have dup URLs)
    seen_urls: set[str]  = set()             # used for fast deduplication

    print("-------------searching search_queries-------------------")
    print(search_queries)
    
    for q in search_queries:
        # 1a) respect your per-minute quota
        _rate_limit_guard(metrics_entry)

        # 1b) call Google CSE
        results = google_search(q, GS_KEY, GSCX_ID, 4)

        # 1c) filter out URLs we’ve already seen
        deduped = [r for r in results if r["url"] not in seen_urls]

        print("-------------search results-------------------")
        print(deduped)

        # 1d) update the URL set and the running list
        seen_urls.update(r["url"] for r in deduped)
        all_results.extend(deduped)

        # 1e) persist this query → results pair in the orchard
        research_entry.data.setdefault("researched_websites", []).append(
            {"query": q, "results": deduped}
        )

    context_variables["orchestration_context"] = orchard
    
    final_search_queries = research_entry.data.get("researched_websites", [])
    
    return ReplyResult(
        message=(
            f"Searched Google with the following results: {final_search_queries}.\n"
        ),
        context_variables=context_variables,
    )


# ---------------------------------------------------------------------------
# Crawl function for single URL
# ---------------------------------------------------------------------------
async def _crawl_one(url: str, context_vars: Any, target_agent_name: str) -> dict:
    """
    Crawl a single URL and store the final text in orchard under:
      [crawl4ai_scraping_agent].scraping-results.scraped_results_per_agent[target_agent_name][url]
    Also updates the "scraped_status_per_agent" structure if needed (e.g. not in this function).
    """
    ANSWER_CONFIRMED_PREFIX = "FINAL_ANSWER:"

    def confirm_summary(url_arg: str, content: str) -> str:
        """
        Called by the agent to finalize. We'll store the content in:
          orchard.agents.root[crawl4ai_scraping_agent name]
                 [entry with technical_name="scraping-results"]
                 .data["scraped_results_per_agent"][target_agent_name][url_arg]
        """
        qra_prefix = target_agent_name.split("_")[0]
        orchard, _, scraping_entry = find_entry(
            context_vars,
            agent_name=f"{qra_prefix}_crawl4ai_scraping_agent",
            technical_name="scraping-results",
        )

        # 1) Save the content in scraped_results_per_agent
        results_map = scraping_entry.data["scraped_results_per_agent"]
        agent_map = results_map.setdefault(target_agent_name, {})
        agent_map[url_arg] = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "page_content": content,
        }

        context_vars["orchestration_context"] = orchard
        # Return final answer to cause termination
        return f"{ANSWER_CONFIRMED_PREFIX} {url_arg}\nSummary: {content}"

    # 2) Build the surfer agent
    llm_cfg = LLMConfig(api_type="openai", model="gpt-4o-mini")
    surfer = WebSurferAgent(
        name="crawl4ai_surfer",
        llm_config=llm_cfg,
        web_tool="crawl4ai",
        human_input_mode="NEVER",
        system_message="""
          You are the 'crawl4ai_surfer' using 'crawl4ai'.
          Once done, call confirm_summary(url, content) to finalize.
        """.strip(),
        web_tool_kwargs={
            "llm_strategy_kwargs": {
                "chunk_token_threshold": 2000,
                "overlap_rate": 0.1,
                "apply_chunking": True,
                "extra_args": {"max_tokens": 1500},
                "verbose": True,
            }
        },
        functions=[confirm_summary],
        is_termination_msg=lambda m: m.get("content", "").startswith(
            ANSWER_CONFIRMED_PREFIX
        ),
    )

    pattern = AutoPattern(
        initial_agent=surfer,
        agents=[surfer],
        user_agent=None,
        group_manager_args={"llm_config": llm_cfg},
    )

    run_result, *_ = initiate_group_chat(
        pattern=pattern,
        messages=f"Please crawl the URL: {url}. Then call confirm_summary(...) to finalize.",
        max_rounds=8,
    )

    final_text = run_result.summary or run_result.last_message.get("content", "")
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "page_content": final_text,
    }


# ---------------------------------------------------------------------------
# scrape_urls(...) calls _crawl_one(...) for each URL
# and updates "scraped_status_per_agent"
# ---------------------------------------------------------------------------
def scrape_urls(
    target_qra_name_for_scraping: str,
    context_variables: Any,
) -> ReplyResult:
    """
    For the agent = target_qra_name_for_scraping:
      1. Grab its 'research-profile' to see the 'researched_websites'
      2. For each URL not already crawled, call _crawl_one(...)
      3. Store final content in orchard under:
         crawl4ai_scraping_agent name.scraping-results.scraped_results_per_agent[agent][url]
      4. Also keep stats in .scraped_status_per_agent[agent]:
         - scraping_complete
         - failed_urls
         - total_urls_scraped
    """
    batch_size = 20

    # 1) find orchard entry for "crawl4ai_scraping_agent name".scraping-results
    qra_prefix = target_qra_name_for_scraping.split("_")[0]
    orchard, _, scraping_entry = find_entry(
        context_variables,
        agent_name=f"{qra_prefix}_crawl4ai_scraping_agent",
        technical_name="scraping-results",
    )

    # 2) find orchard entry for "target_qra_name_for_scraping".research-profile
    _, _, research_entry = find_entry(
        context_variables,
        agent_name=target_qra_name_for_scraping,
        technical_name="research-profile",
    )

    # 3) Access or init the data structures
    results_map = scraping_entry.data["scraped_results_per_agent"]
    status_map = scraping_entry.data["scraped_status_per_agent"]

    # 3a) get the sub-maps for this particular agent
    agent_results = results_map.setdefault(target_qra_name_for_scraping, {})
    agent_status = status_map.setdefault(
        target_qra_name_for_scraping,
        {
            "scraping_complete": False,
            "failed_urls": {},
            "total_urls_scraped": 0,
        },
    )

    # 4) gather all URLs from that agent's research-profile
    all_urls = []
    for item in research_entry.data.get("researched_websites", []):
        for r in item.get("results", []):
            if "url" in r:
                all_urls.append(r["url"])

    # skip those we've already seen
    pending = [
        u
        for u in all_urls
        if u not in agent_results and u not in agent_status["failed_urls"]
    ]
    if not pending:
        return ReplyResult(
            message=f"No new URLs left to scrape for '{target_qra_name_for_scraping}'.",
            context_variables=context_variables,
        )

    successes = 0
    failures = 0

    # 5) call _crawl_one(...) in batches
    loop = asyncio.get_event_loop()
    for i in range(0, len(pending), batch_size):
        batch = pending[i : i + batch_size]
        results = loop.run_until_complete(
            asyncio.gather(
                *[
                    _crawl_one(url, context_variables, target_qra_name_for_scraping)
                    for url in batch
                ],
                return_exceptions=True,
            )
        )
        for url, outcome in zip(batch, results):
            if isinstance(outcome, Exception):
                agent_status["failed_urls"][url] = str(outcome)
                failures += 1
            else:
                successes += 1

    # 6) update status
    agent_status["scraping_complete"] = True
    agent_status["total_urls_scraped"] += successes

    # 7) re-save orchard
    context_variables["orchestration_context"] = orchard

    return ReplyResult(
        message=f"Scraping done for '{target_qra_name_for_scraping}'. "
        f"Success: {successes}, failures: {failures}.",
        context_variables=context_variables,
    )