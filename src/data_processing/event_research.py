"""
Event & Association Research Module for DuPont Tedlar Lead Generation System.

This module identifies and analyzes industry events, trade associations, and
professional bodies relevant to DuPont Tedlar's target market using a tiered LLM approach:
- Perplexity for real-time discovery (lower cost)
- GPT-4 Turbo for detailed relevance analysis (premium model)

The focus is on identifying all industry gatherings where DuPont Tedlar's specific
customer segments are likely to attend, prioritizing those with the highest
concentration of qualified leads.
"""

import os
import json
import time
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from config.config import TEDLAR_CONTEXT, LLM_CONFIG, DATA_DIR
from src.llm.llm_client import query_perplexity, call_openai_api
from src.llm.prompt_templates import EVENT_DISCOVERY_PROMPT, EVENT_QUALIFICATION_PROMPT, customize_prompt
from src.utils.cost_tracker import is_budget_available, log_usage_report
from src.utils.data_models import Event

def discover_industry_gatherings() -> List[Dict[str, Any]]:
    """
    Discover relevant industry events, trade associations, and professional bodies
    using Perplexity for real-time data.
    
    This function implements the first tier of our LLM approach, using the more
    cost-effective Perplexity API to gather current information about industry
    gatherings relevant to Tedlar's target segments.
    
    Returns:
        List of discovered events and associations with basic information
    """
    print("Discovering industry events, associations, and professional bodies using Perplexity...")
    
    # Update the prompt to explicitly include trade associations and industry bodies
    enhanced_prompt = EVENT_DISCOVERY_PROMPT.replace(
        "TASK: Identify the most relevant upcoming industry events",
        "TASK: Identify the most relevant industry events, trade associations, and professional bodies"
    )
    
    enhanced_prompt += "\n\nInclude BOTH time-limited events AND ongoing associations/organizations where Tedlar's target customers participate."
    
    # Budget check - part of our cost optimization strategy
    estimated_cost = 0.02  # Approximate cost for Perplexity request
    if not is_budget_available("event_research", estimated_cost):
        print("WARNING: Insufficient budget for discovery. Using pre-researched gatherings only.")
        return []
    
    # Query Perplexity with our specialized prompt
    perplexity_response = query_perplexity(
        enhanced_prompt,
        module="event_research",
        operation="initial_discovery"
    )
    
    # Extract and parse the JSON from the response
    try:
        # Handle different possible response formats from Perplexity
        if isinstance(perplexity_response["content"], dict) and "answer" in perplexity_response["content"]:
            response_text = perplexity_response["content"]["answer"]
        else:
            response_text = str(perplexity_response["content"])
        
        # Find JSON content within the response
        json_start = response_text.find('[')
        json_end = response_text.rfind(']') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_content = response_text[json_start:json_end]
            discovered_gatherings = json.loads(json_content)
        else:
            # Handle case where JSON isn't properly formatted in the response
            print("WARNING: Could not extract JSON from Perplexity response.")
            print("Raw response:", response_text[:500] + "..." if len(response_text) > 500 else response_text)
            discovered_gatherings = []
    except Exception as e:
        print(f"Error parsing Perplexity response: {str(e)}")
        discovered_gatherings = []
    
    # Include pre-researched events and associations
    all_gatherings = []
    
    # Add pre-researched events
    pre_researched_events = TEDLAR_CONTEXT.get("key_industry_events_2024", [])
    for event in pre_researched_events:
        all_gatherings.append({
            "name": event["name"],
            "type": "event",  # Classify as an event
            "date": event["date"],
            "location": event["location"],
            "description": event["relevance"],
            "website": "",
            "relevance_score": 9.0,  # Pre-vetted as highly relevant
            "relevance_rationale": f"Major industry event with {event['attendees']} focused on {event['relevance']}",
            "source": "Pre-researched data"
        })
    
    # Add pre-researched associations
    pre_researched_associations = TEDLAR_CONTEXT.get("key_industry_associations", [])
    for association in pre_researched_associations:
        all_gatherings.append({
            "name": association["name"],
            "type": "association",  # Classify as an association
            "date": "Ongoing",  # Associations are ongoing
            "location": "Various",
            "description": association["relevance"],
            "website": "",
            "relevance_score": 8.5,  # Pre-vetted as highly relevant
            "relevance_rationale": f"Major industry association with {association['members']} focused on {association['relevance']}",
            "source": "Pre-researched data"
        })
    
    # Add newly discovered gatherings from Perplexity
    for gathering in discovered_gatherings:
        # Skip duplicates
        if any(g["name"] == gathering["name"] for g in all_gatherings):
            continue
            
        # Determine if this is an event or association
        gathering_type = gathering.get("type", "").lower()
        if not gathering_type:
            if any(kw in gathering.get("name", "").lower() for kw in ["association", "organization", "society", "institute", "federation", "alliance"]):
                gathering_type = "association"
            else:
                gathering_type = "event"
                
        all_gatherings.append({
            "name": gathering.get("name", "Unknown"),
            "type": gathering_type,
            "date": gathering.get("date", "Ongoing" if gathering_type == "association" else ""),
            "location": gathering.get("location", "Various" if gathering_type == "association" else ""),
            "description": gathering.get("description", ""),
            "website": gathering.get("website", ""),
            "relevance_score": float(gathering.get("relevance_score", 0)),
            "relevance_rationale": gathering.get("why_relevant", ""),
            "source": "Perplexity discovery"
        })
    
    print(f"Discovered {len(all_gatherings)} industry gatherings:")
    print(f"- Events: {sum(1 for g in all_gatherings if g.get('type') == 'event')}")
    print(f"- Associations/Organizations: {sum(1 for g in all_gatherings if g.get('type') == 'association')}")
    return all_gatherings

def analyze_gathering_relevance(gathering: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze relevance of an industry event or association to DuPont Tedlar's target market.
    
    This function implements the second tier of our LLM approach, using the premium
    GPT-4 Turbo model for detailed analysis to ensure high-quality lead generation
    opportunities are identified.
    
    Args:
        gathering: Basic information about the event or association
        
    Returns:
        Enhanced data with detailed relevance analysis
    """
    print(f"Analyzing relevance of {gathering['type']}: {gathering['name']}...")
    
    # Budget optimization - using premium models only when justified
    estimated_cost = 0.06  # Approximate cost for GPT-4 Turbo analysis
    if not is_budget_available("event_research", estimated_cost):
        print(f"WARNING: Insufficient budget for detailed analysis of {gathering['name']}.")
        return gathering
    
    # Format details for the prompt
    gathering_details = f"""
    Name: {gathering['name']}
    Type: {gathering['type'].title()} {'(one-time event)' if gathering['type'] == 'event' else '(ongoing association/organization)'}
    {'Date: ' + gathering['date'] if gathering['type'] == 'event' else ''}
    {'Location: ' + gathering['location'] if gathering['type'] == 'event' else ''}
    Description: {gathering['description']}
    Website: {gathering['website']}
    Source: {gathering['source']}
    Initial Relevance Assessment: {gathering['relevance_rationale']}
    """
    
    # Adjust qualification prompt based on whether this is an event or association
    if gathering['type'] == 'association':
        qualification_prompt = EVENT_QUALIFICATION_PROMPT.replace(
            "Evaluate this event on the following criteria:",
            "Evaluate this industry association/organization on the following criteria:"
        )
    else:
        qualification_prompt = EVENT_QUALIFICATION_PROMPT
    
    # Customize the prompt with gathering details
    prompt = customize_prompt(qualification_prompt, event_details=gathering_details)
    
    # Premium model analysis - justified for this high-value qualification task
    gpt4_config = LLM_CONFIG["event_research"]["relevance_analysis"]
    response = call_openai_api(
        messages=[{"role": "system", "content": prompt}],
        model=gpt4_config["model"],
        temperature=gpt4_config["temperature"],
        max_tokens=gpt4_config["max_tokens"],
        module="event_research",
        operation="relevance_analysis"
    )
    
    # Extract and parse the analysis results
    try:
        content = response["content"]
        
        # Find and extract JSON content
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_content = content[json_start:json_end]
            analysis = json.loads(json_content)
        else:
            # Handle case where JSON isn't properly formatted
            print("WARNING: Could not extract JSON from GPT-4 response.")
            analysis = {}
    except Exception as e:
        print(f"Error parsing GPT-4 response for {gathering['name']}: {str(e)}")
        analysis = {}
    
    # Update with analysis results
    enhanced_gathering = gathering.copy()
    
    # Extract overall score if available
    if "overall_event_priority" in analysis:
        if isinstance(analysis["overall_event_priority"], dict) and "score" in analysis["overall_event_priority"]:
            enhanced_gathering["relevance_score"] = float(analysis["overall_event_priority"]["score"])
        else:
            # Try to extract score as a direct value
            try:
                enhanced_gathering["relevance_score"] = float(analysis["overall_event_priority"])
            except (ValueError, TypeError):
                # Keep original score if conversion fails
                pass
    
    # Extract detailed rationale for better qualification
    if "overall_event_priority" in analysis and isinstance(analysis["overall_event_priority"], dict) and "justification" in analysis["overall_event_priority"]:
        enhanced_gathering["relevance_rationale"] = analysis["overall_event_priority"]["justification"]
    
    # Include all detailed analysis for downstream processing
    enhanced_gathering["detailed_analysis"] = analysis
    
    return enhanced_gathering

def prioritize_gatherings(gatherings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Prioritize events and associations based on relevance score and analysis.
    
    This prioritization is critical for the quality-focused approach required
    by DuPont Tedlar, ensuring we focus on gatherings with the highest conversion potential.
    
    Args:
        gatherings: List of analyzed events and associations
        
    Returns:
        Prioritized list of gatherings
    """
    # Sort by relevance score (descending)
    sorted_gatherings = sorted(gatherings, key=lambda x: x.get("relevance_score", 0), reverse=True)
    
    # Add priority classification for easier downstream processing
    prioritized_gatherings = []
    for gathering in sorted_gatherings:
        gathering_copy = gathering.copy()
        score = gathering_copy.get("relevance_score", 0)
        
        # Classification thresholds based on our quality-focused approach
        if score >= 8.0:
            gathering_copy["priority"] = "high"
        elif score >= 6.0:
            gathering_copy["priority"] = "medium"
        else:
            gathering_copy["priority"] = "low"
        
        prioritized_gatherings.append(gathering_copy)
    
    return prioritized_gatherings

def save_gathering_data(gatherings: List[Dict[str, Any]]):
    """Save event and association data to JSON files."""
    events_dir = DATA_DIR / "events"
    events_dir.mkdir(exist_ok=True)
    
    associations_dir = DATA_DIR / "associations"
    associations_dir.mkdir(exist_ok=True)
    
    # Custom JSON encoder to handle UUIDs and datetimes
    class CustomEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, uuid.UUID):
                return str(obj)
            if isinstance(obj, datetime):
                return obj.isoformat()
            return super().default(obj)
    
    # Save each gathering as a separate JSON file
    for gathering in gatherings:
        # Create a unique ID if it doesn't have one
        if "id" not in gathering:
            gathering["id"] = str(uuid.uuid4())
        
        try:
            # Create Event object for validation
            gathering_obj = Event(
                id=gathering["id"],
                name=gathering["name"],
                date=gathering.get("date", ""),
                location=gathering.get("location", ""),
                description=gathering.get("description", ""),
                website=gathering.get("website", ""),
                attendees_estimate=None,
                relevance_score=gathering.get("relevance_score", 0.0),
                relevance_rationale=gathering.get("relevance_rationale", ""),
                source=gathering.get("source", "")
            )
            
            # Convert to dictionary
            gathering_dict = gathering_obj.model_dump()  # Using model_dump as recommended
            
            # Add additional fields
            gathering_dict["type"] = gathering.get("type", "event")
            
            if "detailed_analysis" in gathering:
                gathering_dict["detailed_analysis"] = gathering["detailed_analysis"]
            
            if "priority" in gathering:
                gathering_dict["priority"] = gathering["priority"]
                
            # Save to appropriate directory based on type
            if gathering.get("type") == "association":
                file_path = associations_dir / f"{str(gathering_dict['id'])}.json"
            else:
                file_path = events_dir / f"{str(gathering_dict['id'])}.json"
                
            with open(file_path, "w") as f:
                json.dump(gathering_dict, f, indent=2, cls=CustomEncoder)
                
            print(f"Saved {gathering['type']} data for: {gathering['name']}")
        except Exception as e:
            print(f"Error saving {gathering.get('type', 'gathering')} {gathering.get('name', 'unknown')}: {str(e)}")

def run_event_association_research(limit=None, debug=False):
    """
    Run the complete event and association research process:
    1. Discover events, associations, and industry bodies with Perplexity (lower cost model)
    2. Analyze each one with GPT-4 Turbo (premium model)
    3. Prioritize based on relevance for lead generation
    4. Save data for later use
    
    This tiered approach optimizes our $200 budget while ensuring high-quality
    lead generation opportunities are identified.
    
    Args:
        limit: Optional limit on number of gatherings to analyze
        debug: Whether to print debug information
    """
    print("Starting event & association research process...")
    
    # Step 1: Discover all industry gatherings using cost-effective Perplexity
    gatherings = discover_industry_gatherings()
    
    if not gatherings:
        print("No events or associations discovered. Exiting.")
        return
    
    # Apply limit if specified (for budget control)
    if limit is not None and limit > 0:
        gatherings = gatherings[:limit]
        print(f"Limiting analysis to {limit} gatherings.")
    
    # Step 2: Analyze relevance with premium GPT-4 model
    analyzed_gatherings = []
    for gathering in gatherings:
        analyzed_gathering = analyze_gathering_relevance(gathering)
        analyzed_gatherings.append(analyzed_gathering)
        
        if debug:
            print(f"Analysis for {gathering['name']}:")
            print(json.dumps(analyzed_gathering.get("detailed_analysis", {}), indent=2))
        
        # Small delay to avoid API rate limits
        time.sleep(0.5)
    
    # Step 3: Prioritize gatherings based on conversion potential
    prioritized_gatherings = prioritize_gatherings(analyzed_gatherings)
    
    # Step 4: Save data for downstream processing
    save_gathering_data(prioritized_gatherings)
    
    # Track budget usage
    log_usage_report()
    
    # Print summary
    high_priority = sum(1 for g in prioritized_gatherings if g.get("priority") == "high")
    medium_priority = sum(1 for g in prioritized_gatherings if g.get("priority") == "medium")
    low_priority = sum(1 for g in prioritized_gatherings if g.get("priority") == "low")
    
    events_count = sum(1 for g in prioritized_gatherings if g.get("type") == "event")
    associations_count = sum(1 for g in prioritized_gatherings if g.get("type") == "association")
    
    print("\nEvent & Association Research Summary:")
    print(f"Total gatherings analyzed: {len(prioritized_gatherings)}")
    print(f"Events: {events_count}")
    print(f"Associations/Organizations: {associations_count}")
    print(f"High priority: {high_priority}")
    print(f"Medium priority: {medium_priority}")
    print(f"Low priority: {low_priority}")
    print("\nTop 3 gatherings by relevance score:")
    for gathering in prioritized_gatherings[:min(3, len(prioritized_gatherings))]:
        print(f"- {gathering['type'].title()}: {gathering['name']} (Score: {gathering['relevance_score']:.1f}, Priority: {gathering['priority']})")

def parse_arguments():
    """Parse command line arguments for more flexible execution."""
    import argparse
    parser = argparse.ArgumentParser(description="DuPont Tedlar Event & Association Research Module")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of gatherings to analyze")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    run_event_association_research(limit=args.limit, debug=args.debug)