from autogen import config_list_from_json, ConversableAgent, LLMConfig
from autogen.agents.experimental import DeepResearchAgent
from fastapi import FastAPI, Request

import contextlib
import io
import nest_asyncio


nest_asyncio.apply()

app = FastAPI()

def run_agent(user_query):
    """Runs the agent synchronously and returns the final JSON result."""

    # Load config
    config_list = config_list_from_json(env_or_file="OAI_CONFIG_LIST")

    # Initialize DeepResearchAgent
    # agent = DeepResearchAgent(
    
    agent = ConversableAgent(
        name="ConversableAgent",
        llm_config={"config_list": config_list},
        system_message="You are an AI agent that can search the web to create a list of high quality sales leads for a product. The user will provide you with a product that they want to find leads for. After they provide you with the product, you will ask them for the necessary background information to find the leads. After you have the background information, you will use the web search or deep research agent to find the leads. Return the list of leads in a JSON format."
    )

    # Run the agent (synchronous call)
    final_result = agent.run(
        message=user_query,
        tools=agent.tools,
        max_turns=4,
        user_input=False,
        summary_method="reflection_with_llm",
    )

    final_result.process()

    return final_result


@app.post("/chat")
async def chat(request: Request):
    """API Endpoint that returns only the final result as JSON."""
    data = await request.json()
    user_query = data.get("message", "")

    # Capture stdout without modifying the function
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        final_result = run_agent(user_query)

    captured_output = buffer.getvalue()

    results = {
        "final_result_summary": final_result.summary,
        "final_result_cost": final_result.cost,
        "captured_output": captured_output,
    }
    return results
