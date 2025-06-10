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

companyTestData = """
{
  "company_list": [
    {
      "name": "Westport Fuel Systems",
      "website": "https://www.westport.com",
      "description": "Westport Fuel Systems is a global leader in the design, manufacture, and supply of advanced fuel systems for clean, low-carbon fuels.",
      "industry": "Automotive Parts and Manufacturing",
      "location": "Vancouver, BC, Canada",
      "employee_count": "100-150",
      "annual_revenue": "$30M-$40M",
      "relevant_info": "Westport is a good fit for StreamERP due to its focus on clean energy solutions, which likely involves digital transformation, and operates multiple sites.",
      "relevance_score": 85
    },
    {
      "name": "Magna Seating",
      "website": "https://www.magnainc.com",
      "description": "Magna Seating is part of Magna International, specializing in seating solutions for the automotive industry.",
      "industry": "Automotive Parts",
      "location": "Aurora, ON, Canada",
      "employee_count": "100-200",
      "annual_revenue": "$20M-$50M",
      "relevant_info": "As part of Magna, this division likely undergoes digital transformation and operates multiple production sites.",
      "relevance_score": 90
    },
    {
      "name": "Martinrea International Inc.",
      "website": "https://www.martinrea.com",
      "description": "Martinrea International Inc. is a diversified global automotive supplier that provides lightweight castings, aluminum blocks, structural components, and fluid management systems.",
      "industry": "Automotive Parts",
      "location": "Vaughan, ON, Canada",
      "employee_count": "100-200",
      "annual_revenue": "$20M-$50M",
      "relevant_info": "Martinrea is a good fit due to its diverse operations and likely need for digital transformation across multiple sites.",
      "relevance_score": 92
    },
    {
      "name": "Accuride Corporation",
      "website": "https://www.accuridewheels.com",
      "description": "Accuride Corporation is a leading supplier of wheel end solutions to the global commercial vehicle industry.",
      "industry": "Automotive Parts",
      "location": "Evansville, IN, USA",
      "employee_count": "100-200",
      "annual_revenue": "$20M-$50M",
      "relevant_info": "Accuride operates multiple production sites and is likely undergoing digital transformation in its operations.",
      "relevance_score": 88
    },
    {
      "name": "Linamar Corporation",
      "website": "https://www.linamar.com",
      "description": "Linamar Corporation is a diversified global manufacturing company of highly engineered products across its Powertrain and Driveline, Industrial, and Skyjack segments.",
      "industry": "Automotive Parts and Manufacturing",
      "location": "Guelph, ON, Canada",
      "employee_count": "100-200",
      "annual_revenue": "$20M-$50M",
      "relevant_info": "Linamar operates multiple production sites and is likely undergoing digital transformation in its operations.",
      "relevance_score": 90
    }
  ]
}
"""

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
        asyncio.create_task(processIntakeData(user_agent))
        # asyncio.create_task(runOrchestrator(user_agent))
        
    
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
    # companyListString = companyTestData

    print("-------------Company List results-------------------")
    print(companyListString)

    # get people list
    companyListAndPeopleString = await peopleFinderAgent.process_message(companyResearchAgent, intakeInfoString, companyListString)
    print("-------------Company List and people results-------------------")
    print(companyListAndPeopleString)

    # enrich people list
    # companyListAndPeopleStringEnriched = await contactEnrichmentAgent.process_message(peopleFinderAgent, companyListAndPeopleString)

    # score leads
    leadsListString = await leadScoringAgent.process_message(contactEnrichmentAgent, intakeInfoString, companyListAndPeopleString)

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