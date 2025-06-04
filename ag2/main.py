from autogen import config_list_from_json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from intake_agent import IntakeAgent

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
agent = IntakeAgent()

@app.post("/chat")
async def chat(request: Request):
    """API Endpoint that handles individual messages while maintaining conversation history."""
    data = await request.json()
    user_query = data.get("message", "")

    # Process the message and get response
    response = await agent.process_message(user_query)

    results = {
        "response": response,
        "message_history": [
            {
                "role": msg["role"],
                "content": msg["content"]
            }
            for msg in agent.agent.chat_messages.get(agent.userProxy, [])  # None is used as the default recipient
        ]
    }
    
    return results
