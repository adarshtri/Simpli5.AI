import os
import yaml
import json
import re
from typing import Dict, Optional, Any
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
        elif provider_name == 'openai':
            from .openai_provider import OpenAIProvider
            return OpenAIProvider
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
    
    def generate_json_response(self, prompt: str, fields: Dict[str, str], retry_count: int = 3):
        """
        Generates a JSON response with enforced field structure.
        
        Args:
            prompt: The user's prompt
            fields: Dictionary mapping field names to field descriptions
            retry_count: Number of retry attempts if JSON parsing fails
            
        Returns:
            SystemMessage object containing the parsed JSON response
            
        Raises:
            ValueError: If JSON parsing fails after all retry attempts
        """
        # Local import to avoid circular dependency
        from simpli5.agents.core.messages import SystemMessage
        
        if not self.default_provider:
            raise ValueError("No LLM provider is configured")
        
        # Build the JSON-enforced prompt
        json_prompt = self._build_json_prompt(prompt, fields)
        
        for attempt in range(retry_count):
            try:
                # Get response from LLM
                response = self.default_provider.generate_response(json_prompt)
                
                # Try to parse JSON
                parsed_response = self._parse_json_response(response)
                
                # Validate that all required fields are present
                self._validate_json_fields(parsed_response, fields.keys())
                
                # Return as SystemMessage object
                return SystemMessage(message=parsed_response)
                
            except (ValueError, KeyError) as e:
                if attempt == retry_count - 1:
                    # Last attempt failed
                    raise ValueError(f"Failed to generate valid JSON after {retry_count} attempts. Last error: {str(e)}")
                
                # Add more explicit instructions for retry
                json_prompt += f"\n\nIMPORTANT: Your previous response was not valid JSON. Please ensure you return ONLY valid JSON with these exact fields: {list(fields.keys())}"
        
        # This should never be reached, but just in case
        raise ValueError("Unexpected error in JSON generation")
    
    def _build_json_prompt(self, prompt: str, fields: Dict[str, str]) -> str:
        """Build a prompt that enforces JSON output."""
        
        fields_description = "\n".join([f"- {field_name}: {description}" for field_name, description in fields.items()])
        
        return f"""
{prompt}

IMPORTANT: You must respond with ONLY valid JSON. Do not include any other text, explanations, or formatting.

Required JSON fields:
{fields_description}

Example response format:
{{
{chr(10).join([f'    "{field_name}": "example_value"' for field_name in fields.keys()])}
}}

Remember: Return ONLY the JSON object, nothing else.
"""
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response, handling common LLM formatting issues."""
        
        # Clean the response
        cleaned_response = response.strip()
        
        # Remove markdown code blocks if present
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
        
        # Remove any leading/trailing whitespace
        cleaned_response = cleaned_response.strip()
        
        # Try to parse as JSON
        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            raise ValueError(f"Invalid JSON response: {str(e)}")
    
    def _validate_json_fields(self, response: Dict[str, Any], required_fields: set):
        """Validate that all required fields are present in the response."""
        missing_fields = required_fields - set(response.keys())
        if missing_fields:
            raise KeyError(f"Missing required fields: {missing_fields}") 