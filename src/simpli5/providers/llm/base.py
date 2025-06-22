from abc import ABC, abstractmethod

class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers.

    This class defines the common interface that all concrete LLM provider
    implementations must adhere to, ensuring consistency and interchangeability.
    """

    @abstractmethod
    def __init__(self, api_key: str, model: str):
        """
        Initializes the provider with the necessary API key and model.

        Args:
            api_key: The API key for the LLM service.
            model: The specific model to be used for completions.
        """
        pass

    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        """
        Generates a response from the LLM based on a given prompt.

        Args:
            prompt: The user's input prompt to send to the LLM.

        Returns:
            The text content of the LLM's response.
        """
        pass 