import os
import yaml
from typing import Dict, Optional
from .base import BaseLLMProvider

class MultiLLMProvider:
    """
    Manages multiple LLM providers based on a configuration file.
    
    This class loads enabled LLM providers from 'config/llm_providers.yml',
    initializes them, and provides a simple interface to use the default provider.
    """

    def __init__(self, config_path: str = "config/llm_providers.yml"):
        """
        Initializes the MultiLLMProvider.

        Args:
            config_path: The path to the LLM providers configuration file.
        """
        self.config_path = config_path
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.default_provider: Optional[BaseLLMProvider] = None
        self._load_providers()

    def _load_providers(self):
        """Loads and initializes LLM providers from the config file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"LLM config file not found at {self.config_path}. LLM functionality will be disabled.")
            return
        except Exception as e:
            print(f"Error loading LLM config file: {e}. LLM functionality will be disabled.")
            return

        for name, settings in config.get("llm_providers", {}).items():
            if settings.get("enabled"):
                try:
                    api_key = os.environ[settings["api_key_env"]]
                    provider_class = self._get_provider_class(settings["provider"])
                    
                    provider_instance = provider_class(
                        api_key=api_key,
                        model=settings["default_model"]
                    )
                    
                    self.providers[name] = provider_instance
                    print(f"Successfully initialized LLM provider: {name}")

                    # Set the first enabled provider as the default
                    if self.default_provider is None:
                        self.default_provider = provider_instance
                        print(f"Set '{name}' as the default LLM provider.")

                except KeyError:
                    print(f"Warning: Environment variable '{settings['api_key_env']}' not found for LLM provider '{name}'. This provider will be disabled.")
                except Exception as e:
                    print(f"Warning: Failed to initialize LLM provider '{name}'. Error: {e}. This provider will be disabled.")
    
    def _get_provider_class(self, provider_name: str) -> type[BaseLLMProvider]:
        """Dynamically imports and returns a provider class."""
        if provider_name == 'groq':
            from .groq import GroqProvider
            return GroqProvider
        # Add other providers here in the future
        # elif provider_name == 'openai':
        #     from .openai_provider import OpenAIProvider
        #     return OpenAIProvider
        else:
            raise ImportError(f"LLM provider '{provider_name}' is not supported.")

    def has_provider(self) -> bool:
        """Checks if at least one LLM provider is configured and enabled."""
        return self.default_provider is not None

    def generate_response(self, prompt: str) -> str:
        """
        Generates a response using the default LLM provider.

        Args:
            prompt: The user's prompt.

        Returns:
            The LLM's response, or an error message if no provider is available.
        """
        if self.default_provider:
            return self.default_provider.generate_response(prompt)
        
        return "No LLM provider is configured. Please check your 'config/llm_providers.yml' and ensure the required API key environment variables are set." 