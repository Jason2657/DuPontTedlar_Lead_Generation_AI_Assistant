"""
Configuration settings for the DuPont Tedlar Lead Generation System.

This file centralizes all configuration parameters, API keys, and constants
used throughout the application to support a quality-focused lead generation process.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Create required directories if they don't exist
for dir_path in [
    DATA_DIR,
    DATA_DIR / "events",
    DATA_DIR / "companies", 
    DATA_DIR / "stakeholders",
    DATA_DIR / "outreach",
    DATA_DIR / "usage_reports"
]:
    dir_path.mkdir(exist_ok=True)

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

# LLM configuration for each stage of the pipeline
# Using a tiered approach: 
# - Lower cost models for initial broad discovery
# - Mid-tier models for qualification screening
# - Premium models for deep analysis of top prospects
LLM_CONFIG = {
    "event_research": {
        "initial_discovery": {
            "provider": "perplexity",  # Real-time data is crucial for events
            "temperature": 0.1,  # Low temperature for factual responses
            "max_tokens": 2000,
        },
        "relevance_analysis": {
            "provider": "openai", 
            "model": "gpt-4-turbo",  # High reasoning capabilities needed
            "temperature": 0.3,      # Allow some creativity in analysis
            "max_tokens": 1000,
        }
    },
    "company_analysis": {
        "initial_screening": {
            "provider": "openai",
            "model": "gpt-3.5-turbo",  # Cost-effective for initial screening
            "temperature": 0.2,
            "max_tokens": 800,
        },
        "qualification": {
            "provider": "anthropic",  
            "model": "claude-3-opus",  # Superior reasoning for qualification logic
            "temperature": 0.3,
            "max_tokens": 1500,
        },
    },
    "stakeholder_identification": {
        "provider": "openai",
        "model": "gpt-4-turbo",  # Strong organizational understanding
        "temperature": 0.4,      # Some creativity for role inference
        "max_tokens": 1200,
    },
    "outreach_generation": {
        "provider": "anthropic",
        "model": "claude-3-opus",  # Superior personalization capabilities
        "temperature": 0.7,       # Creative but professional messaging
        "max_tokens": 1000,
    }
}

# Token pricing for budget tracking (USD per 1K tokens)
TOKEN_PRICING = {
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "perplexity": {"request": 0.01}  # Per request estimate
}

# Budget allocation strategy (percentage of $200 total)
BUDGET_ALLOCATION = {
    "event_research": 0.10,      # 10% - $20
    "company_analysis": 0.25,    # 25% - $50 
    "stakeholder_identification": 0.15,  # 15% - $30
    "outreach_generation": 0.30, # 30% - $60
    "buffer": 0.20               # 20% - $40 for additional iterations
}

# DuPont Tedlar product and ICP information
# This context is crucial for generating relevant leads
TEDLAR_CONTEXT = {
    "product_name": "DuPont Tedlar protective films",
    "product_description": "High-performance protective films that provide exceptional durability, UV protection, and weather resistance for graphics, signage, and architectural applications.",
    "key_benefits": [
        "Superior protection against UV degradation",
        "Excellent chemical resistance",
        "Extended graphic and color life",
        "Protection against environmental damage",
        "Enhanced durability in outdoor applications"
    ],
    "target_industries": [
        "Graphics & Signage", 
        "Large format printing",
        "Architectural graphics",
        "Vehicle wraps",
        "Outdoor advertising"
    ],
    "ideal_customer_profile": {
        "company_types": [
            "Graphics manufacturers",
            "Signage producers",
            "Printing companies",
            "Architectural film suppliers",
            "Graphics media suppliers"
        ],
        "company_size": "Mid to large enterprises with significant production volume",
        "pain_points": [
            "Premature graphic fading in outdoor applications", 
            "Chemical damage to graphics in harsh environments",
            "Need for extended durability of printed materials",
            "Warranty claims due to product failure"
        ],
        "example_customer": "Avery Dennison Graphics Solutions"
    }
}

# Lead scoring system
# This system prioritizes conversion potential over awareness
LEAD_SCORING = {
    "criteria": {
        "industry_relevance": {
            "weight": 0.30,
            "description": "How closely the company aligns with Tedlar's target industries"
        },
        "product_fit": {
            "weight": 0.25,
            "description": "How well Tedlar's benefits address the company's specific needs"
        },
        "decision_maker_access": {
            "weight": 0.20,
            "description": "Likelihood of reaching actual decision-makers"
        },
        "current_engagement": {
            "weight": 0.15,
            "description": "Level of activity in relevant industry events"
        },
        "market_presence": {
            "weight": 0.10,
            "description": "Company's influence and size in their market"
        }
    },
    "thresholds": {
        "minimum_qualification": 6.0,  # Minimum score to be considered a qualified lead
        "high_priority": 8.0,          # Threshold for deep analysis and premium LLM usage
        "exceptional": 9.0             # Top prospects deserving multiple outreach iterations
    }
}