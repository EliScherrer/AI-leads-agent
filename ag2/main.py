import asyncio
from typing import Any
from autogen import config_list_from_json, UserProxyAgent
from autogen.agentchat import initiate_group_chat
from autogen.agentchat.group.patterns import AutoPattern
from agents.intake_agent import IntakeAgent
from agents.company_research_agent import CompanyResearchAgent
from agents.people_finder_agent import PeopleFinderAgent
from agents.contact_enrichment_agent import ContactEnrichmentAgent
from agents.lead_scoring_agent import LeadScoringAgent
from agents.tsv_output_agent import TSVOutputAgent
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

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

# dictionary to store the final results, key is userId, value is the leads list
final_results = {}

# Initialize agent once and store as global
intakeAgent = IntakeAgent()
companyResearchAgent = CompanyResearchAgent()
peopleFinderAgent = PeopleFinderAgent()
contactEnrichmentAgent = ContactEnrichmentAgent()
leadScoringAgent = LeadScoringAgent()
tsvOutputAgent = TSVOutputAgent()

company_research_agent = QuickResearchAgent(
        search_mode=True,
        scrape_mode=False,
        queries_per_search=3,
        name="company_research_agent",
        llm_config=cfg,
        additional_instructions="""
    Research Goal:
    - Look at the intake_agent discovery_notes to get the company name and website url.
    - The research goal should be to find out what the company does.
    - Make sure one of the queries is ONLY the company url so we can get the home page of the official website.
    - So if the domain is xyz.com, the one of the queries should be "xyz.com" ONLY to get the home page. Nothing else in that query.
    
    Critical Instructions:
    - Ensure all 4 points above are put into the research goal with the REAL company name and website url from the discovery_notes. 
    - Don't actually use xyz.com, this is just an example, get the real data from the discovery_notes and create the research goal using real data.***
    - All other queries MUST include the url in the query, dont do site:websiteurl, just use the website url in the query.
    """,
        additional_functions=[],
    )

@app.post("/chat")
async def chat(request: Request):
    """API Endpoint that handles intake data and responds to user queries"""
    data = await request.json()
    user_query = data.get("message", "")
    user_agent = request.headers.get("user-agent")

    # Process the message and get response
    results = await intakeAgent.process_message(user_query, user_agent)
    print("-------------results-------------------")
    print(results)

    if results["complete"]:
        # asyncio.create_task(processIntakeData(user_agent))
        asyncio.create_task(runOrchestrator(user_agent))
        
    
    return results

@app.post("/new_session")
async def newSession(request: Request):
    """API Endpoint that clears the conversation history and starts a new session"""
    data = await request.json()
    user_agent = request.headers.get("user-agent")

    should_start_new_session = data.get("new", "")

    results = { "response": "Error" }

    if (should_start_new_session == "true"):
        intakeAgent.message_history[user_agent] = []
        if user_agent in final_results:
            del final_results[user_agent]
        results = { "response": "session restarted" }
    else:
        results = { "response": "session not restarted" }

    print("-------------results-------------------")
    print(results)

    return results

async def processIntakeData(userId: str):
    print("-------------started lead generation-------------------")
    intakeInfoString = intakeAgent.intake_data
    # get company list
    companyListString = await companyResearchAgent.process_message(intakeAgent, intakeInfoString)
    # get people list
    companyListAndPeopleString = await peopleFinderAgent.process_message(companyResearchAgent, intakeInfoString, companyListString)
    # enrich people list
    companyListAndPeopleStringEnriched = await contactEnrichmentAgent.process_message(peopleFinderAgent, companyListAndPeopleString)
    # score leads
    leadsListString = await leadScoringAgent.process_message(contactEnrichmentAgent, intakeInfoString, companyListAndPeopleStringEnriched)
    print("-------------Leads List results-------------------")
    print(leadsListString)
    final_results[userId] = leadsListString
    return

@app.get("/results")
async def getResults(request: Request):
    """API Endpoint that returns the leads list for the user"""

    user_agent = request.headers.get("user-agent")

    if user_agent in final_results:
        return final_results[user_agent]

    return "Leads haven't been generated yet"


async def runOrchestrator(userId: str):
    print("-------------started lead generation (AG2 orchestration)-------------------")
    config_list = config_list_from_json(env_or_file="OAI_CONFIG_LIST")

    userProxy = UserProxyAgent(name="userProxy", code_execution_config=False, human_input_mode="NEVER")

    def is_termination_msg(msg: dict[str, Any]) -> bool:
        content = msg.get("content", "")
        if (content is not None) and "\"complete\": true" in content:
            print("-------------Termination message received-------------------")
            return True
        return False

    # Compose the orchestration pattern
    pattern = AutoPattern(
        initial_agent=companyResearchAgent,
        agents=[
            companyResearchAgent,
            peopleFinderAgent,
            contactEnrichmentAgent,
            leadScoringAgent,
        ],
        user_agent=userProxy,
        group_manager_args={"llm_config": {"config_list": config_list}, "is_termination_msg": is_termination_msg},
    )
    agents_order = """ It is critical to transfer agents in the following exact order:
    1. companyResearchAgent
    2. peopleFinderAgent
    3. contactEnrichmentAgent
    4. leadScoringAgent

    """ + intakeAgent.intake_data

    # Run the group chat orchestration max_rounds=100,
    result, context_variables, last_agent = initiate_group_chat(
        pattern=pattern,
        messages=agents_order,
        max_rounds=13,
    )

    print("\n-----------------------------Conversation complete!---------------------------\n")

    # Extract the final leads list from the result
    leadsListString = result  # Adjust this if your agent outputs differently
    print("-------------GroupChat summary-------------------")
    print(leadsListString.summary)

    final_results[userId] = leadsListString.summary
    return