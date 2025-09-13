"""
LiteLLM Configuration and Error Handling
Provides robust configuration for handling LiteLLM API calls with fallbacks
"""

import os
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class LiteLLMConfig:
    """Configuration class for LiteLLM with error handling and fallbacks"""
    
    def __init__(self):
        self.setup_config()
    
    def setup_config(self):
        """Setup LiteLLM configuration with fallback models"""
        
        # Primary model configuration
        self.primary_config = {
            "model": "claude-3-5-sonnet",
            "max_tokens": 4000,
            "temperature": 0.3,
            "timeout": 60
        }
        
        # Fallback models in order of preference
        self.fallback_models = [
            {
                "model": "gpt-4o-mini",
                "max_tokens": 4000,
                "temperature": 0.3,
                "timeout": 60
            },
            {
                "model": "claude-3-haiku",
                "max_tokens": 4000,
                "temperature": 0.3,
                "timeout": 60
            },
            {
                "model": "gpt-3.5-turbo",
                "max_tokens": 4000,
                "temperature": 0.3,
                "timeout": 60
            }
        ]
        
        # Prompt length limits for different models
        self.prompt_limits = {
            "claude-3-5-sonnet": 200000,
            "claude-3-haiku": 200000,
            "gpt-4o-mini": 128000,
            "gpt-3.5-turbo": 16000,
            "default": 100000
        }
        
        # Error patterns to handle
        self.error_patterns = {
            "prompt_too_long": [
                "prompt is too long",
                "prompt too long",
                "context length exceeded",
                "maximum context length",
                "input too long"
            ],
            "rate_limit": [
                "rate limit",
                "too many requests",
                "quota exceeded"
            ],
            "auth_error": [
                "authentication",
                "api key",
                "unauthorized"
            ],
            "model_unavailable": [
                "model not found",
                "model unavailable",
                "service unavailable"
            ]
        }
    
    def get_prompt_limit(self, model: str) -> int:
        """Get prompt length limit for a specific model"""
        return self.prompt_limits.get(model, self.prompt_limits["default"])
    
    def truncate_prompt(self, prompt: str, model: str, safety_margin: int = 1000) -> str:
        """Truncate prompt to fit model's context window"""
        limit = self.get_prompt_limit(model) - safety_margin
        
        if len(prompt) <= limit:
            return prompt
        
        # Truncate and add indicator
        truncated = prompt[:limit-100]
        return truncated + "\n\n[Content truncated to fit context window...]"
    
    def classify_error(self, error_message: str) -> str:
        """Classify error type based on error message"""
        error_msg_lower = error_message.lower()
        
        for error_type, patterns in self.error_patterns.items():
            if any(pattern in error_msg_lower for pattern in patterns):
                return error_type
        
        return "unknown"
    
    def get_retry_strategy(self, error_type: str) -> Dict:
        """Get retry strategy based on error type"""
        strategies = {
            "prompt_too_long": {
                "retry": True,
                "truncate_more": True,
                "max_retries": 2
            },
            "rate_limit": {
                "retry": True,
                "delay": 5,
                "max_retries": 3
            },
            "auth_error": {
                "retry": False,
                "switch_model": True
            },
            "model_unavailable": {
                "retry": True,
                "switch_model": True,
                "max_retries": 1
            },
            "unknown": {
                "retry": True,
                "switch_model": True,
                "max_retries": 1
            }
        }
        
        return strategies.get(error_type, strategies["unknown"])

# Global configuration instance
litellm_config = LiteLLMConfig()

def setup_litellm_logging():
    """Setup logging for LiteLLM debugging"""
    import litellm
    
    # Enable LiteLLM logging
    litellm.set_verbose = True
    
    # Configure logging level
    logging.getLogger("litellm").setLevel(logging.WARNING)
    
    # Log configuration
    logger.info("LiteLLM logging configured")

def validate_environment():
    """Validate that required environment variables are set"""
    required_vars = []
    optional_vars = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY", 
        "VERTEX_AI_PROJECT",
        "VERTEX_AI_LOCATION"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing required environment variables: {missing_vars}")
    
    available_vars = []
    for var in optional_vars:
        if os.getenv(var):
            available_vars.append(var)
    
    logger.info(f"Available API configurations: {available_vars}")
    
    return len(available_vars) > 0

# Example usage and testing
if __name__ == "__main__":
    config = LiteLLMConfig()
    
    # Test prompt truncation
    long_prompt = "This is a very long prompt. " * 1000
    truncated = config.truncate_prompt(long_prompt, "gpt-3.5-turbo")
    print(f"Original length: {len(long_prompt)}")
    print(f"Truncated length: {len(truncated)}")
    
    # Test error classification
    errors = [
        "Vertex_aiException - prompt is too long",
        "Rate limit exceeded",
        "Invalid API key",
        "Model not found"
    ]
    
    for error in errors:
        error_type = config.classify_error(error)
        strategy = config.get_retry_strategy(error_type)
        print(f"Error: {error}")
        print(f"Type: {error_type}")
        print(f"Strategy: {strategy}")
        print("---")
