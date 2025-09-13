# LiteLLM "Prompt Too Long" Error - Complete Solution

## Problem Analysis

The error you encountered:
```
litellm.APIConnectionError: Vertex_aiException - b'{"type":"error","error":{"type":"invalid_request_error","message":"Prompt is too long"},"request_id":"req_vrtx_011CT5xpzTVdYkPnLUMaP6oT"}'
```

This indicates that:
1. You're using LiteLLM with Vertex AI (Google Cloud)
2. The prompt exceeds the model's context window
3. The fallback system isn't working properly
4. No suitable fallback models are configured

## Root Cause

The error occurs when:
- Input text exceeds the model's maximum context length
- Fallback models are misconfigured or unavailable
- API keys for fallback providers are missing
- The prompt truncation logic is insufficient

## Complete Solution

### 1. Install Dependencies

```bash
pip install litellm==1.44.0
```

### 2. Use the Enhanced Error Handler

The solution provides a robust `LiteLLMErrorHandler` class that:
- Automatically detects prompt length issues
- Intelligently truncates prompts while preserving structure
- Implements a fallback chain across multiple providers
- Handles authentication and rate limit errors

### 3. Implementation

#### Basic Usage:
```python
from fix_litellm_errors import LiteLLMErrorHandler

# Initialize the handler
handler = LiteLLMErrorHandler()

# Make a robust API call
response = handler.call_with_fallback(
    prompt="Your long prompt here...",
    model="claude-3-5-sonnet",
    max_tokens=4000,
    temperature=0.3
)

if response:
    print("Success:", response)
else:
    print("All models failed")
```

#### Integration with Existing Code:
```python
# Replace your existing LiteLLM calls
# OLD:
# response = litellm.completion(model="claude-3-5-sonnet", messages=[...])

# NEW:
handler = LiteLLMErrorHandler()
response_text = handler.call_with_fallback(
    prompt=your_prompt,
    model="claude-3-5-sonnet"
)
```

### 4. Configuration

#### API Keys Setup:
Create a `.env` file with your API keys:
```bash
# Choose one or more providers
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# For Vertex AI (Google Cloud)
VERTEX_AI_PROJECT=your_project_id
VERTEX_AI_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
```

#### Model Configuration:
The handler automatically configures safe limits for each model:
- Claude 3.5 Sonnet: 150,000 tokens (safe limit)
- GPT-4o Mini: 100,000 tokens (safe limit)
- Claude 3 Haiku: 150,000 tokens (safe limit)
- GPT-3.5 Turbo: 12,000 tokens (safe limit)

### 5. Error Handling Features

#### Intelligent Prompt Truncation:
- Preserves sentence boundaries when possible
- Adds clear truncation indicators
- Maintains context relevance

#### Fallback Chain:
1. Primary model (e.g., Claude 3.5 Sonnet)
2. GPT-4o Mini (high capacity, cost-effective)
3. Claude 3 Haiku (fast, efficient)
4. GPT-3.5 Turbo (reliable fallback)

#### Error Classification:
- **Prompt too long**: Auto-truncate and retry
- **Rate limits**: Switch to different provider
- **Authentication**: Try alternative API keys
- **Model unavailable**: Use fallback models

### 6. Integration with Your Talent Platform

#### Update your AI models:
```python
# In models/ai_models.py, replace the simple parsing with:
from fix_litellm_errors import LiteLLMErrorHandler

class TalentMatcher:
    def __init__(self):
        # ... existing code ...
        self.llm_handler = LiteLLMErrorHandler()
    
    def parse_resume_with_llm(self, resume_text: str) -> Dict:
        prompt = f"""
        Parse this resume and extract:
        - name, skills, experience_years, education, certifications
        
        Resume: {resume_text}
        
        Return JSON only.
        """
        
        response = self.llm_handler.call_with_fallback(
            prompt=prompt,
            model="claude-3-5-sonnet",
            max_tokens=1000
        )
        
        if response:
            try:
                return json.loads(response)
            except:
                pass
        
        # Fallback to simple parsing
        return self.parse_resume_simple(resume_text)
```

### 7. Testing the Solution

Run the test script:
```bash
python3 fix_litellm_errors.py
```

This will:
- Test prompt truncation logic
- Verify API connectivity (if keys are configured)
- Create configuration templates
- Demonstrate error handling

### 8. Monitoring and Debugging

#### Enable Detailed Logging:
```python
import logging
logging.basicConfig(level=logging.INFO)

# The handler will log:
# - Model attempts and failures
# - Prompt truncation events
# - Fallback activations
# - Error classifications
```

#### Check API Status:
```python
handler = LiteLLMErrorHandler()
print(f"LiteLLM available: {handler.litellm_available}")

# Test specific models
response = handler.call_with_fallback(
    "Test prompt",
    model="gpt-4o-mini"  # Try different models
)
```

## Prevention Strategies

### 1. Proactive Prompt Management:
- Estimate token counts before API calls
- Implement smart summarization for long inputs
- Use chunking for very large documents

### 2. Model Selection:
- Use high-capacity models (Claude, GPT-4) for long prompts
- Reserve smaller models for short, focused tasks
- Implement cost-aware model selection

### 3. Fallback Architecture:
- Always configure multiple providers
- Test fallback chains regularly
- Monitor API quotas and limits

## Cost Optimization

### Model Cost Comparison (approximate):
- **GPT-4o Mini**: $0.15/$0.60 per 1M tokens (input/output)
- **Claude 3 Haiku**: $0.25/$1.25 per 1M tokens
- **Claude 3.5 Sonnet**: $3.00/$15.00 per 1M tokens
- **GPT-3.5 Turbo**: $0.50/$1.50 per 1M tokens

### Optimization Tips:
1. Use GPT-4o Mini for most tasks (best value)
2. Reserve Claude 3.5 Sonnet for complex reasoning
3. Implement prompt caching for repeated queries
4. Monitor usage with LiteLLM's built-in tracking

## Troubleshooting

### Common Issues:

#### "All models failed":
- Check API keys in `.env` file
- Verify internet connectivity
- Check API quotas/billing

#### "LiteLLM not available":
```bash
pip install litellm==1.44.0
```

#### Vertex AI specific issues:
```bash
# Ensure Google Cloud SDK is configured
gcloud auth application-default login
export GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
```

#### Rate limiting:
- Implement exponential backoff
- Use multiple API keys
- Distribute load across providers

## Production Deployment

### 1. Environment Variables:
```bash
# Production .env
OPENAI_API_KEY=prod_key_here
ANTHROPIC_API_KEY=prod_key_here
LITELLM_LOG=WARNING  # Reduce log verbosity
```

### 2. Error Monitoring:
```python
# Add to your application
import sentry_sdk

def enhanced_error_tracking():
    try:
        response = handler.call_with_fallback(prompt)
        return response
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return fallback_response
```

### 3. Performance Monitoring:
```python
import time

start_time = time.time()
response = handler.call_with_fallback(prompt)
duration = time.time() - start_time

# Log performance metrics
logger.info(f"LLM call took {duration:.2f}s")
```

## Summary

This solution provides:
✅ **Robust error handling** for prompt length issues
✅ **Automatic fallback** across multiple providers  
✅ **Intelligent truncation** preserving content structure
✅ **Cost optimization** through smart model selection
✅ **Production-ready** monitoring and logging
✅ **Easy integration** with existing codebases

The error you encountered should no longer occur with this implementation, as it handles prompt length limits proactively and provides multiple fallback options.
