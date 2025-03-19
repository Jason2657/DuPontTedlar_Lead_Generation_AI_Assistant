"""
LLM Client Utilities for DuPont Tedlar Lead Generation System.

This module provides interfaces to different LLM providers using a tiered approach:
- Lower cost models for initial broad discovery
- Mid-tier models for qualification screening
- Premium models for deep analysis of top prospects
"""

import os
import json
import time
import requests
from typing import Dict, Any, List, Optional
import openai
from datetime import datetime
from config.config import OPENAI_API_KEY, PERPLEXITY_API_KEY, TOKEN_PRICING, DATA_DIR
from pathlib import Path

# Initialize API clients
openai.api_key = OPENAI_API_KEY

# Path for token usage logging
#from config.config import DATA_DIR
TOKEN_USAGE_FILE = DATA_DIR / "token_usage.json"

def log_token_usage(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    module: str,
    operation: str
) -> Dict[str, Any]:
    """
    Log token usage and associated costs for budget tracking.
    
    This function is critical for ensuring we stay within our $200 budget while
    prioritizing tokens for high-value operations like qualification and outreach.
    """
    # Calculate costs based on model
    if "gpt-" in model:
        model_pricing = TOKEN_PRICING.get(model, TOKEN_PRICING["gpt-4-turbo"])
        input_cost = (prompt_tokens / 1000) * model_pricing["input"]
        output_cost = (completion_tokens / 1000) * model_pricing["output"]
        total_cost = input_cost + output_cost
    elif "claude" in model:
        model_pricing = TOKEN_PRICING.get(model, TOKEN_PRICING["claude-3-opus"])
        input_cost = (prompt_tokens / 1000) * model_pricing["input"]
        output_cost = (completion_tokens / 1000) * model_pricing["output"]
        total_cost = input_cost + output_cost
    elif "perplexity" in model:
        # Perplexity has per-request pricing
        total_cost = TOKEN_PRICING["perplexity"]["request"]
        input_cost = 0
        output_cost = 0
    else:
        # Default fallback for unknown models
        total_cost = 0
        input_cost = 0
        output_cost = 0
    
    # Create usage record
    usage_record = {
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "input_cost_usd": input_cost,
        "output_cost_usd": output_cost,
        "total_cost_usd": total_cost,
        "module": module,
        "operation": operation,
        "timestamp": datetime.now().isoformat()
    }
    
    # Append to usage file
    with open(TOKEN_USAGE_FILE, "a") as f:
        f.write(json.dumps(usage_record) + "\n")
    
    return usage_record

def call_openai_api(
    messages: List[Dict[str, str]],
    model: str = "gpt-4-turbo",
    temperature: float = 0.7,
    max_tokens: int = 1000,
    module: str = "general",
    operation: str = "general"
) -> Dict[str, Any]:
    """
    Call OpenAI API with error handling and token tracking.
    Updated to use OpenAI API v1.0.0+
    """
    max_retries = 3
    retry_delay = 2
    
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    for attempt in range(max_retries):
        try:
            # Make API call using new format
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Process usage for token tracking
            usage_data = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            # Log token usage
            usage = log_token_usage(
                model=model,
                prompt_tokens=usage_data["prompt_tokens"],
                completion_tokens=usage_data["completion_tokens"],
                module=module,
                operation=operation
            )
            
            return {
                "content": response.choices[0].message.content,
                "usage": usage
            }
        
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Error calling OpenAI API: {str(e)}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print(f"Failed to call OpenAI API after {max_retries} attempts: {str(e)}")
                # Return fallback response
                return {
                    "content": f"Error: {str(e)}",
                    "usage": log_token_usage(
                        model=model,
                        prompt_tokens=0,
                        completion_tokens=0,
                        module=module,
                        operation=f"error_{operation}"
                    )
                }

def call_claude_api(
    messages: List[Dict[str, str]],
    model: str = "claude-3-opus",
    temperature: float = 0.7,
    max_tokens: int = 1000,
    module: str = "general",
    operation: str = "general"
) -> Dict[str, Any]:
    """
    Call Anthropic's Claude API with error handling and token tracking.
    
    Claude is used for high-quality reasoning tasks like lead qualification
    and personalized outreach generation, where its strengths align with 
    DuPont Tedlar's focus on quality over quantity.
    """
    # Note: Implementation depends on Anthropic's API client
    # This is a placeholder that would be replaced with actual implementation
    # For the prototype, you can use OpenAI's API as a stand-in
    
    # Placeholder response for demonstration
    placeholder_response = {
        "content": "This is a placeholder for Claude API response",
        "usage": log_token_usage(
            model=model,
            prompt_tokens=500,  # Estimated
            completion_tokens=300,  # Estimated
            module=module,
            operation=operation
        )
    }
    
    return placeholder_response

def query_perplexity(
    query: str,
    module: str = "event_research",
    operation: str = "initial_discovery"
) -> Dict[str, Any]:
    """
    Query Perplexity API for real-time information.
    
    Used primarily for event research where recent data is critical for
    identifying relevant industry gatherings for DuPont Tedlar's target market.
    """
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "query": query,
        "source_priority": "recent"  # Focus on recent information for events
    }
    
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "https://api.perplexity.ai/search",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Log token usage (estimated for Perplexity)
                usage = log_token_usage(
                    model="perplexity",
                    prompt_tokens=len(query.split()),  # Rough estimation
                    completion_tokens=len(str(result).split()),  # Rough estimation
                    module=module,
                    operation=operation
                )
                
                return {
                    "content": result,
                    "usage": usage
                }
            else:
                raise Exception(f"Perplexity API returned status code {response.status_code}: {response.text}")
        
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Error calling Perplexity API: {str(e)}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                print(f"Failed to query Perplexity API after {max_retries} attempts: {str(e)}")
                # Return fallback response
                return {
                    "content": f"Error: {str(e)}",
                    "usage": log_token_usage(
                        model="perplexity",
                        prompt_tokens=len(query.split()),  # Rough estimation
                        completion_tokens=0,
                        module=module,
                        operation=f"error_{operation}"
                    )
                }