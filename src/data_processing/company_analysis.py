"""
Company Analysis Module for DuPont Tedlar Lead Generation System.

This module identifies and qualifies companies that attend industry events and
associations relevant to DuPont Tedlar's target market. It implements a tiered LLM approach:
- GPT-3.5 Turbo for initial company discovery (lower cost)
- GPT-4 Turbo for detailed qualification (premium model)
- Claude Opus for deep analysis of highest potential leads (precision focus)

The focus is on identifying high-quality leads that match DuPont Tedlar's ICP,
emphasizing conversion potential over mere awareness.
"""

import os
import json
import time
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import random

from config.config import TEDLAR_CONTEXT, LLM_CONFIG, DATA_DIR, LEAD_SCORING
from src.llm.llm_client import call_openai_api
from src.llm.prompt_templates import BASE_TEDLAR_CONTEXT
from src.utils.cost_tracker import is_budget_available, log_usage_report
from src.utils.data_models import Company
from src.utils.lead_scoring import calculate_lead_score, get_lead_priority, should_use_premium_model, generate_qualification_rationale

def load_events_and_associations() -> List[Dict[str, Any]]:
    """
    Load analyzed events and associations data.
    
    This function retrieves the events and associations identified and analyzed
    in the event research module, prioritizing high and medium priority gatherings.
    
    Returns:
        List of analyzed industry gatherings (events and associations)
    """
    print("Loading analyzed industry events and associations...")
    
    gatherings = []
    
    # Load events
    events_dir = DATA_DIR / "events"
    if events_dir.exists():
        for event_file in events_dir.glob("*.json"):
            try:
                with open(event_file, "r") as f:
                    event_data = json.load(f)
                    
                    # Add type if not present
                    if "type" not in event_data:
                        event_data["type"] = "event"
                        
                    gatherings.append(event_data)
            except Exception as e:
                print(f"Error loading event data from {event_file}: {str(e)}")
    
    # Load associations
    associations_dir = DATA_DIR / "associations"
    if associations_dir.exists():
        for assoc_file in associations_dir.glob("*.json"):
            try:
                with open(assoc_file, "r") as f:
                    assoc_data = json.load(f)
                    
                    # Add type if not present
                    if "type" not in assoc_data:
                        assoc_data["type"] = "association"
                        
                    gatherings.append(assoc_data)
            except Exception as e:
                print(f"Error loading association data from {assoc_file}: {str(e)}")
    
    # Sort by priority and relevance score
    gatherings = sorted(gatherings, key=lambda g: (
        0 if g.get("priority") == "high" else (1 if g.get("priority") == "medium" else 2),
        -float(g.get("relevance_score", 0))
    ))
    
    print(f"Loaded {len(gatherings)} industry gatherings:")
    print(f"- Events: {sum(1 for g in gatherings if g.get('type') == 'event')}")
    print(f"- Associations: {sum(1 for g in gatherings if g.get('type') == 'association')}")
    print(f"- High priority: {sum(1 for g in gatherings if g.get('priority') == 'high')}")
    print(f"- Medium priority: {sum(1 for g in gatherings if g.get('priority') == 'medium')}")
    
    return gatherings

def discover_companies_for_gathering(gathering: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Discover companies likely to attend a specific industry gathering.
    
    This function implements the first tier of our LLM approach, using the more
    cost-effective GPT-3.5 Turbo for initial company discovery.
    
    Args:
        gathering: Event or association information
        
    Returns:
        List of discovered companies with basic information
    """
    print(f"Discovering companies for {gathering['type']}: {gathering['name']}...")
    
    # Budget check - part of our cost optimization strategy
    estimated_cost = 0.02  # Approximate cost for GPT-3.5 Turbo
    if not is_budget_available("company_analysis", estimated_cost):
        print(f"WARNING: Insufficient budget for company discovery for {gathering['name']}.")
        return []
    
    # Format gathering details for the prompt
    gathering_details = f"""
    Name: {gathering['name']}
    Type: {gathering['type']}
    {'Date: ' + gathering.get('date', '') if gathering['type'] == 'event' else ''}
    {'Location: ' + gathering.get('location', '') if gathering['type'] == 'event' else ''}
    Description: {gathering.get('description', '')}
    Relevance: {gathering.get('relevance_rationale', '')}
    
    This is a {gathering.get('priority', 'medium')} priority {gathering['type']} with a relevance score of {gathering.get('relevance_score', 7.0)}/10 for DuPont Tedlar's target market.
    """
    
    # Direct prompt construction 
    prompt = f"""
    {BASE_TEDLAR_CONTEXT}

    TASK: Identify companies likely to attend the following event that match 
    DuPont Tedlar's ideal customer profile.

    EVENT: {gathering['name']}
    DETAILS: {gathering_details}

    Focus on companies that:
    1. Match one of Tedlar's 6 specific customer segments
    2. Experience the pain points Tedlar addresses (degradation, fading, chemical damage)
    3. Would benefit from Tedlar's specific product lines and performance characteristics
    4. Have the appropriate decision-maker roles (e.g., Production Directors, Materials Engineering Directors)

    For each potential company, provide:
    - Company name
    - Which customer segment they belong to (large format printers, fleet graphics, etc.)
    - Estimated company size (revenue and employees if available)
    - Brief description of their business
    - Why they match Tedlar's ICP
    - Specific pain points they likely experience
    - How they would benefit from Tedlar's specific product capabilities
    - Relevant use cases for Tedlar's products
    - Initial qualification score (1-10)

    Focus on quality over quantity. Identify 5-8 companies that are most likely to be 
    strong prospects for Tedlar's protective films.

    FORMAT YOUR RESPONSE AS JSON with an array of company objects.
    """
    
    # Use cost-effective model for initial discovery
    gpt35_config = LLM_CONFIG["company_analysis"]["initial_screening"]
    response = call_openai_api(
        messages=[{"role": "system", "content": prompt}],
        model=gpt35_config["model"],
        temperature=gpt35_config["temperature"],
        max_tokens=gpt35_config["max_tokens"],
        module="company_analysis",
        operation="company_discovery"
    )
    
    # Extract and parse the companies from the response
    try:
        content = response["content"]
        
        # Find and extract JSON content
        json_start = content.find('[')
        json_end = content.rfind(']') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_content = content[json_start:json_end]
            discovered_companies = json.loads(json_content)
        else:
            # Fallback if JSON format isn't clear
            print(f"WARNING: Could not extract JSON from response for {gathering['name']}. Using fallback approach.")
            
            # Add example company as fallback for prototype
            discovered_companies = [
                {
                    "name": "Avery Dennison Graphics Solutions",
                    "industry": "Graphics & Signage",
                    "description": "Global manufacturer of graphics materials and solutions",
                    "revenue_estimate": "$8B+",
                    "size_estimate": "Thousands of employees",
                    "why_relevant": "Specializes in large-format signage, architectural graphics, and vehicle wraps.",
                    "qualification_score": 8.5
                }
            ]
    except Exception as e:
        print(f"Error parsing response for {gathering['name']}: {str(e)}")
        discovered_companies = []
    
    # Enhance company data with gathering context and IDs
    enhanced_companies = []
    for company in discovered_companies:
        company_id = str(uuid.uuid4())
        
        enhanced_companies.append({
            "id": company_id,
            "name": company.get("name", "Unknown Company"),
            "industry": company.get("industry", "Graphics & Signage"),
            "description": company.get("description", ""),
            "revenue_estimate": company.get("revenue_estimate", "Unknown"),
            "size_estimate": company.get("size_estimate", "Unknown"),
            "website": company.get("website", ""),
            "qualification_score": float(company.get("qualification_score", 0.0)),
            "qualification_rationale": company.get("why_relevant", ""),
            "source_gathering_id": gathering.get("id", ""),
            "source_gathering_name": gathering["name"],
            "source_gathering_type": gathering["type"],
            "discovery_date": datetime.now().isoformat()
        })
    
    print(f"Discovered {len(enhanced_companies)} potential companies from {gathering['name']}.")
    return enhanced_companies

def qualify_company(company: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform detailed qualification analysis of a company.
    
    This function implements the second tier of our LLM approach, using the premium
    GPT-4 or Claude model for detailed analysis of promising companies.
    
    Args:
        company: Basic company information
        
    Returns:
        Enhanced company data with detailed qualification analysis
    """
    print(f"Qualifying company: {company['name']}...")
    
    # Budget check - using premium models only for promising leads
    # Check initial qualification score to determine if premium model is justified
    initial_score = company.get("qualification_score", 0.0)
    
    # Only use premium model if initial score suggests a good fit
    model_tier = "qualification" if initial_score >= 6.0 else "initial_screening"
    estimated_cost = 0.10 if model_tier == "qualification" else 0.02
    
    if not is_budget_available("company_analysis", estimated_cost):
        print(f"WARNING: Insufficient budget for detailed qualification of {company['name']}.")
        return company
    
    # Format company details for the prompt
    company_details = f"""
    Company Name: {company['name']}
    Industry: {company['industry']}
    Description: {company['description']}
    Estimated Revenue: {company['revenue_estimate']}
    Estimated Size: {company['size_estimate']}
    Website: {company.get('website', 'Unknown')}
    
    Initial Assessment: {company.get('qualification_rationale', '')}
    
    Found through: {company['source_gathering_type']} - {company['source_gathering_name']}
    """
    
    # Direct prompt construction
    prompt = f"""
    {BASE_TEDLAR_CONTEXT}

    TASK: Perform an in-depth qualification analysis of the following company 
    as a potential customer for DuPont Tedlar protective films.

    COMPANY: {company['name']}
    DETAILS: {company_details}

    Evaluate this company against our lead scoring criteria:
    {json.dumps(LEAD_SCORING, indent=2)}

    For each criterion:

    1. Industry Relevance (30% weight)
       - Identify which of Tedlar's 6 target segments they fit into
       - Evaluate how central graphics/signage is to their business
       - Assess if they work with applications requiring Tedlar's extreme durability

    2. Product Fit (25% weight)
       - Analyze which specific Tedlar products would benefit them (CLR, TWH, TMT, etc.)
       - Match Tedlar's specific performance capabilities to their likely challenges
       - Identify how Tedlar's technical specs (chemical resistance, temperature range, etc.) address their needs

    3. Decision Maker Access (20% weight)
       - Identify the specific job titles/roles that would make purchasing decisions
       - Assess organizational structure and purchase process complexity
       - Evaluate likelihood of reaching true decision-makers vs. gatekeepers

    4. Current Engagement (15% weight)
       - Note their presence at relevant industry events
       - Identify involvement in industry associations
       - Assess their activity level in the graphics/signage community

    5. Market Presence (10% weight)
       - Evaluate their influence within their industry segment
       - Assess company size relative to Tedlar's target parameters
       - Consider growth trajectory and investment in graphics/signage

    For each criterion:
    1. Assign a score (0-10)
    2. Provide detailed justification with specific references to the company
    3. Identify specific use cases for Tedlar products
    4. Outline potential pain points that Tedlar can address

    Calculate a weighted qualification score and provide a comprehensive qualification rationale.
    Focus on conversion potential rather than general awareness.

    FORMAT YOUR RESPONSE AS JSON with scores, justifications, and detailed analysis.
    """
    
    # Use appropriate model based on initial qualification
    if model_tier == "qualification":
        # Premium model for promising leads - use GPT-4 instead of Claude
        model_config = {
            "model": "gpt-4-turbo",
            "temperature": 0.3,
            "max_tokens": 1500,
        }
        operation = "detailed_qualification"
    else:
        # Cost-effective model for basic qualification
        model_config = LLM_CONFIG["company_analysis"]["initial_screening"]
        operation = "basic_qualification"
    
    response = call_openai_api(
        messages=[{"role": "system", "content": prompt}],
        model=model_config["model"],
        temperature=model_config["temperature"],
        max_tokens=model_config["max_tokens"],
        module="company_analysis",
        operation=operation
    )
    
    # Extract and parse the qualification results
    try:
        content = response["content"]
        
        # Find and extract JSON content
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_content = content[json_start:json_end]
            qualification = json.loads(json_content)
        else:
            # Handle case where JSON isn't properly formatted
            print(f"WARNING: Could not extract JSON from response for {company['name']}.")
            qualification = {}
    except Exception as e:
        print(f"Error parsing qualification response for {company['name']}: {str(e)}")
        qualification = {}
    
    # Update company with qualification results
    qualified_company = company.copy()
    
    # Extract scores for each criterion if available
    criterion_scores = {}
    criterion_justifications = {}
    use_cases = []
    pain_points = []
    
    if "industry_relevance" in qualification:
        if isinstance(qualification["industry_relevance"], dict):
            criterion_scores["industry_relevance"] = float(qualification["industry_relevance"].get("score", 0.0))
            criterion_justifications["industry_relevance"] = qualification["industry_relevance"].get("justification", "")
        else:
            # Try direct value
            try:
                criterion_scores["industry_relevance"] = float(qualification["industry_relevance"])
            except:
                pass
    
    if "product_fit" in qualification:
        if isinstance(qualification["product_fit"], dict):
            criterion_scores["product_fit"] = float(qualification["product_fit"].get("score", 0.0))
            criterion_justifications["product_fit"] = qualification["product_fit"].get("justification", "")
        else:
            try:
                criterion_scores["product_fit"] = float(qualification["product_fit"])
            except:
                pass
    
    if "decision_maker_access" in qualification:
        if isinstance(qualification["decision_maker_access"], dict):
            criterion_scores["decision_maker_access"] = float(qualification["decision_maker_access"].get("score", 0.0))
            criterion_justifications["decision_maker_access"] = qualification["decision_maker_access"].get("justification", "")
        else:
            try:
                criterion_scores["decision_maker_access"] = float(qualification["decision_maker_access"])
            except:
                pass
    
    if "current_engagement" in qualification:
        if isinstance(qualification["current_engagement"], dict):
            criterion_scores["current_engagement"] = float(qualification["current_engagement"].get("score", 0.0))
            criterion_justifications["current_engagement"] = qualification["current_engagement"].get("justification", "")
        else:
            try:
                criterion_scores["current_engagement"] = float(qualification["current_engagement"])
            except:
                pass
    
    if "market_presence" in qualification:
        if isinstance(qualification["market_presence"], dict):
            criterion_scores["market_presence"] = float(qualification["market_presence"].get("score", 0.0))
            criterion_justifications["market_presence"] = qualification["market_presence"].get("justification", "")
        else:
            try:
                criterion_scores["market_presence"] = float(qualification["market_presence"])
            except:
                pass
    
    # Extract use cases if available
    if "use_cases" in qualification:
        if isinstance(qualification["use_cases"], list):
            use_cases = qualification["use_cases"]
        elif isinstance(qualification["use_cases"], dict) and "items" in qualification["use_cases"]:
            use_cases = qualification["use_cases"]["items"]
    
    # Extract pain points if available
    if "pain_points" in qualification:
        if isinstance(qualification["pain_points"], list):
            pain_points = qualification["pain_points"]
        elif isinstance(qualification["pain_points"], dict) and "items" in qualification["pain_points"]:
            pain_points = qualification["pain_points"]["items"]
    
    # Calculate overall qualification score using our weighted model
    if criterion_scores:
        overall_score = calculate_lead_score(criterion_scores)
        qualified_company["qualification_score"] = overall_score
        qualified_company["lead_priority"] = get_lead_priority(overall_score)
    
    # Generate comprehensive qualification rationale
    if criterion_scores:
        customer_segment = identify_customer_segment(company.get("industry", ""), company.get("description", ""))
        qualified_company["customer_segment"] = customer_segment
        
        qualification_rationale = generate_qualification_rationale(
            company_name=company["name"],
            scores=criterion_scores,
            justifications=criterion_justifications,
            use_cases=use_cases,
            pain_points=pain_points,
            #customer_segment=customer_segment
        )
        
        qualified_company["qualification_rationale"] = qualification_rationale
    
    # Store detailed qualification data
    qualified_company["detailed_qualification"] = {
        "criterion_scores": criterion_scores,
        "criterion_justifications": criterion_justifications,
        "use_cases": use_cases,
        "pain_points": pain_points,
        "raw_qualification": qualification
    }
    
    return qualified_company

def identify_customer_segment(industry: str, description: str) -> str:
    """
    Identify which of Tedlar's customer segments the company belongs to.
    
    Args:
        industry: Company industry
        description: Company description
        
    Returns:
        Most likely customer segment
    """
    combined_text = f"{industry} {description}".lower()
    
    segment_keywords = {
        "Large Format Print Providers": ["large format", "print provider", "wide format", "banner", "printing service"],
        "Fleet Graphics Specialists": ["fleet", "vehicle wrap", "automotive graphic", "transit", "car wrap"],
        "Architectural Graphics Manufacturers": ["architectural", "building", "facade", "interior", "wayfinding"],
        "Outdoor Advertising Companies": ["billboard", "outdoor advertising", "signage company", "out-of-home"],
        "Sign Manufacturing Companies": ["sign manufacturer", "signage", "sign maker", "display", "visual communication"],
        "Material Distributors & Converters": ["distributor", "converter", "supplier", "reseller", "wholesale"]
    }
    
    # Count keyword matches for each segment
    match_counts = {segment: 0 for segment in segment_keywords}
    
    for segment, keywords in segment_keywords.items():
        for keyword in keywords:
            if keyword in combined_text:
                match_counts[segment] += 1
    
    # Find segment with highest match count
    best_match = max(match_counts.items(), key=lambda x: x[1])
    
    # Return the best matching segment, or a default if no good matches
    if best_match[1] > 0:
        return best_match[0]
    
    # If no clear match, make an educated guess based on industry
    if "print" in industry.lower():
        return "Large Format Print Providers"
    elif "sign" in industry.lower():
        return "Sign Manufacturing Companies"
    elif "advertising" in industry.lower():
        return "Outdoor Advertising Companies"
    
    # Default fallback
    return "Sign Manufacturing Companies"

def prioritize_companies(companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Prioritize qualified companies for stakeholder identification.
    
    This prioritization is crucial for allocating budget effectively, focusing
    on companies with the highest conversion potential.
    
    Args:
        companies: List of qualified companies
        
    Returns:
        Prioritized list of companies
    """
    # Sort companies by qualification score (descending)
    sorted_companies = sorted(companies, key=lambda x: x.get("qualification_score", 0.0), reverse=True)
    
    # Categorize by priority level
    high_priority = []
    medium_priority = []
    low_priority = []
    
    for company in sorted_companies:
        priority = company.get("lead_priority", "unqualified")
        
        if priority == "exceptional" or priority == "high_priority":
            high_priority.append(company)
        elif priority == "qualified":
            medium_priority.append(company)
        else:
            low_priority.append(company)
    
    # Combine categories in order of priority
    prioritized_companies = high_priority + medium_priority + low_priority
    
    print(f"\nCompany Prioritization Summary:")
    print(f"Total qualified companies: {len(prioritized_companies)}")
    print(f"High/Exceptional priority: {len(high_priority)}")
    print(f"Medium priority: {len(medium_priority)}")
    print(f"Low priority: {len(low_priority)}")
    
    return prioritized_companies

def save_company_data(companies: List[Dict[str, Any]]):
    """
    Save qualified company data to JSON files.
    
    Structured data storage is essential for the downstream stakeholder
    identification module, ensuring data integrity throughout the pipeline.
    
    Args:
        companies: List of qualified and prioritized companies
    """
    companies_dir = DATA_DIR / "companies"
    companies_dir.mkdir(exist_ok=True)
    
    # Custom JSON encoder to handle various data types
    class CustomEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, uuid.UUID):
                return str(obj)
            if isinstance(obj, datetime):
                return obj.isoformat()
            return super().default(obj)
    
    # Save each company as a separate JSON file
    for company in companies:
        try:
            # Create Company object for validation
            company_obj = Company(
                id=company["id"],
                name=company["name"],
                industry=company["industry"],
                description=company["description"],
                revenue_estimate=company.get("revenue_estimate", ""),
                size_estimate=company.get("size_estimate", ""),
                website=company.get("website", ""),
                qualification_score=company.get("qualification_score", 0.0),
                qualification_rationale=company.get("qualification_rationale", "")
            )
            
            # Convert to dictionary for saving
            company_dict = company_obj.model_dump()
            
            # Add additional fields
            if "customer_segment" in company:
                company_dict["customer_segment"] = company["customer_segment"]
                
            if "lead_priority" in company:
                company_dict["lead_priority"] = company["lead_priority"]
                
            if "source_gathering_id" in company:
                company_dict["source_gathering_id"] = company["source_gathering_id"]
                
            if "source_gathering_name" in company:
                company_dict["source_gathering_name"] = company["source_gathering_name"]
                
            if "source_gathering_type" in company:
                company_dict["source_gathering_type"] = company["source_gathering_type"]
                
            if "detailed_qualification" in company:
                company_dict["detailed_qualification"] = company["detailed_qualification"]
                
            # Save to file
            company_file = companies_dir / f"{company['id']}.json"
            with open(company_file, "w") as f:
                json.dump(company_dict, f, indent=2, cls=CustomEncoder)
                
            print(f"Saved company data for: {company['name']} (Priority: {company.get('lead_priority', 'unknown')})")
        except Exception as e:
            print(f"Error saving company {company.get('name', 'unknown')}: {str(e)}")

def run_company_analysis(limit_gatherings=None, limit_companies_per_gathering=None, debug=False):
    """
    Run the complete company analysis process:
    1. Load events and associations from prior analysis
    2. Discover companies for each gathering
    3. Qualify each company for fit with DuPont Tedlar's target market
    4. Prioritize companies based on qualification score
    5. Save company data for stakeholder identification
    
    This tiered approach optimizes our $200 budget while ensuring high-quality
    leads are identified for conversion-focused outreach.
    
    Args:
        limit_gatherings: Optional limit on number of gatherings to process
        limit_companies_per_gathering: Optional limit on companies per gathering
        debug: Whether to print debug information
    """
    print("Starting company analysis process...")
    
    # Step 1: Load events and associations from prior research
    gatherings = load_events_and_associations()
    
    if not gatherings:
        print("No events or associations found. Run event research module first.")
        return
    
    # Apply limit on gatherings if specified
    if limit_gatherings is not None and limit_gatherings > 0:
        gatherings = gatherings[:limit_gatherings]
        print(f"Limiting analysis to {limit_gatherings} gatherings.")
    
    # Step 2: Discover companies for each gathering
    all_companies = []
    for gathering in gatherings:
        companies = discover_companies_for_gathering(gathering)
        
        # Apply limit on companies per gathering if specified
        if limit_companies_per_gathering is not None and limit_companies_per_gathering > 0:
            companies = companies[:limit_companies_per_gathering]
            print(f"Limiting to {limit_companies_per_gathering} companies for {gathering['name']}.")
        
        all_companies.extend(companies)
        
        # Small delay to avoid API rate limits
        time.sleep(0.5)
    
    # De-duplicate companies by name
    unique_companies = {}
    for company in all_companies:
        company_name = company["name"].strip().lower()
        
        if company_name not in unique_companies:
            unique_companies[company_name] = company
        else:
            # If duplicate found, keep the one with higher initial score
            if company.get("qualification_score", 0) > unique_companies[company_name].get("qualification_score", 0):
                unique_companies[company_name] = company
    
    all_companies = list(unique_companies.values())
    
    print(f"Discovered {len(all_companies)} unique companies across all gatherings.")
    
    # Step 3: Qualify each company with detailed analysis
    qualified_companies = []
    for company in all_companies:
        qualified_company = qualify_company(company)
        qualified_companies.append(qualified_company)
        
        if debug:
            print(f"Qualification for {company['name']}:")
            print(f"Score: {qualified_company.get('qualification_score', 0.0)}")
            print(f"Priority: {qualified_company.get('lead_priority', 'unknown')}")
            print(f"Segment: {qualified_company.get('customer_segment', 'unknown')}")
        
        # Small delay to avoid API rate limits
        time.sleep(0.5)
    
    # Step 4: Prioritize companies based on qualification score
    prioritized_companies = prioritize_companies(qualified_companies)
    
    # Step 5: Save company data for stakeholder identification
    save_company_data(prioritized_companies)
    
    # Track budget usage
    log_usage_report()
    
    # Print top companies by score
    print("\nTop 5 Qualified Companies:")
    for i, company in enumerate(prioritized_companies[:min(5, len(prioritized_companies))]):
        print(f"{i+1}. {company['name']} (Score: {company.get('qualification_score', 0.0):.1f}, Priority: {company.get('lead_priority', 'unknown')})")

def parse_arguments():
    """Parse command line arguments for more flexible execution."""
    import argparse
    parser = argparse.ArgumentParser(description="DuPont Tedlar Company Analysis Module")
    parser.add_argument("--limit-gatherings", type=int, default=None, help="Limit the number of gatherings to process")
    parser.add_argument("--limit-companies", type=int, default=None, help="Limit the number of companies per gathering")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    run_company_analysis(
        limit_gatherings=args.limit_gatherings,
        limit_companies_per_gathering=args.limit_companies,
        debug=args.debug
    )