# agents/perplexity_client.py
import json
import os
import requests

from dotenv import load_dotenv
from jsonschema import ValidationError
from pydantic import BaseModel

load_dotenv()

class PerplexityClient():
    """
    Specialist agent for interacting with the Perplexity API and gathering information from the web.
    """

    def __init__(self,):
        self.API_URL = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {os.getenv("PERPLEXITY_API_KEY")}"
        }
        self.model = "sonar"
        self.max_tokens = 1000
        self.web_search_options = {"search_context_size": "high"}


    def search(self, system_prompt: str, user_prompt: str) -> str:
        """Processes a search request to the Perplexity API."""

        if not system_prompt:
            return "no system_prompt available"
        if not user_prompt:
            return "no user_prompt available"

        # Create a payload object for the API request
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": self.max_tokens,
            "web_search_options": self.web_search_options,
        }

        response = requests.post(self.API_URL, headers=self.headers, json=data, timeout=90)
        try:
            response.raise_for_status()
        except requests.exceptions.Timeout as e:
            raise RuntimeError(
                f"Perplexity API => Request timed out: {response.text}. Status code: {response.status_code}"
            ) from e
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(
                f"Perplexity API => HTTP error occurred: {response.text}. Status code: {response.status_code}"
            ) from e
        except requests.exceptions.RequestException as e:
            raise RuntimeError(
                f"Perplexity API => Error during request: {response.text}. Status code: {response.status_code}"
            ) from e

        try:
            response_json = response.json()
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Perplexity API => Invalid JSON response received. Error: {e}") from e

        try:
            # This may raise a pydantic.ValidationError if the response structure is not as expected.
            perp_resp = PerplexityChatCompletionResponse(**response_json)
        except ValidationError as e:
            raise RuntimeError("Perplexity API => Validation error when parsing API response: " + str(e)) from e
        except Exception as e:
            raise RuntimeError(
                "Perplexity API => Failed to parse API response into PerplexityChatCompletionResponse: " + str(e)
            ) from e

        return perp_resp.choices[0].message.content
      
    

class Usage(BaseModel):
    """
    Model representing token usage details.

    Attributes:
        prompt_tokens (int): The number of tokens used for the prompt.
        completion_tokens (int): The number of tokens generated in the completion.
        total_tokens (int): The total number of tokens (prompt + completion).
        search_context_size (str): The size context used in the search (e.g., "high").
    """

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    search_context_size: str

class Message(BaseModel):
    """
    Represents a message in the chat conversation.

    Attributes:
        role (str): The role of the message sender (e.g., "system", "user").
        content (str): The text content of the message.
    """

    role: str
    content: str

class Choice(BaseModel):
    """
    Represents one choice in the response from the Perplexity API.

    Attributes:
        index (int): The index of this choice.
        finish_reason (str): The reason why the API finished generating this choice.
        message (Message): The message object containing the response text.
    """

    index: int
    finish_reason: str
    message: Message

class PerplexityChatCompletionResponse(BaseModel):
    """
    Represents the full chat completion response from the Perplexity API.

    Attributes:
        id (str): Unique identifier for the response.
        model (str): The model name used for generating the response.
        created (int): Timestamp when the response was created.
        usage (Usage): Token usage details.
        citations (list[str]): list of citation strings included in the response.
        object (str): Type of the response object.
        choices (list[Choice]): list of choices returned by the API.
    """

    id: str
    model: str
    created: int
    usage: Usage
    citations: list[str]
    object: str
    choices: list[Choice]