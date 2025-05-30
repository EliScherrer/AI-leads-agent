from autogen import ConversableAgent, LLMConfig

# 1. Define LLM configuration for OpenAI's GPT-4o
#    uses the OPENAI_API_KEY environment variable - export OPENAI_API_KEY="XYZ"
llm_config = LLMConfig(api_type="openai", model="gpt-4o")

# 2. Create LLM agent
my_agent = ConversableAgent(
    name="research_agent",
    llm_config=llm_config,
    system_message="You are an AI agent that can search the web to create a list of high quality sales leads for a product. The user will provide you with a product that they want to find leads for. After they provide you with the product, you will ask them for the necessary background information to find the leads. After you have the background information, you will use the web search or deep research agent to find the leads. Return the list of leads in a JSON format.",
)

# 3. Run the agent with a prompt
response = my_agent.run(
    message="I need leads for settelers of catan",
    user_input=True
)

# 4. Iterate through the chat automatically with console output
response.process()

# 5. Print the chat
print(response.messages)