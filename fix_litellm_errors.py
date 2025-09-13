#!/usr/bin/env python3
"""
LiteLLM Error Fix Script
Addresses the "prompt too long" error and provides robust error handling
"""

import sys
import os
import json
import logging
from typing import Dict, List, Optional, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LiteLLMErrorHandler:
    """Handles LiteLLM errors with robust fallback mechanisms"""
    
    def __init__(self):
        self.setup_config()
        self.litellm_available = self.check_litellm_availability()
    
    def check_litellm_availability(self) -> bool:
        """Check if LiteLLM is available and properly configured"""
        try:
            import litellm
            logger.info("LiteLLM is available")
            return True
        except ImportError:
            logger.warning("LiteLLM not installed. Install with: pip install litellm")
            return False
    
    def setup_config(self):
        """Setup configuration for error handling"""
        self.model_configs = {
            "claude-3-5-sonnet": {
                "max_context": 200000,
                "safe_limit": 150000,
                "provider": "anthropic"
            },
            "claude-3-haiku": {
                "max_context": 200000,
                "safe_limit": 150000,
                "provider": "anthropic"
            },
            "gpt-4o-mini": {
                "max_context": 128000,
                "safe_limit": 100000,
                "provider": "openai"
            },
            "gpt-3.5-turbo": {
                "max_context": 16000,
                "safe_limit": 12000,
                "provider": "openai"
            }
        }
        
        self.fallback_chain = [
            "gpt-4o-mini",
            "claude-3-haiku", 
            "gpt-3.5-turbo"
        ]
    
    def estimate_token_count(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Rough estimation: 1 token ≈ 4 characters for English text
        return len(text) // 4
    
    def truncate_text_smart(self, text: str, max_tokens: int) -> str:
        """Smart text truncation that preserves structure"""
        estimated_tokens = self.estimate_token_count(text)
        
        if estimated_tokens <= max_tokens:
            return text
        
        # Calculate character limit based on token estimate
        char_limit = max_tokens * 4
        
        # Try to truncate at sentence boundaries
        sentences = text.split('. ')
        truncated = ""
        
        for sentence in sentences:
            test_text = truncated + sentence + ". "
            if len(test_text) > char_limit - 200:  # Leave margin for truncation notice
                break
            truncated = test_text
        
        if not truncated:  # Fallback if no complete sentences fit
            truncated = text[:char_limit - 200]
        
        return truncated + "\n\n[Content truncated to fit context window]"
    
    def handle_prompt_too_long_error(self, prompt: str, model: str) -> str:
        """Handle prompt too long error by truncating intelligently"""
        config = self.model_configs.get(model, self.model_configs["gpt-3.5-turbo"])
        safe_limit = config["safe_limit"]
        
        logger.warning(f"Prompt too long for {model}, truncating to {safe_limit} tokens")
        return self.truncate_text_smart(prompt, safe_limit)
    
    def call_with_fallback(self, prompt: str, **kwargs) -> Optional[str]:
        """Call LiteLLM with comprehensive error handling and fallbacks"""
        if not self.litellm_available:
            logger.error("LiteLLM not available")
            return None
        
        import litellm
        
        # Start with primary model or specified model
        primary_model = kwargs.get('model', 'claude-3-5-sonnet')
        models_to_try = [primary_model] + [m for m in self.fallback_chain if m != primary_model]
        
        original_prompt = prompt
        
        for attempt, model in enumerate(models_to_try):
            try:
                logger.info(f"Attempt {attempt + 1}: Trying model {model}")
                
                # Prepare the prompt for this model
                current_prompt = self.prepare_prompt_for_model(original_prompt, model)
                
                # Make the API call
                response = litellm.completion(
                    model=model,
                    messages=[{"role": "user", "content": current_prompt}],
                    max_tokens=kwargs.get('max_tokens', 4000),
                    temperature=kwargs.get('temperature', 0.3),
                    timeout=kwargs.get('timeout', 60)
                )
                
                logger.info(f"Success with model {model}")
                return response.choices[0].message.content
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Error with model {model}: {error_msg}")
                
                # Handle specific error types
                if self.is_prompt_too_long_error(error_msg):
                    # Try with truncated prompt
                    truncated_prompt = self.handle_prompt_too_long_error(original_prompt, model)
                    try:
                        response = litellm.completion(
                            model=model,
                            messages=[{"role": "user", "content": truncated_prompt}],
                            max_tokens=kwargs.get('max_tokens', 4000),
                            temperature=kwargs.get('temperature', 0.3),
                            timeout=kwargs.get('timeout', 60)
                        )
                        logger.info(f"Success with truncated prompt on {model}")
                        return response.choices[0].message.content
                    except Exception as e2:
                        logger.warning(f"Truncated prompt also failed for {model}: {str(e2)}")
                        continue
                
                elif self.is_rate_limit_error(error_msg):
                    logger.warning(f"Rate limit hit for {model}, trying next model")
                    continue
                
                elif self.is_auth_error(error_msg):
                    logger.warning(f"Authentication error for {model}, trying next model")
                    continue
                
                else:
                    logger.warning(f"Unknown error for {model}, trying next model")
                    continue
        
        logger.error("All models failed")
        return None
    
    def prepare_prompt_for_model(self, prompt: str, model: str) -> str:
        """Prepare prompt for specific model"""
        config = self.model_configs.get(model, self.model_configs["gpt-3.5-turbo"])
        safe_limit = config["safe_limit"]
        
        estimated_tokens = self.estimate_token_count(prompt)
        if estimated_tokens > safe_limit:
            return self.truncate_text_smart(prompt, safe_limit)
        
        return prompt
    
    def is_prompt_too_long_error(self, error_msg: str) -> bool:
        """Check if error is related to prompt length"""
        error_patterns = [
            "prompt is too long",
            "prompt too long", 
            "context length exceeded",
            "maximum context length",
            "input too long",
            "token limit exceeded"
        ]
        return any(pattern in error_msg.lower() for pattern in error_patterns)
    
    def is_rate_limit_error(self, error_msg: str) -> bool:
        """Check if error is related to rate limiting"""
        error_patterns = [
            "rate limit",
            "too many requests",
            "quota exceeded",
            "rate_limit_exceeded"
        ]
        return any(pattern in error_msg.lower() for pattern in error_patterns)
    
    def is_auth_error(self, error_msg: str) -> bool:
        """Check if error is related to authentication"""
        error_patterns = [
            "authentication",
            "api key",
            "unauthorized",
            "invalid_api_key",
            "permission denied"
        ]
        return any(pattern in error_msg.lower() for pattern in error_patterns)

def demonstrate_error_handling():
    """Demonstrate the error handling capabilities"""
    handler = LiteLLMErrorHandler()
    
    # Test with a very long prompt
    long_prompt = """
    This is a demonstration of handling very long prompts that might exceed the context window.
    """ * 1000  # Make it very long
    
    print(f"Original prompt length: {len(long_prompt)} characters")
    print(f"Estimated tokens: {handler.estimate_token_count(long_prompt)}")
    
    # Test truncation
    truncated = handler.truncate_text_smart(long_prompt, 1000)
    print(f"Truncated length: {len(truncated)} characters")
    print(f"Truncated tokens: {handler.estimate_token_count(truncated)}")
    
    # Test actual API call (if LiteLLM is available)
    if handler.litellm_available:
        print("\nTesting API call with fallback...")
        response = handler.call_with_fallback(
            "Explain what artificial intelligence is in one sentence.",
            model="claude-3-5-sonnet",
            max_tokens=100
        )
        
        if response:
            print(f"Response: {response}")
        else:
            print("All API calls failed - this is expected if no API keys are configured")
    else:
        print("LiteLLM not available - install with: pip install litellm")

def create_environment_template():
    """Create a template .env file for API configuration"""
    env_template = """
# LiteLLM API Configuration
# Uncomment and fill in the API keys you want to use

# OpenAI
# OPENAI_API_KEY=your_openai_api_key_here

# Anthropic (Claude)
# ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Google Vertex AI
# VERTEX_AI_PROJECT=your_project_id
# VERTEX_AI_LOCATION=us-central1
# GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Azure OpenAI
# AZURE_API_KEY=your_azure_api_key
# AZURE_API_BASE=https://your-resource.openai.azure.com/
# AZURE_API_VERSION=2023-05-15

# Debugging
# LITELLM_LOG=DEBUG
"""
    
    with open('.env.template', 'w') as f:
        f.write(env_template.strip())
    
    print("Created .env.template file with API configuration examples")

def main():
    """Main function to run the error handling demonstration"""
    print("LiteLLM Error Handler - Fixing 'prompt too long' errors")
    print("=" * 60)
    
    # Create environment template
    create_environment_template()
    
    # Demonstrate error handling
    demonstrate_error_handling()
    
    print("\n" + "=" * 60)
    print("Error handling setup complete!")
    print("\nTo use this in your application:")
    print("1. Install LiteLLM: pip install litellm")
    print("2. Configure API keys in .env file (see .env.template)")
    print("3. Import and use LiteLLMErrorHandler in your code")
    print("\nExample usage:")
    print("""
from fix_litellm_errors import LiteLLMErrorHandler

handler = LiteLLMErrorHandler()
response = handler.call_with_fallback(
    "Your prompt here",
    model="claude-3-5-sonnet",
    max_tokens=4000
)
""")

if __name__ == "__main__":
    main()
