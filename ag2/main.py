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

leadsTestData = """
{
  "complete": true,
  "leads_list": [
      {
          "name": "Rubina Ali",
          "title": "Chief Information Officer",
          "email": "",
          "phone": "",
          "linkedin": "",
          "relevant_info": "Rubina Ali is the Chief Information Officer at Flex-N-Gate and is likely responsible for IT decisions, making her a good fit for discussing cloud-based ERP solutions.",
          "relevance_score": 90,
          "approach_reccomendation": "Approach Rubina Ali by highlighting how StreamERP can enhance IT infrastructure and support digital transformation within Flex-N-Gate's operations.",
          "notes": "Rubina Ali's role suggests she would be interested in ERP solutions that improve IT operations.",
          "source_urls": ["https://rocketreach.co/flex-n-gate-management_b5c6c1d2f42e0ccf"],
          "company_info": {
              "name": "Flex-N-Gate Corporation",
              "website": "https://flex-n-gate.com",
              "description": "Manufactures interior and exterior plastics, metal bumpers, and towing devices for the automotive industry.",
              "industry": "Automotive Parts Manufacturing",
              "location": "Urbana, IL, USA",
              "employee_count": "Over 20,000 globally but likely smaller relevant units",
              "annual_revenue": "$7,024M",
              "relevant_info": "Flex-N-Gate operates multiple production sites and is likely undergoing digital transformation to remain competitive."
          }
      },
      {
          "name": "Dan Palazzolo",
          "title": "Chief Financial Officer",
          "email": "",
          "phone": "",
          "linkedin": "",
          "relevant_info": "Dan Palazzolo, as the CFO, could be interested in cost optimization and financial management aspects of StreamERP.",
          "relevance_score": 85,
          "approach_reccomendation": "Highlight to Dan Palazzolo how StreamERP can help streamline financial operations and improve cost efficiency.",
          "notes": "CFOs often focus on financial optimization, making them interested in cost-effective ERP solutions.",
          "source_urls": ["https://www.cbinsights.com/company/flex-n-gate/people"],
          "company_info": {
              "name": "Flex-N-Gate Corporation",
              "website": "https://flex-n-gate.com",
              "description": "Manufactures interior and exterior plastics, metal bumpers, and towing devices for the automotive industry.",
              "industry": "Automotive Parts Manufacturing",
              "location": "Urbana, IL, USA",
              "employee_count": "Over 20,000 globally but likely smaller relevant units",
              "annual_revenue": "$7,024M",
              "relevant_info": "Flex-N-Gate operates multiple production sites and is likely undergoing digital transformation to remain competitive."
          }
      },
      {
          "name": "Michael J. Lynch",
          "title": "President & COO",
          "email": "",
          "phone": "",
          "linkedin": "",
          "relevant_info": "Michael J. Lynch is the President & COO of American Axle & Manufacturing Holdings Inc., responsible for overseeing operations. His role makes him a good fit for discussing operational improvements and digital transformation.",
          "relevance_score": 90,
          "approach_reccomendation": "Reach out to Michael J. Lynch by highlighting how StreamERP can enhance operational efficiency and streamline processes, emphasizing the benefits of cloud-based solutions for automotive suppliers.",
          "notes": "Could not find email or LinkedIn URL for Michael J. Lynch. Assumed relevance based on title.",
          "source_urls": ["https://www.aam.com/who-we-are/leadership", "https://www.globaldata.com/company-profile/american-axle-manufacturing-holdings-inc/executives/"],
          "company_info": {
              "name": "American Axle & Manufacturing Holdings Inc.",
              "website": "https://www.aam.com",
              "description": "Specializes in driveline and metal forming components for the automotive industry.",
              "industry": "Automotive Parts Manufacturing",
              "location": "Detroit, MI, USA",
              "employee_count": "Over 20,000 globally",
              "annual_revenue": "$4,441M",
              "relevant_info": "American Axle operates multiple production sites and is involved in digital transformation to enhance efficiency."
          }
      },
      {
          "name": "Christopher J. May",
          "title": "Executive VP & CFO",
          "email": "",
          "phone": "",
          "linkedin": "",
          "relevant_info": "As the Executive VP & CFO, Christopher J. May oversees financial operations. He is a key decision-maker for financial and strategic investments, such as implementing new ERP solutions.",
          "relevance_score": 85,
          "approach_reccomendation": "Approach Christopher J. May by discussing the financial benefits and ROI of StreamERP, highlighting how it can improve financial management and planning.",
          "notes": "Could not find email or LinkedIn URL for Christopher J. May. Assumed relevance based on title.",
          "source_urls": ["https://www.globaldata.com/company-profile/american-axle-manufacturing-holdings-inc/executives/", "https://www.aam.com/who-we-are/leadership"],
          "company_info": {
              "name": "American Axle & Manufacturing Holdings Inc.",
              "website": "https://www.aam.com",
              "description": "Specializes in driveline and metal forming components for the automotive industry.",
              "industry": "Automotive Parts Manufacturing",
              "location": "Detroit, MI, USA",
              "employee_count": "Over 20,000 globally",
              "annual_revenue": "$4,441M",
              "relevant_info": "American Axle operates multiple production sites and is involved in digital transformation to enhance efficiency."
          }
      },
      {
          "name": "Joseph Fadool",
          "title": "President and CEO",
          "email": "",
          "phone": "",
          "linkedin": "",
          "relevant_info": "Joseph Fadool is the President and CEO of BorgWarner, overseeing the company's strategic direction and operations. He could be interested in enterprise solutions like StreamERP.",
          "relevance_score": 90,
          "approach_reccomendation": "Approach Joseph Fadool by highlighting StreamERP's ability to enhance operational efficiency and strategic alignment across BorgWarner's diverse product lines.",
          "notes": "Joseph Fadool's role as CEO positions him as a key decision-maker for strategic investments in technology and operations.",
          "source_urls": ["https://www.borgwarner.com/newsroom/press-releases/2024/11/07/borgwarner-announces-ceo-succession-plan", "https://www.borgwarner.com/company/leadership"],
          "company_info": {
              "name": "BorgWarner Inc.",
              "website": "https://www.borgwarner.com",
              "description": "Provides innovative solutions for combustion, hybrid and electric vehicles.",
              "industry": "Automotive Parts Manufacturing",
              "location": "Auburn Hills, MI, USA",
              "employee_count": "Over 50,000 globally",
              "annual_revenue": "$14.84B",
              "relevant_info": "BorgWarner operates globally and is undergoing significant digital transformation to support electric vehicle technologies."
          }
      },
      {
          "name": "Craig D. Aaron",
          "title": "Executive Vice President and Chief Financial Officer",
          "email": "",
          "phone": "",
          "linkedin": "",
          "relevant_info": "Craig Aaron is responsible for financial planning and operations. He could be interested in how StreamERP can optimize financial management and supply chain operations.",
          "relevance_score": 85,
          "approach_reccomendation": "Approach Craig Aaron by discussing how StreamERP can streamline financial processes and enhance supply chain efficiency.",
          "notes": "As CFO, Craig Aaron is likely interested in cost-saving and efficiency-enhancing solutions.",
          "source_urls": ["https://www.borgwarner.com/company/leadership", "https://www.globaldata.com/company-profile/borgwarner-inc/executives/"],
          "company_info": {
              "name": "BorgWarner Inc.",
              "website": "https://www.borgwarner.com",
              "description": "Provides innovative solutions for combustion, hybrid and electric vehicles.",
              "industry": "Automotive Parts Manufacturing",
              "location": "Auburn Hills, MI, USA",
              "employee_count": "Over 50,000 globally",
              "annual_revenue": "$14.84B",
              "relevant_info": "BorgWarner operates globally and is undergoing significant digital transformation to support electric vehicle technologies."
          }
      },
      {
          "name": "Jim Jarrell",
          "title": "CEO & President",
          "email": "",
          "phone": "",
          "linkedin": "",
          "relevant_info": "Jim Jarrell is the CEO and President of Linamar Corporation, overseeing overall strategy and operations, which includes aspects relevant to ERP solutions.",
          "relevance_score": 90,
          "approach_reccomendation": "Approach Jim Jarrell by highlighting the strategic benefits of StreamERP in enhancing operational efficiency and decision-making for automotive suppliers.",
          "notes": "I inferred relevance based on his role as CEO and President, which likely involves overseeing operations and technology decisions.",
          "source_urls": ["https://www.linamar.com/team/jim-jarrell/", "https://www.linamar.com/wp-content/uploads/2025/03/2024-MIC-Final.pdf"],
          "company_info": {
              "name": "Linamar Corporation",
              "website": "https://www.linamar.com",
              "description": "Manufacturer of precision metallic components for the automotive industry.",
              "industry": "Automotive Parts Manufacturing",
              "location": "Guelph, ON, Canada",
              "employee_count": "Over 20,000 globally",
              "annual_revenue": "$5B+ CAD",
              "relevant_info": "Linamar operates multiple production sites and is involved in digital transformation efforts."
          }
      },
      {
          "name": "Dale Schneider",
          "title": "Chief Financial Officer",
          "email": "",
          "phone": "",
          "linkedin": "",
          "relevant_info": "As CFO, Dale Schneider is responsible for financial strategies and operations, making him a key decision-maker for ERP systems.",
          "relevance_score": 95,
          "approach_reccomendation": "Engage Dale Schneider by discussing the financial benefits and cost optimizations offered by StreamERP.",
          "notes": "I inferred his role's relevance based on typical CFO responsibilities.",
          "source_urls": ["https://www.globaldata.com/company-profile/linamar-corp/executives/"],
          "company_info": {
              "name": "Linamar Corporation",
              "website": "https://www.linamar.com",
              "description": "Manufacturer of precision metallic components for the automotive industry.",
              "industry": "Automotive Parts Manufacturing",
              "location": "Guelph, ON, Canada",
              "employee_count": "Over 20,000 globally",
              "annual_revenue": "$5B+ CAD",
              "relevant_info": "Linamar operates multiple production sites and is involved in digital transformation efforts."
          }
      }
  ]
}
""".strip()

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

    # user_agent = request.headers.get("user-agent")

    # if user_agent in final_results:
    #     return final_results[user_agent]

    return leadsTestData
    # return "Leads haven't been generated yet"