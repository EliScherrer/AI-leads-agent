from autogen import config_list_from_json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from agents.intake_agent import IntakeAgent
from agents.company_research_agent import CompanyResearchAgent

import nest_asyncio

nest_asyncio.apply()
app = FastAPI()

# confige CORS
origins = [
    "http://localhost",
    "http://localhost:3000",
    "127.0.0.1.*"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load config once at startup
config_list = config_list_from_json(env_or_file="OAI_CONFIG_LIST")

# Initialize agent once and store as global
intakeAgent = IntakeAgent()
companyResearchAgent = CompanyResearchAgent()

@app.post("/chat")
async def chat(request: Request):
    """API Endpoint that handles individual messages while maintaining conversation history."""
    data = await request.json()
    user_query = data.get("message", "")
    user_agent = request.headers.get("user-agent")

    # Process the message and get response
    results = await intakeAgent.process_message(user_query, user_agent)
    print("-------------results-------------------")
    print(results)

    if results["complete"]:
        # TODO: call company research agent
        pass
    
    return results

@app.post("/new_session")
async def chat(request: Request):
    """API Endpoint that handles individual messages while maintaining conversation history."""
    data = await request.json()
    user_agent = request.headers.get("user-agent")

    should_start_new_session = data.get("new", "")

    results = { "response": "Error" }

    if (should_start_new_session == "true"):
        intakeAgent.message_history[user_agent] = []
        results = { "response": "session restarted" }
    else:
        results = { "response": "session not restarted" }

    print("-------------results-------------------")
    print(results)

    return results

@app.get("/companies")
async def chat(request: Request):
    """API Endpoint that handles individual messages while maintaining conversation history."""
    user_agent = request.headers.get("user-agent")

    # Process the message and get response
    results = await companyResearchAgent.process_message(intakeAgent.agent, intakeAgent.intake_data)
    print("-------------Company Research Agent results-------------------")
    print(results)

    return results
