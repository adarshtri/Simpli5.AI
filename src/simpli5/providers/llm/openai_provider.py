from openai import OpenAI, APIStatusError
from .base import BaseLLMProvider

class OpenAIProvider(BaseLLMProvider):
    """
    A provider to interact with the OpenAI API for LLM chat completions.
    This class adheres to the BaseLLMProvider interface.
    """
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """
        Initializes the OpenAIProvider.

        Args:
            api_key: The OpenAI API key.
            model: The name of the OpenAI model to use for chat completions.
        """
        self.api_key = api_key
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        print(f"OpenAI provider initialized with model: {self.model}")

    def generate_response(self, prompt: str) -> str:
        """
        Generates a response from the OpenAI LLM.

        Args:
            prompt: The user's prompt to send to the LLM.

        Returns:
            The content of the LLM's response.
        """
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self.model,
            )
            return chat_completion.choices[0].message.content
        except APIStatusError as e:
            return f"Error: Received status code {e.status_code} from OpenAI API."
        except Exception as e:
            return f"An unexpected error occurred: {e}"
