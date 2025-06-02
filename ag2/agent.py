from autogen import UserProxyAgent, config_list_from_json, ConversableAgent, LLMConfig
from autogen.agents.experimental import DeepResearchAgent
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

import contextlib
import io
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
agent = ConversableAgent(
    name="ConversableAgent",
    llm_config={"config_list": config_list},
    system_message="You are an AI agent that can search the web to create a list of high quality sales leads for a product. The user will provide you with a product that they want to find leads for. After they provide you with the product, you will ask them for the necessary background information to find the leads. After you have the background information, you will use the web search or deep research agent to find the leads. Return the list of leads in a JSON format.",
    human_input_mode="NEVER"  # Don't ask for human input since we're in API mode
)
userProxy = UserProxyAgent(name="userProxy", code_execution_config=False)

async def process_message(message: str) -> str:
    """Process a single message and return the agent's response."""
    # Create a message in the format expected by the agent
    user_message = {
        "role": "user",
        "content": message
    }
    
    # Send the message to the agent
    agent.receive(user_message, userProxy)

    # Get the message history
    messages = []
    for msg in agent.chat_messages.get(userProxy, []):
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    messages.append(user_message)
    
    # Get the agent's reply
    reply = agent.generate_reply(messages=messages, sender=userProxy)
    
    if reply is None:
        return "I apologize, but I couldn't generate a response."
    
    return reply

@app.post("/chat")
async def chat(request: Request):
    """API Endpoint that handles individual messages while maintaining conversation history."""
    data = await request.json()
    user_query = data.get("message", "")

    # Process the message and get response
    response = await process_message(user_query)

    results = {
        "response": response,
        "message_history": [
            {
                "role": msg["role"],
                "content": msg["content"]
            }
            for msg in agent.chat_messages.get(userProxy, [])  # None is used as the default recipient
        ]
    }
    
    return results
