"""
LLM Client - Azure OpenAI integration for RCA Agent
"""

from typing import Dict, Any, List, Optional
import logging
import os
from openai import OpenAI


class LLMClient:
    """Client for interacting with Azure OpenAI API"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize Azure OpenAI client
        
        Args:
            config: Configuration dictionary with Azure OpenAI settings
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Get configuration from config or environment variables
        self.azure_endpoint = self.config.get('azure_endpoint') or os.getenv('AZURE_OPENAI_ENDPOINT')
        self.api_key = self.config.get('api_key') or os.getenv('AZURE_OPENAI_API_KEY')
        self.api_version = self.config.get('api_version') or os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
        self.deployment_name = self.config.get('deployment_name') or os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4')
        self.model = self.config.get('model') or os.getenv('AZURE_OPENAI_MODEL', 'gpt-4')
        self.temperature = self.config.get('temperature', 0.7)
        self.max_tokens = self.config.get('max_tokens', 2000)
        
        # For newer models (GPT-4o, GPT-5, etc.), use max_completion_tokens instead of max_tokens
        self.use_max_completion_tokens = True  # Default for newer models
        
        # Validate required settings
        if not self.azure_endpoint or not self.api_key:
            raise ValueError("Azure OpenAI endpoint and API key are required. Set them in config or environment variables.")
        
        # Initialize OpenAI client with custom base URL for APIM
        # Construct the base URL for the specific deployment
        # Format: {endpoint}/deployments/{deployment_name}
        base_url = f"{self.azure_endpoint}/deployments/{self.deployment_name}"
        
        try:
            self.client = OpenAI(
                base_url=base_url,
                api_key=self.api_key,
                default_headers={
                    "api-key": self.api_key
                },
                default_query={
                    "api-version": self.api_version
                }
            )
            self.logger.info(f"Azure OpenAI client initialized successfully")
            self.logger.info(f"Base URL: {base_url}")
            self.logger.info(f"Deployment: {self.deployment_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Azure OpenAI client: {str(e)}")
            raise
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a chat completion
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Optional temperature override
            max_tokens: Optional max_tokens override (will use max_completion_tokens for newer models)
            **kwargs: Additional parameters for the API call
            
        Returns:
            Response dictionary from Azure OpenAI
        """
        try:
            # Prepare parameters
            params = {
                "model": self.deployment_name,
                "messages": messages,
                "temperature": temperature or self.temperature,
            }
            
            # Use max_completion_tokens for newer models, max_tokens for older ones
            token_limit = max_tokens or self.max_tokens
            if self.use_max_completion_tokens:
                params["max_completion_tokens"] = token_limit
            else:
                params["max_tokens"] = token_limit
            
            # Add any additional kwargs
            params.update(kwargs)
            
            response = self.client.chat.completions.create(**params)
            
            self.logger.debug(f"Chat completion successful. Usage: {response.usage}")
            
            return {
                "content": response.choices[0].message.content,
                "role": response.choices[0].message.role,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": response.model
            }
        
        except Exception as e:
            self.logger.error(f"Chat completion failed: {str(e)}")
            raise
    
    def analyze_text(
        self,
        prompt: str,
        system_message: str = "You are a helpful AI assistant for root cause analysis.",
        **kwargs
    ) -> str:
        """
        Analyze text with a simple prompt
        
        Args:
            prompt: User prompt
            system_message: System message to set context
            **kwargs: Additional parameters
            
        Returns:
            Response content as string
        """
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat_completion(messages, **kwargs)
        return response["content"]
    
    def analyze_with_context(
        self,
        question: str,
        context: str,
        system_message: str = "You are an expert in software debugging and root cause analysis.",
        **kwargs
    ) -> str:
        """
        Analyze a question with provided context
        
        Args:
            question: The question to answer
            context: Context information
            system_message: System message
            **kwargs: Additional parameters
            
        Returns:
            Response content as string
        """
        prompt = f"""Context:
{context}

Question:
{question}

Please provide a detailed analysis based on the context provided."""
        
        return self.analyze_text(prompt, system_message, **kwargs)
    
    def generate_structured_response(
        self,
        prompt: str,
        system_message: str = "You are a helpful assistant. Always respond in valid JSON format.",
        **kwargs
    ) -> str:
        """
        Generate a structured response (useful for JSON outputs)
        
        Args:
            prompt: User prompt
            system_message: System message
            **kwargs: Additional parameters
            
        Returns:
            Response content as string (parse as needed)
        """
        return self.analyze_text(prompt, system_message, **kwargs)


# Singleton instance
_llm_client_instance = None


def get_llm_client(config: Dict[str, Any] = None) -> LLMClient:
    """
    Get or create LLM client singleton
    
    Args:
        config: Configuration dictionary
        
    Returns:
        LLMClient instance
    """
    global _llm_client_instance
    
    if _llm_client_instance is None:
        _llm_client_instance = LLMClient(config)
    
    return _llm_client_instance


def reset_llm_client():
    """Reset the LLM client singleton (useful for testing)"""
    global _llm_client_instance
    _llm_client_instance = None
