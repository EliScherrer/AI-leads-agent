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
from agents.research_agent.research_agent import ResearchAgent
from agents.tsv_output_agent import TSVOutputAgent
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from agents.research_agent.schemas import (
    OrchestrationContext,
    SessionDetails,
    AgentsContext,
    AgentContextEntry,
)
from agents.research_agent.my_context_vars import StrictContextVariables
from datetime import datetime

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

company_google_research_agent = ResearchAgent(
        search_mode=True,
        scrape_mode=False,
        queries_per_search=5,
        name="company_google_research_agent",
        additional_instructions="""
    Research Goal:
    - Find companies that match the ICP for a sales agent at company_info to sell product_info to.
    - Look at the structured JSON input to get company_info, product_info, and ICP 
    - The research goal should be to find companies that match the ICP for a sales agent at company_info to sell product_info to.
    - the companies do not have to exactly match the ICP, try to find at least 3 and at most 10 that you think most closely match a company that a sales agent at company_info may be able to sell product_info to.
    
    Critical Instructions:
    - Ensure all points above are put into the research goal and the ICO is captured in its entirety.
    - The output should be a list of companies that match the ICP for a sales agent at company_info to sell product_info to.
    
    - The output should be in the following format (this is just example data):
    {
        "company_list": [
            "company_info": {
            "name": "SupplyStream Technologies",
            "website": "https://www.supplystreamtech.com",
            "description": "SupplyStream Technologies provides AI-driven ERP solutions for mid-sized automotive manufacturers, streamlining operations from procurement to distribution.",
            "industry": "B2B SaaS",
            "location": "Detroit, MI",
            "employee_count": 45,
            "annual_revenue": "12M",
            "relevant_info": "This company is a good fit for the ICP because they are a mid-sized automotive manufacturer that is undergoing digital transformation and operating multiple production sites.",
            "relevance_score": 95
            }
        ]
    }
    """,
        additional_functions=[],
    )
people_google_research_agent = ResearchAgent(
        search_mode=True,
        scrape_mode=False,
        queries_per_search=5,
        name="people_google_research_agent",
        additional_instructions="""
    Research Goal:
    - Find leads that match the ICP for a sales agent at company_info to sell product_info to.
    - search for people at the companies in the company_list that is provided to you in the structured JSON input
    - Look at the structured JSON input to get company_info, product_info, and ICP 
    - The research goal should be to find people that match the ICP for a sales agent at company_info to sell product_info to.
    - the people do not have to exactly match the ICP, try to find at least 3 and at most 10 that you think most closely match a person that a sales agent at company_info may be able to sell product_info to.
    - Use fuzzy title matching and job summaries to infer role alignment.
    
    Critical Instructions:
    - Ensure all points above are put into the research goal and the ICO is captured in its entirety.
    - The output should be a list of companies with peoplethat match the ICP for a sales agent at company_info to sell product_info to.
    
    - The output should be in the following format (this is just example data):
{
    "company_list": [
        "company_info": {
          "name": "SupplyStream Technologies",
          "website": "https://www.supplystreamtech.com",
          "description": "SupplyStream Technologies provides AI-driven ERP solutions for mid-sized automotive manufacturers, streamlining operations from procurement to distribution.",
          "industry": "B2B SaaS",
          "location": "Detroit, MI",
          "employee_count": 45,
          "annual_revenue": "12M",
          "relevant_info": "This company is a good fit for the ICP because they are a mid-sized automotive manufacturer that is undergoing digital transformation and operating multiple production sites.",
          "relevance_score": 83,
          "people_list": [
              "person_info": {
                  "name": "John Doe",
                  "title": "COO",
                  "email": "john.doe@supplystreamtech.com",
                  "phone": "123-456-7890",
                  "linkedin": "https://www.linkedin.com/in/john-doe-1234567890",
                  "relevant_info": "John Doe is the COO of SupplyStream Technologies and is responsible for the overall operations of the company.",
                  "relevance_score": 95,
                  "approach_reccomendation": "I would approach John Doe by saying 'Hello, I'm from SupplyStream Technologies and we provide AI-driven ERP solutions for mid-sized automotive manufacturers. We're looking for a COO like you who is interested in digital transformation and streamlining operations. Would you be interested in a demo?'",
                  "notes": "I found this information on the company website. The phone number I'm not sure if it's still valid. the email might be John's or steve hammond's",
                  "source_url": "https://www.supplystreamtech.com/people/john-doe"
              }
          ]
        }
    ]
}
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
            company_google_research_agent,
            peopleFinderAgent,
            people_google_research_agent,
            # contactEnrichmentAgent,
            leadScoringAgent,
        ],
        user_agent=userProxy,
        context_variables=get_context_variables(),
        group_manager_args={"llm_config": {"config_list": config_list}, "is_termination_msg": is_termination_msg},
    )
    agents_order = """ It is critical to transfer agents in the following exact order:
    1. companyResearchAgent
    2. company_google_research_agent
    3. companyResearchAgent
    4. peopleFinderAgent
    5. people_google_research_agent
    6. peopleFinderAgent
    7. leadScoringAgent

    """ + intakeAgent.intake_data
    # 7. contactEnrichmentAgent


    # Run the group chat orchestration max_rounds=100,
    result, context_variables, last_agent = initiate_group_chat(
        pattern=pattern,
        messages=agents_order,
        max_rounds=40,
    )

    print("\n-----------------------------Conversation complete!---------------------------\n")

    # Extract the final leads list from the result
    leadsListString = result  # Adjust this if your agent outputs differently
    print("-------------GroupChat summary-------------------")
    print(leadsListString.summary)

    final_results[userId] = leadsListString.summary
    return

def get_context_variables():
    orchard_ctx = OrchestrationContext(
        session_details=SessionDetails(
            session_id="123-1-2222-989",
            session_started=datetime.utcnow().isoformat(),
        ),
        agents=AgentsContext(
            root={
                "CompanyResearchAgent": [
                    AgentContextEntry(
                        technical_name="intake_data",
                        description="Contains the intake data.",
                        data={
                            "intake_data": intakeAgent.intake_data,
                            "discovery_complete": True,
                        },
                    ),
                    AgentContextEntry(
                        technical_name="company_list",
                        description="Consists of the companies that match the ICP.",
                        data={"company_list": []},
                    ),
                ],
                "company_google_research_agent": [
                    AgentContextEntry(
                        technical_name="research-profile",
                        description="Data store for all research. We'll store 'researched_websites' here.",
                        data={
                            "search_queries": [],
                            "researched_websites": [],
                            "research_completed": False,
                        },
                    ),
                    AgentContextEntry(
                        technical_name="google-search-metrics",
                        description="All metrics related to Google Search to ensure rate limits are respected.",
                        data={
                            "rate_limit_per_minute": 100,
                            "search_requests_made": {},
                            "available_searches_now_per_minute": 100,
                        },
                    ),
                ],
                "PeopleFinderAgent": [
                    AgentContextEntry(
                        technical_name="company_list",
                        description="Consists of the companies and people at those companies that match the ICP.",
                        data={"company_list": []},
                    ),
                ],
                "people_google_research_agent": [
                    AgentContextEntry(
                        technical_name="research-profile",
                        description="Data store for all research. We'll store 'researched_websites' here.",
                        data={
                            "search_queries": [],
                            "researched_websites": [],
                            "research_completed": False,
                        },
                    ),
                    AgentContextEntry(
                        technical_name="google-search-metrics",
                        description="All metrics related to Google Search to ensure rate limits are respected.",
                        data={
                            "rate_limit_per_minute": 100,
                            "search_requests_made": {},
                            "available_searches_now_per_minute": 100,
                        },
                    ),
                ],
                "ContactEnrichmentAgent": [
                    AgentContextEntry(
                        technical_name="company_list",
                        description="Consists of the companies and people at those companies that match the ICP.",
                        data={"company_list": []},
                    ),
                ],
                "LeadScoringAgent": [
                    AgentContextEntry(
                        technical_name="leads_list",
                        description="Consists of the leads at the companies that match the ICP.",
                        data={"leads_list": []},
                    ),
                ],
            }
        ),
    )

    ctx = StrictContextVariables(data={"orchestration_context": orchard_ctx})
    return ctx