"""
Outreach Message Generation Module for DuPont Tedlar Lead Generation System.

This module generates personalized outreach messages for stakeholders identified 
in the previous step. It implements a tiered approach:
- GPT-4 Turbo for high-priority stakeholders (more detailed personalization)
- GPT-3.5 Turbo for standard stakeholders (cost-effective personalization)

The focus is on creating conversion-oriented messages that emphasize specific 
Tedlar benefits relevant to each stakeholder's role and company needs.
"""

import os
import json
import time
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from config.config import TEDLAR_CONTEXT, LLM_CONFIG, DATA_DIR
from src.llm.llm_client import call_openai_api
from src.llm.prompt_templates import BASE_TEDLAR_CONTEXT, OUTREACH_MESSAGE_PROMPT
from src.utils.cost_tracker import is_budget_available, log_usage_report
from src.utils.data_models import OutreachMessage

def load_prioritized_stakeholders() -> List[Dict[str, Any]]:
    """
    Load stakeholders identified in the previous step.
    
    This function retrieves stakeholders that have been identified and prioritized,
    focusing on high and medium priority stakeholders for outreach.
    
    Returns:
        List of prioritized stakeholders
    """
    print("Loading prioritized stakeholders...")
    
    stakeholders = []
    
    # Load stakeholders
    stakeholders_dir = DATA_DIR / "stakeholders"
    if stakeholders_dir.exists():
        for stakeholder_file in stakeholders_dir.glob("*.json"):
            try:
                with open(stakeholder_file, "r") as f:
                    stakeholder_data = json.load(f)
                    
                    # Skip stakeholders from companies with generated names
                    if stakeholder_data.get("company_name", "").startswith("Company-") or \
                       stakeholder_data.get("company_name", "") == "Unknown Company":
                        print(f"Skipping stakeholder from {stakeholder_data.get('company_name')} (invalid company name)")
                        continue
                    
                    # Skip stakeholders with Unknown title/position
                    if stakeholder_data.get("title", "") == "Unknown":
                        print(f"Skipping stakeholder {stakeholder_data.get('name')} (unknown position)")
                        continue
                    
                    stakeholders.append(stakeholder_data)
            except Exception as e:
                print(f"Error loading stakeholder data from {stakeholder_file}: {str(e)}")
    
    # Sort by priority and decision_maker_score
    stakeholders = sorted(stakeholders, key=lambda s: (
        0 if s.get("priority") == "high" else (1 if s.get("priority") == "medium" else 2),
        -float(s.get("decision_maker_score", 0))
    ))
    
    print(f"Loaded {len(stakeholders)} prioritized stakeholders:")
    print(f"- High priority: {sum(1 for s in stakeholders if s.get('priority') == 'high')}")
    print(f"- Medium priority: {sum(1 for s in stakeholders if s.get('priority') == 'medium')}")
    print(f"- Low priority: {sum(1 for s in stakeholders if s.get('priority') == 'low')}")
    
    return stakeholders

def get_company_details(stakeholder: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get detailed company information for a stakeholder.
    
    This function retrieves the full company data to provide context
    for personalized outreach message generation.
    
    Args:
        stakeholder: Stakeholder information
        
    Returns:
        Company details dictionary
    """
    company_id = stakeholder.get("company_id", "")
    if not company_id:
        return {}
    
    # Attempt to load company data
    company_file = DATA_DIR / "companies" / f"{company_id}.json"
    if company_file.exists():
        try:
            with open(company_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading company data for {stakeholder.get('company_name', 'Unknown')}: {str(e)}")
    
    # If company file not found or error loading, create minimal company data from stakeholder
    return {
        "id": company_id,
        "name": stakeholder.get("company_name", "Unknown Company"),
        "industry": stakeholder.get("industry", "Graphics & Signage"),
        "customer_segment": stakeholder.get("customer_segment", "Sign Manufacturing Companies"),
        "description": "",
        "qualification_score": 0.0,
        "qualification_rationale": ""
    }

def get_event_context(company: Dict[str, Any]) -> str:
    """
    Get event context for the outreach message.
    
    This function identifies the event where the company was discovered,
    providing a personalized opener for the outreach message.
    
    Args:
        company: Company information
        
    Returns:
        Event context string for personalization
    """
    source_gathering = company.get("source_gathering_name", "")
    if not source_gathering:
        # If no specific event, use a general industry event
        industry_events = [
            "PRINTING United Expo",
            "ISA International Sign Expo",
            "FESPA Global Print Expo",
            "Graphics Pro Expo"
        ]
        import random
        source_gathering = random.choice(industry_events)
    
    return source_gathering

def generate_outreach_message(stakeholder: Dict[str, Any], company: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a personalized outreach message for a stakeholder.
    
    This function implements a tiered approach based on stakeholder priority:
    - Premium model (GPT-4 Turbo) for high-priority stakeholders
    - Standard model (GPT-3.5 Turbo) for other stakeholders
    
    Args:
        stakeholder: Stakeholder information
        company: Company information
        
    Returns:
        Outreach message with subject and body
    """
    print(f"Generating outreach message for: {stakeholder['name']} ({stakeholder['title']}) at {stakeholder['company_name']}...")
    
    # Budget check - critical for not exceeding our $200 allocation
    estimated_cost = 0.05 if stakeholder.get("priority") == "high" else 0.02
    if not is_budget_available("outreach_generation", estimated_cost):
        print(f"WARNING: Insufficient budget for outreach message generation.")
        return {
            "stakeholder_id": stakeholder["id"],
            "company_id": company["id"],
            "subject": f"Enhancing your signage durability with DuPont Tedlar",
            "message_body": "Insufficient budget for personalized message generation.",
            "personalization_factors": [],
            "value_propositions": [],
            "call_to_action": "Request more information"
        }
    
    # Format company details for the prompt
    company_details = f"""
    Company Name: {company['name']}
    Industry: {company.get('industry', 'Graphics & Signage')}
    Customer Segment: {company.get('customer_segment', 'Unknown')}
    Description: {company.get('description', '')}
    
    Qualification Information:
    - Qualification Score: {company.get('qualification_score', 0.0)}/10
    - Pain Points: {', '.join(company.get('detailed_qualification', {}).get('pain_points', []))}
    - Use Cases: {', '.join(company.get('detailed_qualification', {}).get('use_cases', []))}
    """
    
    # Get stakeholder-specific details
    stakeholder_name = stakeholder["name"]
    stakeholder_title = stakeholder["title"]
    stakeholder_role = "technical" if any(role in stakeholder_title.lower() for role in ["technical", "engineer", "director", "r&d"]) else "business"
    
    # Get event context
    event_name = get_event_context(company)
    
    # Get qualification rationale
    qualification_rationale = company.get("qualification_rationale", "")
    
    # Direct prompt construction or use template if available
    if OUTREACH_MESSAGE_PROMPT:
        from src.llm.prompt_templates import customize_prompt
        prompt = customize_prompt(
            OUTREACH_MESSAGE_PROMPT,
            stakeholder_name=stakeholder_name,
            stakeholder_title=stakeholder_title,
            company_name=company['name'],
            company_details=company_details,
            customer_segment=company.get('customer_segment', 'Sign Manufacturing Companies'),
            event_name=event_name,
            qualification_rationale=qualification_rationale
        )
    else:
        # Fallback direct prompt
        prompt = f"""
        {BASE_TEDLAR_CONTEXT}

        TASK: Create a highly personalized outreach message to the following stakeholder 
        at a qualified company, emphasizing Tedlar's value proposition for their specific needs.

        STAKEHOLDER: {stakeholder_name}, {stakeholder_title}
        COMPANY: {company['name']}
        COMPANY DETAILS: {company_details}
        CUSTOMER SEGMENT: {company.get('customer_segment', 'Sign Manufacturing Companies')}
        EVENT CONTEXT: {event_name}
        QUALIFICATION RATIONALE: {qualification_rationale}

        Create a personalized outreach message that:

        1. References the specific industry event as a conversation starter
           - Be specific about the event rather than generic

        2. Demonstrates understanding of their specific industry challenges
           - Reference the exact pain points from their customer segment
           - Use industry-specific terminology familiar to their role

        3. Highlights 2-3 Tedlar benefits with quantified performance data
           - For technical roles: Focus on specific performance metrics (e.g., <3 Delta E color shift, temperature range)
           - For business roles: Emphasize TCO (30-40% lower lifetime costs despite 15-20% premium pricing)

        4. References a relevant application example
           - Choose from Tedlar's specific use cases that match their business
           - Be specific about how Tedlar solves their particular challenge

        5. Includes a clear, low-friction call to action
           - Suggest a specific topic for discussion
           - Offer to share relevant case studies or technical information

        The message should be concise (150-200 words), conversion-focused, and demonstrate deep
        understanding of both their business and how Tedlar specifically addresses their needs.

        FORMAT YOUR RESPONSE WITH:
        - Email subject line (compelling, specific to their needs)
        - Message body (personalized, value-focused)
        - List of personalization elements used
        """
    
    # Use appropriate model based on stakeholder priority
    model_tier = "high_quality" if stakeholder.get("priority") == "high" else "standard"
    
    if model_tier == "high_quality":
        # Use premium model for high-priority stakeholders
        model_config = {
            "model": "gpt-4-turbo",
            "temperature": 0.7,  # Higher temperature for creative messaging
            "max_tokens": 1000,
        }
        operation = "premium_outreach_generation"
    else:
        # Use cost-effective model for standard stakeholders
        model_config = {
            "model": "gpt-3.5-turbo",
            "temperature": 0.6,
            "max_tokens": 800,
        }
        operation = "standard_outreach_generation"
    
    response = call_openai_api(
        messages=[{"role": "system", "content": prompt}],
        model=model_config["model"],
        temperature=model_config["temperature"],
        max_tokens=model_config["max_tokens"],
        module="outreach_generation",
        operation=operation
    )
    
    # Parse the response
    content = response["content"]
    
    # Extract subject and message body
    subject = ""
    message_body = ""
    personalization_factors = []
    value_propositions = []
    call_to_action = ""
    
    # Extract subject line (usually the first line after "Subject:" or similar)
    subject_markers = ["Subject:", "Subject Line:", "Email Subject:"]
    for marker in subject_markers:
        if marker in content:
            subject_start = content.index(marker) + len(marker)
            subject_end = content.find("\n", subject_start)
            if subject_end > subject_start:
                subject = content[subject_start:subject_end].strip()
                break
    
    # If no explicit subject marker, use the first line if it's short enough
    if not subject and "\n" in content:
        first_line = content.split("\n")[0].strip()
        if len(first_line) < 100 and not first_line.startswith("Dear") and not first_line.startswith("Hello"):
            subject = first_line
    
    # If still no subject, generate a default one
    if not subject:
        if stakeholder_role == "technical":
            subject = f"Enhanced durability metrics for {company['name']}'s signage"
        else:
            subject = f"Reducing TCO for {company['name']}'s graphics solutions"
    
    # Extract message body
    body_indicators = ["Dear", "Hello", "Hi ", "Greetings", "Good"]
    for indicator in body_indicators:
        if indicator in content:
            message_start = content.find(indicator)
            message_body = content[message_start:].strip()
            break
    
    # If no clear message body identified, use everything after the subject
    if not message_body and subject:
        message_start = content.find(subject) + len(subject)
        message_body = content[message_start:].strip()
        # Remove any section starts that might be part of the API response
        for section in ["Personalization elements:", "Value propositions:", "Call to action:"]:
            if section in message_body:
                message_body = message_body[:message_body.find(section)].strip()
    
    # If still no message body, use the entire content (fallback)
    if not message_body:
        message_body = content.strip()
    
    # Extract personalization elements if listed
    if "Personalization elements:" in content:
        personalization_section = content.split("Personalization elements:")[1]
        if "\n\n" in personalization_section:
            personalization_section = personalization_section.split("\n\n")[0]
        
        # Extract bullet points or numbered items
        import re
        personalization_factors = re.findall(r'\n[-*•]?\s*(.*?)(?=\n[-*•]|\n\n|$)', personalization_section)
        personalization_factors = [p.strip() for p in personalization_factors if p.strip()]
    
    # If no personalization elements extracted, create defaults
    if not personalization_factors:
        personalization_factors = [
            f"Reference to {event_name}",
            f"Specific role: {stakeholder_title}",
            f"Industry segment: {company.get('customer_segment', 'Sign Manufacturing')}"
        ]
    
    # Extract value propositions if listed
    if "Value propositions:" in content:
        value_section = content.split("Value propositions:")[1]
        if "\n\n" in value_section:
            value_section = value_section.split("\n\n")[0]
        
        # Extract bullet points or numbered items
        import re
        value_propositions = re.findall(r'\n[-*•]?\s*(.*?)(?=\n[-*•]|\n\n|$)', value_section)
        value_propositions = [v.strip() for v in value_propositions if v.strip()]
    
    # If no value propositions extracted, create defaults
    if not value_propositions:
        if stakeholder_role == "technical":
            value_propositions = [
                "Superior UV resistance (<3 Delta E color shift after 10 years)",
                "Anti-delamination technology preventing edge lifting",
                "Chemical resistance to 300+ substances"
            ]
        else:
            value_propositions = [
                "30-40% lower lifetime costs despite premium pricing",
                "5-7 years longer graphic life than standard laminates",
                "Reduced maintenance and warranty claims"
            ]
    
    # Extract call to action
    if "Call to action:" in content:
        cta_section = content.split("Call to action:")[1]
        if "\n\n" in cta_section:
            cta_section = cta_section.split("\n\n")[0]
        call_to_action = cta_section.strip()
    
    # If no call to action extracted, create a default one
    if not call_to_action:
        if stakeholder_role == "technical":
            call_to_action = "Discuss specific durability requirements for your projects"
        else:
            call_to_action = "Schedule a brief call to explore potential cost savings"
    
    # Create outreach message object
    outreach_message = {
        "id": str(uuid.uuid4()),
        "stakeholder_id": stakeholder["id"],
        "company_id": company["id"],
        "stakeholder_name": stakeholder["name"],
        "stakeholder_title": stakeholder["title"],
        "company_name": company["name"],
        "subject": subject,
        "message_body": message_body,
        "personalization_factors": personalization_factors,
        "value_propositions": value_propositions,
        "call_to_action": call_to_action,
        "created_at": datetime.now().isoformat(),
        "stakeholder_role": stakeholder_role
    }
    
    return outreach_message

def save_outreach_message(message: Dict[str, Any]):
    """
    Save outreach message to JSON file.
    
    This function stores the generated outreach message for later display
    in the dashboard and for potential integration with email systems.
    
    Args:
        message: Outreach message to save
    """
    outreach_dir = DATA_DIR / "outreach"
    outreach_dir.mkdir(exist_ok=True)
    
    # Custom JSON encoder to handle various data types
    class CustomEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, uuid.UUID):
                return str(obj)
            if isinstance(obj, datetime):
                return obj.isoformat()
            return super().default(obj)
    
    try:
        # Create OutreachMessage object for validation
        outreach_obj = OutreachMessage(
            id=message["id"],
            stakeholder_id=message["stakeholder_id"],
            company_id=message["company_id"],
            subject=message["subject"],
            message_body=message["message_body"],
            call_to_action=message["call_to_action"]
        )
        
        # Convert to dictionary for saving
        outreach_dict = outreach_obj.model_dump()
        
        # Add additional fields
        outreach_dict["stakeholder_name"] = message["stakeholder_name"]
        outreach_dict["stakeholder_title"] = message["stakeholder_title"]
        outreach_dict["company_name"] = message["company_name"]
        outreach_dict["personalization_factors"] = message["personalization_factors"]
        outreach_dict["value_propositions"] = message["value_propositions"]
        outreach_dict["stakeholder_role"] = message["stakeholder_role"]
        
        # Save to file
        outreach_file = outreach_dir / f"{message['id']}.json"
        with open(outreach_file, "w") as f:
            json.dump(outreach_dict, f, indent=2, cls=CustomEncoder)
            
        print(f"Saved outreach message for: {message['stakeholder_name']} at {message['company_name']}")
        return True
    except Exception as e:
        print(f"Error saving outreach message for {message.get('stakeholder_name', 'unknown')}: {str(e)}")
        return False

def run_outreach_generation(limit_stakeholders=None, debug=False):
    """
    Run the complete outreach message generation process:
    1. Load prioritized stakeholders from prior analysis
    2. Get detailed company information for each stakeholder
    3. Generate personalized outreach messages
    4. Save outreach messages for dashboard display
    
    This approach optimizes the $200 budget while ensuring high-quality,
    personalized outreach messages for the most promising leads.
    
    Args:
        limit_stakeholders: Optional limit on number of stakeholders to process
        debug: Whether to print debug information
    """
    print("Starting outreach message generation process...")
    
    # Step 1: Load prioritized stakeholders
    stakeholders = load_prioritized_stakeholders()
    
    if not stakeholders:
        print("No prioritized stakeholders found. Run stakeholder identification module first.")
        return
    
    # Apply limit on stakeholders if specified
    if limit_stakeholders is not None and limit_stakeholders > 0:
        stakeholders = stakeholders[:limit_stakeholders]
        print(f"Limiting generation to {limit_stakeholders} stakeholders.")
    
    # Step 2 & 3: Generate outreach messages for each stakeholder
    outreach_messages = []
    for stakeholder in stakeholders:
        # Get company details
        company = get_company_details(stakeholder)
        
        # Skip if company is unknown or has issues
        if not company or company.get("name", "") == "Unknown Company":
            print(f"Skipping outreach for {stakeholder['name']} (company data unavailable)")
            continue
        
        # Generate personalized message
        message = generate_outreach_message(stakeholder, company)
        outreach_messages.append(message)
        
        if debug:
            print(f"\nOutreach for {stakeholder['name']} at {company['name']}:")
            print(f"Subject: {message['subject']}")
            print(f"Personalization: {', '.join(message['personalization_factors'])}")
            print(f"Message: {message['message_body'][:100]}...")
        
        # Small delay to avoid API rate limits
        time.sleep(0.5)
    
    # Step 4: Save outreach messages
    saved_count = 0
    for message in outreach_messages:
        if save_outreach_message(message):
            saved_count += 1
    
    # Track budget usage
    log_usage_report()
    
    # Print summary
    print(f"\nOutreach Generation Summary:")
    print(f"Total messages generated: {len(outreach_messages)}")
    print(f"Total messages saved: {saved_count}")
    
    # Print sample messages
    if outreach_messages:
        print(f"\nSample Outreach Messages:")
        for i, message in enumerate(outreach_messages[:min(3, len(outreach_messages))]):
            print(f"\n{i+1}. To: {message['stakeholder_name']} ({message['stakeholder_title']}) at {message['company_name']}")
            print(f"Subject: {message['subject']}")
            print(f"Message (excerpt): {message['message_body'][:150]}...")

def parse_arguments():
    """Parse command line arguments for more flexible execution."""
    import argparse
    parser = argparse.ArgumentParser(description="DuPont Tedlar Outreach Message Generation Module")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of stakeholders to process")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    run_outreach_generation(
        limit_stakeholders=args.limit,
        debug=args.debug
    )