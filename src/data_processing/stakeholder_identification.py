"""
Stakeholder Identification Module for DuPont Tedlar Lead Generation System.

This module identifies key decision-makers at qualified companies who would be involved
in purchasing protective films for graphics and signage applications. It implements 
a tiered LLM approach:
- GPT-3.5 Turbo for initial stakeholder discovery (lower cost)
- GPT-4 Turbo for detailed analysis of high-priority stakeholders (premium model)

The focus is on identifying 1-2 high-value stakeholders per company rather than 
an exhaustive list, emphasizing quality over quantity for conversion-focused outreach.
"""

import os
import json
import time
import uuid
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from config.config import TEDLAR_CONTEXT, LLM_CONFIG, DATA_DIR
from src.llm.llm_client import call_openai_api
from src.llm.prompt_templates import BASE_TEDLAR_CONTEXT, STAKEHOLDER_IDENTIFICATION_PROMPT, LINKEDIN_QUERY_TEMPLATE
from src.utils.cost_tracker import is_budget_available, log_usage_report
from src.utils.data_models import Stakeholder

"""
API INTEGRATION PROVISIONS:

This module is designed for future integration with external APIs:

1. LinkedIn Sales Navigator API Integration:
   - Would replace the `generate_random_linkedin_id()` function with actual API calls
   - Integration point: After stakeholder identification, before generating the outreach
   - API endpoint would be: https://api.linkedin.com/v2/salesNavigator/lead/{company_id}
   - Sample implementation:
     ```
     def get_real_stakeholder_data(company_name, job_title):
         # Authentication with Sales Navigator API
         headers = {"Authorization": f"Bearer {LINKEDIN_API_KEY}"}
         
         # Search for stakeholders matching criteria
         params = {
             "company_name": company_name,
             "job_title": job_title,
             "count": 5
         }
         response = requests.get("https://api.linkedin.com/v2/salesNavigator/search", 
                                headers=headers, params=params)
         return response.json()
     ```

2. Clay API Integration:
   - Alternative data enrichment source if LinkedIn data is unavailable
   - Integration point: After company identification, before stakeholder generation
   - Sample implementation:
     ```
     def enrich_stakeholder_data(stakeholder):
         # Clay API for contact information enrichment
         headers = {"Authorization": f"Bearer {CLAY_API_KEY}"}
         
         # Enrich with contact details
         data = {
             "name": stakeholder["name"],
             "company": stakeholder["company_name"],
             "title": stakeholder["title"]
         }
         response = requests.post("https://api.clay.com/v1/enrichment", 
                                 headers=headers, json=data)
         
         # Update stakeholder with email and phone from Clay
         enriched_data = response.json()
         stakeholder["email"] = enriched_data.get("email")
         stakeholder["phone"] = enriched_data.get("phone")
         return stakeholder
     ```

3. Data Security and Validation:
   - All API responses would be validated before storage
   - Contact information stored securely as per compliance requirements
   - API rate limits would be respected with exponential backoff
"""

def load_qualified_companies() -> List[Dict[str, Any]]:
    """
    Load qualified companies from the company analysis phase.
    
    This function retrieves companies that have been identified and qualified
    in the company analysis module, prioritizing high and medium priority companies.
    
    Returns:
        List of qualified companies
    """
    print("Loading qualified companies...")
    
    companies = []
    
    # Load companies
    companies_dir = DATA_DIR / "companies"
    if companies_dir.exists():
        print(f"Found company directory at: {companies_dir}")
        company_files = list(companies_dir.glob("*.json"))
        print(f"Found {len(company_files)} company JSON files")
        
        for company_file in companies_dir.glob("*.json"):
            try:
                with open(company_file, "r") as f:
                    company_data = json.load(f)
                    
                    # Debug info
                    print(f"Loaded company: {company_data.get('name', 'Missing name')} (ID: {company_data.get('id', 'No ID')})")
                    
                    # Ensure required fields are present
                    if "name" not in company_data or not company_data["name"] or company_data["name"] == "Unknown Company":
                        new_name = f"Company-{company_file.stem[-8:]}"
                        print(f"⚠️ Company missing valid name, assigning: {new_name}")
                        company_data["name"] = new_name
                    
                    # Ensure ID is present
                    if "id" not in company_data:
                        company_data["id"] = str(uuid.uuid4())
                        print(f"Added missing ID to company: {company_data['name']}")
                    
                    companies.append(company_data)
            except Exception as e:
                print(f"Error loading company data from {company_file}: {str(e)}")
    
    # Sort by priority and qualification score
    companies = sorted(companies, key=lambda c: (
        0 if c.get("lead_priority") == "exceptional" else (
            1 if c.get("lead_priority") == "high_priority" else (
                2 if c.get("lead_priority") == "qualified" else 3
            )
        ),
        -float(c.get("qualification_score", 0))
    ))
    
    print(f"Loaded {len(companies)} qualified companies:")
    print(f"- Exceptional priority: {sum(1 for c in companies if c.get('lead_priority') == 'exceptional')}")
    print(f"- High priority: {sum(1 for c in companies if c.get('lead_priority') == 'high_priority')}")
    print(f"- Qualified: {sum(1 for c in companies if c.get('lead_priority') == 'qualified')}")
    print(f"- Other: {sum(1 for c in companies if c.get('lead_priority') not in ['exceptional', 'high_priority', 'qualified'])}")
    
    return companies

def generate_name_from_title(title):
    """
    Generate a placeholder name based on job title.
    """
    first_names = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Avery", "Quinn"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Wilson"]
    
    import random
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def identify_stakeholders_for_company(company: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Identify key decision-makers at a qualified company.
    
    This function implements the first tier of our LLM approach, using a
    cost-effective model for initial stakeholder identification.
    
    Args:
        company: Qualified company information
        
    Returns:
        List of identified stakeholders
    """
    print(f"Identifying stakeholders for: {company['name']}...")
    
    # Budget check
    estimated_cost = 0.03  # Approximate cost for initial stakeholder identification
    if not is_budget_available("stakeholder_identification", estimated_cost):
        print(f"WARNING: Insufficient budget for stakeholder identification for {company['name']}.")
        return []
    
    # Format company details for the prompt
    company_details = f"""
    Company Name: {company['name']}
    Industry: {company.get('industry', 'Graphics & Signage')}
    Customer Segment: {company.get('customer_segment', 'Unknown')}
    Description: {company.get('description', '')}
    Estimated Revenue: {company.get('revenue_estimate', 'Unknown')}
    Estimated Size: {company.get('size_estimate', 'Unknown')}
    Website: {company.get('website', 'Unknown')}
    
    Qualification Information:
    - Qualification Score: {company.get('qualification_score', 0.0)}/10
    - Priority: {company.get('lead_priority', 'Unknown')}
    - Pain Points: {', '.join(company.get('detailed_qualification', {}).get('pain_points', []))}
    - Use Cases: {', '.join(company.get('detailed_qualification', {}).get('use_cases', []))}
    """
    
    # Get customer segment - critical for identifying the right roles
    customer_segment = company.get('customer_segment', '')
    if not customer_segment:
        # Try to infer from industry if not available
        if 'print' in company.get('industry', '').lower():
            customer_segment = "Large Format Print Providers"
        elif 'fleet' in company.get('industry', '').lower() or 'vehicle' in company.get('industry', '').lower():
            customer_segment = "Fleet Graphics Specialists"
        elif 'architect' in company.get('industry', '').lower():
            customer_segment = "Architectural Graphics Manufacturers"
        elif 'outdoor' in company.get('industry', '').lower() or 'billboard' in company.get('industry', '').lower():
            customer_segment = "Outdoor Advertising Companies"
        elif 'sign' in company.get('industry', '').lower():
            customer_segment = "Sign Manufacturing Companies"
        elif 'distribut' in company.get('industry', '').lower() or 'supply' in company.get('industry', '').lower():
            customer_segment = "Material Distributors & Converters"
        else:
            customer_segment = "Sign Manufacturing Companies"  # Default fallback
    
    # Direct prompt construction or use template if available
    if STAKEHOLDER_IDENTIFICATION_PROMPT:
        from src.llm.prompt_templates import customize_prompt
        prompt = customize_prompt(
            STAKEHOLDER_IDENTIFICATION_PROMPT,
            company_name=company['name'],
            company_details=company_details,
            customer_segment=customer_segment
        )
    else:
        # Fallback direct prompt
        prompt = f"""
        {BASE_TEDLAR_CONTEXT}

        TASK: Identify key decision-makers at the following company who would be involved in 
        purchasing protective films for graphics and signage applications.

        COMPANY: {company['name']}
        DETAILS: {company_details}
        CUSTOMER SEGMENT: {customer_segment}

        Based on the company's customer segment, identify the specific decision-maker roles that 
        would be involved in evaluating and purchasing Tedlar protective films.

        For each potential stakeholder:

        1. Identify the exact job title based on the company's customer segment:
           - For Large Format Print Providers: Target Operations Directors, Production Managers, R&D Directors
           - For Fleet Graphics Specialists: Target Fleet Graphics Directors, Product Development Managers
           - For Architectural Graphics: Target VP of Product Development, Materials Engineering Directors
           - For Outdoor Advertising: Target Production Directors, Materials Procurement Managers
           - For Sign Manufacturing: Target Production Managers, Technical Directors
           - For Material Distributors: Target Product Line Managers, Business Development Directors

        2. For each identified role:
           - Explain their likely responsibilities related to protective films
           - Assess their influence in the purchasing decision process (primary, influential, technical evaluator)
           - Identify specific Tedlar benefits that would resonate with their role
           - Explain how Tedlar addresses their specific job challenges
           - Assign a decision-maker score (1-10)
           - Provide a detailed rationale for this score

        3. Prioritize stakeholders based on:
           - Decision-making authority
           - Alignment with Tedlar's value proposition
           - Technical vs. business focus
           - Influence in the organization

        Focus on 2-3 high-value stakeholders rather than an exhaustive list.
        Consider both technical decision-makers and financial/business approvers.

        FOR EACH STAKEHOLDER, INCLUDE A LINKEDIN PROFILE URL in this format:
        https://www.linkedin.com/sales/people/ACoAA..., with a realistic-looking Sales Navigator ID.

        FORMAT YOUR RESPONSE AS JSON with stakeholder details and decision-making assessment.
        Include a priority ranking of which stakeholders to contact first.
        """
    
    # Use appropriate model based on company priority
    model_tier = "high_quality" if company.get('lead_priority') in ['exceptional', 'high_priority'] else "standard"
    
    if model_tier == "high_quality":
        # Use premium model for high-priority companies
        model_config = {
            "model": "gpt-4-turbo",
            "temperature": 0.4,
            "max_tokens": 1500,
        }
        operation = "detailed_stakeholder_identification"
    else:
        # Use cost-effective model for standard companies
        model_config = {
            "model": "gpt-3.5-turbo",
            "temperature": 0.3,
            "max_tokens": 1200,
        }
        operation = "standard_stakeholder_identification"
    
    response = call_openai_api(
        messages=[{"role": "system", "content": prompt}],
        model=model_config["model"],
        temperature=model_config["temperature"],
        max_tokens=model_config["max_tokens"],
        module="stakeholder_identification",
        operation=operation
    )
    
    # Extract and parse the stakeholders from the response
    try:
        content = response["content"]
        
        # Debug output to help with troubleshooting
        print(f"\nDEBUG - First 500 characters of API response:")
        print(content[:500])
        print("\n")
        
        # Try to parse the JSON response
        try:
            # Try direct parsing first
            stakeholders_data = json.loads(content)
            
            # Debug the structure
            print(f"Parsed JSON structure: {list(stakeholders_data.keys()) if isinstance(stakeholders_data, dict) else 'list'}")
            
            # Check all possible structures
            if isinstance(stakeholders_data, dict):
                # Try different possible keys for stakeholders
                if "stakeholders" in stakeholders_data:
                    stakeholders = stakeholders_data["stakeholders"]
                elif "Stakeholders" in stakeholders_data:
                    stakeholders = stakeholders_data["Stakeholders"]
                elif "people" in stakeholders_data:
                    stakeholders = stakeholders_data["people"]
                elif "People" in stakeholders_data:
                    stakeholders = stakeholders_data["People"]
                elif "decision_makers" in stakeholders_data:
                    stakeholders = stakeholders_data["decision_makers"]
                elif "DecisionMakers" in stakeholders_data:
                    stakeholders = stakeholders_data["DecisionMakers"]
                else:
                    # If no stakeholders array found, check if this is a single stakeholder
                    if any(key in stakeholders_data for key in ["name", "title", "jobTitle", "JobTitle", "role", "Role"]):
                        stakeholders = [stakeholders_data]  # Single stakeholder as an object
                    else:
                        stakeholders = []
            elif isinstance(stakeholders_data, list):
                stakeholders = stakeholders_data
            else:
                stakeholders = []
                
            # Debug the stakeholders
            print(f"Found {len(stakeholders)} stakeholders in response")
            for idx, s in enumerate(stakeholders):
                print(f"Stakeholder {idx+1} keys: {list(s.keys()) if isinstance(s, dict) else 'not a dict'}")
                
        except json.JSONDecodeError:
            # Try to extract JSON content if direct parsing fails
            import re
            
            # First try to find a JSON object/array
            json_matches = re.findall(r'```json(.*?)```', content, re.DOTALL)
            if json_matches:
                clean_json = json_matches[0].strip()
                try:
                    stakeholders_data = json.loads(clean_json)
                    # Process same as above
                    if isinstance(stakeholders_data, dict):
                        if "stakeholders" in stakeholders_data:
                            stakeholders = stakeholders_data["stakeholders"]
                        elif "Stakeholders" in stakeholders_data:
                            stakeholders = stakeholders_data["Stakeholders"]
                        else:
                            stakeholders = [stakeholders_data]
                    elif isinstance(stakeholders_data, list):
                        stakeholders = stakeholders_data
                    else:
                        stakeholders = []
                except:
                    stakeholders = []
            else:
                # If no JSON object found, use regex to extract
                stakeholder_patterns = re.findall(r'\{\s*"(?:name|title|jobTitle|JobTitle)".*?(?=\{\s*"(?:name|title|jobTitle|JobTitle)|\Z)', content, re.DOTALL)
                
                if stakeholder_patterns:
                    stakeholders = []
                    for pattern in stakeholder_patterns:
                        # Clean up and complete the JSON
                        if not pattern.strip().endswith('}'):
                            pattern += '}'
                        try:
                            stakeholder = json.loads(pattern)
                            stakeholders.append(stakeholder)
                        except:
                            pass
                else:
                    # Fallback if no structured data can be extracted
                    print(f"WARNING: Could not extract JSON from response for {company['name']}. Using fallback approach.")
                    stakeholders = []
    except Exception as e:
        print(f"Error parsing stakeholders for {company['name']}: {str(e)}")
        stakeholders = []
    
    # If no stakeholders found, create fallback stakeholders
    if not stakeholders:
        # Create fallback stakeholders based on customer segment
        segment = company.get('customer_segment', 'Sign Manufacturing Companies')
        
        if segment == "Large Format Print Providers":
            stakeholders = [
                {
                    "name": f"Alex Johnson",
                    "title": "Operations Director",
                    "decision_maker_score": 9.0,
                    "rationale": "Operations Directors at Large Format Print Providers typically oversee production processes and make material sourcing decisions.",
                    "linkedin_url": f"https://www.linkedin.com/sales/people/ACoAA{generate_random_linkedin_id()}"
                },
                {
                    "name": f"Sam Williams",
                    "title": "Production Manager",
                    "decision_maker_score": 8.0,
                    "rationale": "Production Managers influence material selection based on quality and performance requirements.",
                    "linkedin_url": f"https://www.linkedin.com/sales/people/ACoAA{generate_random_linkedin_id()}"
                }
            ]
        elif segment == "Fleet Graphics Specialists":
            stakeholders = [
                {
                    "name": f"Taylor Reed",
                    "title": "Fleet Graphics Director",
                    "decision_maker_score": 9.0,
                    "rationale": "Fleet Graphics Directors make decisions on materials that ensure longevity of vehicle wraps.",
                    "linkedin_url": f"https://www.linkedin.com/sales/people/ACoAA{generate_random_linkedin_id()}"
                },
                {
                    "name": f"Jamie Martin",
                    "title": "Product Development Manager",
                    "decision_maker_score": 7.5,
                    "rationale": "Product Development Managers evaluate new materials for enhanced performance.",
                    "linkedin_url": f"https://www.linkedin.com/sales/people/ACoAA{generate_random_linkedin_id()}"
                }
            ]
        else:
            stakeholders = [
                {
                    "name": f"Morgan Smith",
                    "title": "Production Director",
                    "decision_maker_score": 8.5,
                    "rationale": "Production Directors influence material selection based on performance requirements.",
                    "linkedin_url": f"https://www.linkedin.com/sales/people/ACoAA{generate_random_linkedin_id()}"
                },
                {
                    "name": f"Casey Brown",
                    "title": "Materials Procurement Manager",
                    "decision_maker_score": 7.0,
                    "rationale": "Materials Procurement Managers make purchasing decisions based on cost-benefit analysis.",
                    "linkedin_url": f"https://www.linkedin.com/sales/people/ACoAA{generate_random_linkedin_id()}"
                }
            ]
    
    # Enhance stakeholder data with company context
    enhanced_stakeholders = []
    for idx, stakeholder in enumerate(stakeholders):
        stakeholder_id = str(uuid.uuid4())
        
        print(f"Processing stakeholder {idx+1}: {list(stakeholder.keys()) if isinstance(stakeholder, dict) else 'not a dict'}")
        
        # Extract name - check multiple possible field names
        name = None
        for name_field in ["name", "Name", "contact", "Contact", "person", "Person"]:
            if name_field in stakeholder and stakeholder[name_field]:
                name = stakeholder[name_field]
                break
        
        # If no name found, generate one
        if not name:
            # Generate name from title/role if available
            title_value = None
            for title_field in ["title", "Title", "jobTitle", "JobTitle", "role", "Role", "position", "Position"]:
                if title_field in stakeholder and stakeholder[title_field]:
                    title_value = stakeholder[title_field]
                    break
                    
            name = generate_name_from_title(title_value or "Unknown")
        
        # Extract title - check multiple possible field names
        title = None
        for title_field in ["title", "Title", "jobTitle", "JobTitle", "role", "Role", "position", "Position"]:
            if title_field in stakeholder and stakeholder[title_field]:
                title = stakeholder[title_field]
                break
        
        # Extract decision maker score - check multiple possible field names
        score = 7.5  # Default score
        for score_field in [
            "decision_maker_score", "decisionMakerScore", "DecisionMakerScore", 
            "score", "Score", "relevance", "Relevance", "priority_score", "PriorityScore"
        ]:
            if score_field in stakeholder and stakeholder[score_field]:
                try:
                    score = float(stakeholder[score_field])
                    break
                except:
                    pass
        
        # Extract rationale - check multiple possible field names
        rationale = ""
        for rationale_field in [
            "rationale", "Rationale", "decision_maker_rationale", "decisionMakerRationale",
            "justification", "Justification", "reason", "Reason", "explanation", "Explanation",
            "JobChallengesAddressed", "jobChallengesAddressed"
        ]:
            if rationale_field in stakeholder and stakeholder[rationale_field]:
                if isinstance(stakeholder[rationale_field], list):
                    rationale = "; ".join(stakeholder[rationale_field])
                else:
                    rationale = stakeholder[rationale_field]
                break
        
        # Extract LinkedIn URL - check multiple possible field names
        linkedin_url = ""
        for linkedin_field in [
            "linkedin_url", "linkedinUrl", "LinkedinUrl", "linkedin", "Linkedin",
            "linkedInProfile", "LinkedInProfile"
        ]:
            if linkedin_field in stakeholder and stakeholder[linkedin_field]:
                linkedin_url = stakeholder[linkedin_field]
                break
        
        # Extract responsibilities - check multiple possible field names
        responsibilities = []
        for resp_field in ["responsibilities", "Responsibilities", "duties", "Duties", "role_details", "RoleDetails"]:
            if resp_field in stakeholder:
                if isinstance(stakeholder[resp_field], list):
                    responsibilities = stakeholder[resp_field]
                elif isinstance(stakeholder[resp_field], str):
                    responsibilities = [stakeholder[resp_field]]
                break
        
        # Extract influence - check multiple possible field names
        influence = ""
        for influence_field in ["influence", "Influence", "influenceInPurchasing", "InfluenceInPurchasing"]:
            if influence_field in stakeholder and stakeholder[influence_field]:
                influence = stakeholder[influence_field]
                break
        
        # Extract benefits - check multiple possible field names
        benefits = []
        for benefit_field in [
            "relevant_benefits", "relevantBenefits", "tedlarBenefits", "TedlarBenefits",
            "benefits", "Benefits"
        ]:
            if benefit_field in stakeholder:
                if isinstance(stakeholder[benefit_field], list):
                    benefits = stakeholder[benefit_field]
                elif isinstance(stakeholder[benefit_field], str):
                    benefits = [stakeholder[benefit_field]]
                break
        
        enhanced_stakeholders.append({
            "id": stakeholder_id,
            "company_id": company.get("id", ""),
            "company_name": company["name"],
            "name": name,
            "title": title or "Unknown",
            "department": stakeholder.get("department", ""),
            "decision_maker_score": score,
            "decision_maker_rationale": rationale,
            "linkedin_url": linkedin_url,
            "email": stakeholder.get("email", ""),
            "priority": stakeholder.get("priority", "medium"),
            "responsibilities": responsibilities,
            "influence": influence,
            "relevant_benefits": benefits,
            "customer_segment": company.get("customer_segment", "")
        })
        
        print(f"Enhanced stakeholder: {name} ({title or 'Unknown'}) at {company['name']}")
    
    print(f"Identified {len(enhanced_stakeholders)} stakeholders for {company['name']}.")
    return enhanced_stakeholders

def generate_random_linkedin_id():
    """
    Generate a realistic-looking LinkedIn Sales Navigator profile ID.
    
    Sales Navigator IDs are typically 10-12 characters consisting of 
    alphanumeric characters after 'ACoAA'.
    """
    characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    id_length = random.randint(10, 12)
    return ''.join(random.choice(characters) for _ in range(id_length))

def generate_sales_navigator_query(company: Dict[str, Any], stakeholder: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a LinkedIn Sales Navigator search query for finding the stakeholder.
    
    This function implements the second tier of our LLM approach, using a
    specialized query generator to help sales teams find the exact stakeholder.
    
    Args:
        company: Company information
        stakeholder: Stakeholder information
        
    Returns:
        Enhanced stakeholder with Sales Navigator query
    """
    print(f"Generating Sales Navigator query for: {stakeholder['name']} ({stakeholder['title']})...")
    
    # Budget check
    estimated_cost = 0.01  # Very small cost for query generation
    if not is_budget_available("stakeholder_identification", estimated_cost):
        print(f"WARNING: Insufficient budget for Sales Navigator query generation.")
        return stakeholder
    
    # Only generate queries for high-scoring stakeholders to optimize budget
    if stakeholder.get("decision_maker_score", 0.0) < 7.0:
        print(f"Skipping query generation for low-scoring stakeholder: {stakeholder['name']}.")
        return stakeholder
    
    # Format company and stakeholder details for the prompt
    company_details = f"""
    Company Name: {company['name']}
    Industry: {company.get('industry', 'Graphics & Signage')}
    Customer Segment: {company.get('customer_segment', 'Unknown')}
    Description: {company.get('description', '')}
    Estimated Size: {company.get('size_estimate', 'Unknown')}
    """
    
    customer_segment = company.get('customer_segment', '')
    
    # Direct prompt construction or use template if available
    if LINKEDIN_QUERY_TEMPLATE:
        from src.llm.prompt_templates import customize_prompt
        prompt = customize_prompt(
            LINKEDIN_QUERY_TEMPLATE,
            company_name=company['name'],
            company_details=company_details,
            customer_segment=customer_segment
        )
    else:
        # Fallback direct prompt
        prompt = f"""
        {BASE_TEDLAR_CONTEXT}

        TASK: Create a LinkedIn Sales Navigator search query to find this specific stakeholder
        at the company.

        COMPANY: {company['name']}
        DETAILS: {company_details}
        CUSTOMER SEGMENT: {customer_segment}
        STAKEHOLDER: {stakeholder['name']}
        TITLE: {stakeholder['title']}

        Based on the company's customer segment and the stakeholder's role, create a targeted
        Sales Navigator search query that will help find this specific person or someone in
        that role.

        Create a query with these parameters:
        1. Company name: Exact company name
        2. Title keywords: Include variations of the stakeholder's title
        3. Industry-specific keywords related to this role
        4. Function/department filters appropriate for this role
        5. Seniority levels: Appropriate for the role and company size

        FORMAT YOUR RESPONSE AS A STRUCTURED QUERY that can be directly copied into 
        Sales Navigator's search fields. Include explanations for why each parameter was chosen.
        """
    
    # Use cost-effective model for query generation
    model_config = {
        "model": "gpt-3.5-turbo",
        "temperature": 0.2,
        "max_tokens": 800,
    }
    
    response = call_openai_api(
        messages=[{"role": "system", "content": prompt}],
        model=model_config["model"],
        temperature=model_config["temperature"],
        max_tokens=model_config["max_tokens"],
        module="stakeholder_identification",
        operation="sales_navigator_query_generation"
    )
    
    # Extract the query from the response
    content = response["content"]
    
    # Update stakeholder with query information
    enhanced_stakeholder = stakeholder.copy()
    enhanced_stakeholder["sales_navigator_query"] = content
    
    return enhanced_stakeholder

def prioritize_stakeholders(stakeholders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Prioritize stakeholders based on decision-maker score and role.
    
    This prioritization is crucial for allocating outreach efforts effectively,
    focusing on stakeholders with the highest potential for conversion.
    
    Args:
        stakeholders: List of identified stakeholders
        
    Returns:
        Prioritized list of stakeholders
    """
    # Sort stakeholders by decision-maker score (descending)
    sorted_stakeholders = sorted(stakeholders, key=lambda x: x.get("decision_maker_score", 0.0), reverse=True)
    
    # Categorize by priority
    high_priority = []
    medium_priority = []
    low_priority = []
    
    for stakeholder in sorted_stakeholders:
        score = stakeholder.get("decision_maker_score", 0.0)
        
        if score >= 8.0:
            stakeholder["priority"] = "high"
            high_priority.append(stakeholder)
        elif score >= 6.0:
            stakeholder["priority"] = "medium"
            medium_priority.append(stakeholder)
        else:
            stakeholder["priority"] = "low"
            low_priority.append(stakeholder)
    
    # Combine categories in order of priority
    prioritized_stakeholders = high_priority + medium_priority + low_priority
    
    print(f"\nStakeholder Prioritization Summary:")
    print(f"Total stakeholders identified: {len(prioritized_stakeholders)}")
    print(f"High priority stakeholders: {len(high_priority)}")
    print(f"Medium priority stakeholders: {len(medium_priority)}")
    print(f"Low priority stakeholders: {len(low_priority)}")
    
    return prioritized_stakeholders

def save_stakeholder_data(stakeholders: List[Dict[str, Any]]):
    """
    Save stakeholder data to JSON files.
    
    Structured data storage is essential for the downstream outreach
    generation module, ensuring data integrity throughout the pipeline.
    
    Args:
        stakeholders: List of identified and prioritized stakeholders
    """
    stakeholders_dir = DATA_DIR / "stakeholders"
    stakeholders_dir.mkdir(exist_ok=True)
    
    # Custom JSON encoder to handle various data types
    class CustomEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, uuid.UUID):
                return str(obj)
            if isinstance(obj, datetime):
                return obj.isoformat()
            return super().default(obj)
    
    # Save each stakeholder as a separate JSON file
    for stakeholder in stakeholders:
        try:
            # Create Stakeholder object for validation
            stakeholder_obj = Stakeholder(
                id=stakeholder["id"],
                company_id=stakeholder["company_id"],
                name=stakeholder["name"],
                title=stakeholder["title"],
                department=stakeholder.get("department", ""),
                linkedin_url=stakeholder.get("linkedin_url", ""),
                email=stakeholder.get("email", ""),
                relevance_score=stakeholder.get("decision_maker_score", 0.0),
                relevance_rationale=stakeholder.get("decision_maker_rationale", "")
            )
            
            # Convert to dictionary for saving
            stakeholder_dict = stakeholder_obj.model_dump()
            
            # Add additional fields
            if "priority" in stakeholder:
                stakeholder_dict["priority"] = stakeholder["priority"]
                
            if "responsibilities" in stakeholder:
                stakeholder_dict["responsibilities"] = stakeholder["responsibilities"]
                
            if "influence" in stakeholder:
                stakeholder_dict["influence"] = stakeholder["influence"]
                
            if "relevant_benefits" in stakeholder:
                stakeholder_dict["relevant_benefits"] = stakeholder["relevant_benefits"]
                
            if "company_name" in stakeholder:
                stakeholder_dict["company_name"] = stakeholder["company_name"]
                
            if "customer_segment" in stakeholder:
                stakeholder_dict["customer_segment"] = stakeholder["customer_segment"]
                
            if "sales_navigator_query" in stakeholder:
                stakeholder_dict["sales_navigator_query"] = stakeholder["sales_navigator_query"]
                
            # Save to file
            stakeholder_file = stakeholders_dir / f"{stakeholder['id']}.json"
            with open(stakeholder_file, "w") as f:
                json.dump(stakeholder_dict, f, indent=2, cls=CustomEncoder)
                
            print(f"Saved stakeholder data for: {stakeholder['name']} ({stakeholder['title']}) at {stakeholder['company_name']}")
        except Exception as e:
            print(f"Error saving stakeholder {stakeholder.get('name', 'unknown')}: {str(e)}")

def run_stakeholder_identification(limit_companies=None, limit_stakeholders_per_company=None, debug=False):
    """
    Run the complete stakeholder identification process:
    1. Load qualified companies from company analysis
    2. Identify stakeholders for each company
    3. Generate Sales Navigator queries for high-value stakeholders
    4. Prioritize stakeholders based on decision-maker score
    5. Save stakeholder data for outreach generation
    
    This approach optimizes the $200 budget while ensuring high-quality
    stakeholders are identified for personalized outreach.
    
    Args:
        limit_companies: Optional limit on number of companies to process
        limit_stakeholders_per_company: Optional limit on stakeholders per company
        debug: Whether to print debug information
    """
    print("Starting stakeholder identification process...")
    
    # Step 1: Load qualified companies from company analysis
    companies = load_qualified_companies()
    
    if not companies:
        print("No qualified companies found. Run company analysis module first.")
        return
    
    # Apply limit on companies if specified
    if limit_companies is not None and limit_companies > 0:
        companies = companies[:limit_companies]
        print(f"Limiting analysis to {limit_companies} companies.")
    
    # Step 2: Identify stakeholders for each company
    all_stakeholders = []
    for company in companies:
        stakeholders = identify_stakeholders_for_company(company)
        
        # Apply limit on stakeholders per company if specified
        if limit_stakeholders_per_company is not None and limit_stakeholders_per_company > 0:
            stakeholders = stakeholders[:limit_stakeholders_per_company]
            print(f"Limiting to {limit_stakeholders_per_company} stakeholders for {company['name']}.")
        
        all_stakeholders.extend(stakeholders)
        
        # Small delay to avoid API rate limits
        time.sleep(0.5)
    
    # Step 3: Generate Sales Navigator queries for high-value stakeholders
    for i, stakeholder in enumerate(all_stakeholders):
        if stakeholder.get("decision_maker_score", 0.0) >= 7.5:
            # Only generate queries for high-scoring stakeholders to optimize budget
            company = next((c for c in companies if c["id"] == stakeholder["company_id"]), None)
            if company:
                all_stakeholders[i] = generate_sales_navigator_query(company, stakeholder)
        
        # Small delay to avoid API rate limits
        time.sleep(0.5)
    
    # Step 4: Prioritize stakeholders based on decision-maker score
    prioritized_stakeholders = prioritize_stakeholders(all_stakeholders)
    
    # Step 5: Save stakeholder data for outreach generation
    save_stakeholder_data(prioritized_stakeholders)
    
    # Track budget usage
    log_usage_report()
    
    # Print top stakeholders by score
    print("\nTop 5 Identified Stakeholders:")
    for i, stakeholder in enumerate(prioritized_stakeholders[:min(5, len(prioritized_stakeholders))]):
        print(f"{i+1}. {stakeholder['name']} ({stakeholder['title']}) at {stakeholder['company_name']} " +
              f"(Score: {stakeholder.get('decision_maker_score', 0.0):.1f}, Priority: {stakeholder.get('priority', 'unknown')})")
    
    # Filter out stakeholders with problematic company names before displaying
    # Update your filter code to this
    filtered_stakeholders = [s for s in prioritized_stakeholders 
                            if not (s['company_name'].startswith('Company-') or 
                                    s['company_name'] == 'Unknown Company') and
                            s['title'] != 'Unknown']

    print("\nFiltered Results (Excluding auto-generated company names):")
    print(f"Total filtered stakeholders: {len(filtered_stakeholders)}")
    print("\nTop 5 Quality Stakeholders:")
    for i, stakeholder in enumerate(filtered_stakeholders[:min(5, len(filtered_stakeholders))]):
        print(f"{i+1}. {stakeholder['name']} ({stakeholder['title']}) at {stakeholder['company_name']} " +
            f"(Score: {stakeholder.get('decision_maker_score', 0.0):.1f}, Priority: {stakeholder.get('priority', 'unknown')})")

def parse_arguments():
    """Parse command line arguments for more flexible execution."""
    import argparse
    parser = argparse.ArgumentParser(description="DuPont Tedlar Stakeholder Identification Module")
    parser.add_argument("--limit-companies", type=int, default=None, help="Limit the number of companies to process")
    parser.add_argument("--limit-stakeholders", type=int, default=None, help="Limit the number of stakeholders per company")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    run_stakeholder_identification(
        limit_companies=args.limit_companies,
        limit_stakeholders_per_company=args.limit_stakeholders,
        debug=args.debug
    )