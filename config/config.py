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
# Enhanced with detailed Perplexity research
TEDLAR_CONTEXT = {
    "product_name": "DuPont Tedlar protective films",
    "product_description": "Premium polyvinyl fluoride (PVF) protective films with over 60 years of technology development, specifically engineered to extend the life of graphics applications in challenging environments.",
    "product_specifications": {
        "composition": "Proprietary polyvinyl fluoride (PVF) technology",
        "thicknesses": "1.0 mil (25μm) to 2.0 mil (50μm)",
        "standard_widths": "48\" to 60\" (custom widths available)",
        "surface_finishes": ["Clear", "Matte", "Custom textures"],
        "temperature_range": "-70°F to 302°F (-57°C to 150°C)",
        "uv_protection": "Blocks >99% of damaging UV radiation"
    },
    "product_lines": [
        {"name": "Tedlar CLR", "description": "Clear protective overlaminates for maximum color clarity"},
        {"name": "Tedlar TWH", "description": "White films for backlit signage applications"},
        {"name": "Tedlar TMT", "description": "Matte finish films for glare reduction"},
        {"name": "Tedlar TCW", "description": "Customizable width films for large format applications"},
        {"name": "Tedlar TAW", "description": "Architectural grade films for building graphics"}
    ],
    "key_benefits": [
        "Extended graphic life (5-7 years longer than standard laminates)",
        "Superior color retention (<3 Delta E color shift after 10 years)",
        "Exceptional chemical resistance (resistant to 300+ chemicals)",
        "Graffiti resistance with easy cleaning",
        "Anti-delamination technology preventing edge lifting",
        "Weather resistance tested for 10+ years outdoor exposure",
        "Reduced maintenance and cleaning frequency"
    ],
    "target_customer_segments": [
        {
            "segment": "Large Format Print Providers",
            "size_revenue": "$5M-$50M annual revenue",
            "size_employees": "50-250 employees",
            "geographic_scope": "National or multinational operations",
            "pain_points": ["Premature graphic failure", "Warranty claims", "Color fading"],
            "decision_makers": ["Operations Directors", "Production Managers", "R&D Directors"]
        },
        {
            "segment": "Fleet Graphics Specialists",
            "size_revenue": "$2M-$20M annual revenue",
            "size_employees": "25-100 employees",
            "pain_points": ["Graphics degradation in harsh transit conditions", "Fleet downtime"],
            "decision_makers": ["Fleet Graphics Directors", "Product Development Managers"]
        },
        {
            "segment": "Architectural Graphics Manufacturers",
            "size_revenue": "$10M-$100M annual revenue",
            "size_employees": "100-500 employees",
            "pain_points": ["Extended warranties", "Installation complexity", "Material longevity"],
            "decision_makers": ["VP of Product Development", "Materials Engineering Directors"]
        },
        {
            "segment": "Outdoor Advertising Companies",
            "size_revenue": "$20M-$500M annual revenue",
            "size_employees": "100-1,000 employees",
            "pain_points": ["Weather damage", "Maintenance costs", "Extended installation lifespans"],
            "decision_makers": ["Production Directors", "Materials Procurement Managers"]
        },
        {
            "segment": "Sign Manufacturing Companies",
            "size_revenue": "$1M-$25M annual revenue",
            "size_employees": "20-150 employees",
            "pain_points": ["UV degradation", "Color consistency", "Delamination"],
            "decision_makers": ["Production Managers", "Technical Directors"]
        },
        {
            "segment": "Material Distributors & Converters",
            "size_revenue": "$10M-$200M annual revenue",
            "size_employees": "50-300 employees",
            "pain_points": ["Product differentiation", "Competitive advantages", "Specialized applications"],
            "decision_makers": ["Product Line Managers", "Business Development Directors"]
        }
    ],
    "use_cases": [
        {
            "category": "Transit & Fleet Graphics",
            "applications": [
                "Bus wraps requiring 5-7 year durability",
                "Fleet vehicle graphics with reduced replacement cycles",
                "Rail car exterior graphics exposed to extreme conditions"
            ]
        },
        {
            "category": "Architectural Applications",
            "applications": [
                "Building facade graphics with 10+ year warranties",
                "Interior wayfinding with chemical cleaning resistance",
                "Corporate identity signage with consistent appearance"
            ]
        },
        {
            "category": "Outdoor Signage",
            "applications": [
                "Highway billboards with minimal maintenance",
                "Stadium and arena signage with weather resistance",
                "Retail exterior signage with enhanced color retention"
            ]
        },
        {
            "category": "Specialty Applications",
            "applications": [
                "Marine graphics with salt water resistance",
                "Airport signage with jet fuel vapor resistance",
                "Industrial signage in chemical processing environments"
            ]
        }
    ],
    "competitive_positioning": {
        "primary_competitors": ["3M Scotchcal", "Avery Dennison MPI", "ORAFOL Oraguard"],
        "performance_advantages": [
            "30-50% longer life in accelerated weathering tests",
            "Superior UV resistance with proprietary inhibitors",
            "Chemical resistance to 300+ substances",
            "Less than 0.2% shrinkage compared to 0.5-1.5% for competitors"
        ],
        "pricing": "Premium positioned at 15-30% above standard protective films",
        "total_cost_of_ownership": "Despite 15-20% premium pricing, delivers 30-40% lower lifetime costs"
    },
    "key_industry_events_2024": [
        {
            "name": "ISA International Sign Expo 2024",
            "date": "April 10-12, 2024",
            "location": "Orlando, FL",
            "attendees": "20,000+ professionals",
            "relevance": "Premier event for sign, graphics, and visual communications industry"
        },
        {
            "name": "PRINTING United Expo 2024",
            "date": "September 10-12, 2024",
            "location": "Las Vegas, NV",
            "attendees": "18,000+ professionals",
            "relevance": "Comprehensive printing industry event spanning all markets and technologies"
        },
        {
            "name": "FESPA Global Print Expo 2024",
            "date": "May 21-24, 2024",
            "location": "Amsterdam, Netherlands",
            "attendees": "15,000+ international visitors",
            "relevance": "International exhibition for screen, digital, and textile printing"
        },
        {
            "name": "Graphics Pro Expo 2024",
            "date": "Various (6 regional events throughout 2024)",
            "location": "Multiple US cities",
            "attendees": "2,000-3,500 per regional event",
            "relevance": "Regional focus with education and product showcase for graphics professionals"
        }
    ],
    "key_industry_associations": [
        {
            "name": "International Sign Association (ISA)",
            "members": "2,300+ sign and graphics companies",
            "relevance": "Primary trade association for sign industry professionals"
        },
        {
            "name": "PRINTING United Alliance",
            "members": "7,000+ companies across printing technologies",
            "relevance": "Created from merger of SGIA and PIA, representing broad printing industry"
        },
        {
            "name": "Society for Experiential Graphic Design (SEGD)",
            "members": "2,000+ professionals across multiple disciplines",
            "relevance": "Focus on architectural, wayfinding, and experiential graphics"
        },
        {
            "name": "FESPA",
            "members": "37 national associations and thousands of company members",
            "relevance": "Global federation with strong European presence"
        },
        {
            "name": "Specialty Graphic Imaging Association (SGIA)",
            "members": "Now part of PRINTING United Alliance",
            "relevance": "Historical focus on specialty graphics, including screen printing"
        },
        {
            "name": "National Association of Sign Supply Distributors (NASSD)",
            "members": "Leading distributors of sign supplies and materials",
            "relevance": "Key channel partners for material distribution"
        }
    ]
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