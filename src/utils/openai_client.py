import openai
import os
from typing import Optional, Type, TypeVar
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class OpenAIClient:
    """
    OpenAI API wrapper with structured output support for reliability
    """
    def __init__(self, api_key: Optional[str] = None):
        # Use provided key, fallback to environment variable
        self.client = openai.OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY")
        )
        
        # Default model configs per agent type
        self.agent_models = {
            "scout": "gpt-4.1-mini",      # Fast, cheap research
            "writer": "gpt-4.1",           # Best quality for scripts
            "validator": "gpt-4.1-mini"    # Fast validation
        }
        
        self.agent_temps = {
            "scout": 0.3,      # Factual
            "writer": 0.8,     # Creative
            "validator": 0.2   # Consistent
        }
    
    def call_agent(
        self,
        agent_type: str,
        system_prompt: str,
        user_message: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 2048
    ) -> str:
        """
        Standard text completion for open-ended responses
        """
        model = model or self.agent_models.get(agent_type, "gpt-4.1-mini")
        temperature = temperature or self.agent_temps.get(agent_type, 0.7)
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"OpenAI API error for {agent_type}: {e}")
            raise
    
    def call_agent_structured(
        self,
        agent_type: str,
        system_prompt: str,
        user_message: str,
        response_format: Type[T],
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> T:
        """
        Structured output with Pydantic schema 
        """
        model = model or self.agent_models.get(agent_type, "gpt-4.1-mini")
        temperature = temperature or self.agent_temps.get(agent_type, 0.7)
        
        try:
            response = self.client.beta.chat.completions.parse(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                response_format=response_format,
                temperature=temperature
            )
            
            # Returns typed Pydantic object, not string
            return response.choices[0].message.parsed
        
        except Exception as e:
            print(f"Structured output failed for {agent_type}: {e}")
            raise
