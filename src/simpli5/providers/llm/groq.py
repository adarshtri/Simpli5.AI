from groq import Groq, APIStatusError
from .base import BaseLLMProvider

class GroqProvider(BaseLLMProvider):
    """
    A provider to interact with the Groq API for LLM chat completions.
    This class adheres to the BaseLLMProvider interface.
    """
    def __init__(self, api_key: str, model: str = "llama3-8b-8192"):
        """
        Initializes the GroqProvider.

        Args:
            api_key: The Groq API key.
            model: The name of the Groq model to use for chat completions.
        """
        self.api_key = api_key
        self.client = Groq(api_key=self.api_key)
        self.model = model
        print(f"Groq provider initialized with model: {self.model}")

    def generate_response(self, prompt: str) -> str:
        """
        Generates a response from the Groq LLM.

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
            return f"Error: Received status code {e.status_code} from Groq API."
        except Exception as e:
            return f"An unexpected error occurred: {e}" 