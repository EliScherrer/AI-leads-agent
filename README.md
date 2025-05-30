## Overview
Build an AI agent that can search the web to create a list of high quality leads for a product. The user should be able to input the production and the agent should ask the user the necessary background (use AG2 intake agent) and find great leads that would be a good match (use the AG2 web search or deep research agent). Add a nice looking frontend for this agent using React, Chakra, and Express.


### how to run
1. Build frontend
    1. cd /client
    2. npm i
    3. npm run build
2. Export openAI key for agent to use in CLI `export OPENAI_API_KEY="XYZ"`
3. Start express-server 
    1. cd /express-server
    2. npm i
    3. `node server.js`
4. Start ag2 agent
    1. `python3 agent.py`
5. Go to http://localhost:3000/ and chat



## TODO
### Agent Server
1. Start convo asking for product name
2. Ask user for background information (AG2 intake agent)
3. Use agent to find leads (web search or deep research agent)
4. Return list of leads

### Node Server
1. Host React frontend
2. Web requests for communicating with agent server

### Frontend
1. simple single page website
2. chat window
