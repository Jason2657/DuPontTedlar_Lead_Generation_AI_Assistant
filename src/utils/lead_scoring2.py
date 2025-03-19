"""
Lead Qualification Scoring System for DuPont Tedlar. (Includes perplexity context info)

This module implements a multi-criteria scoring system to identify and prioritize
high-quality leads based on DuPont Tedlar's preference for conversion-focused leads.
"""

from typing import Dict, Any, List, Optional
from config.config import LEAD_SCORING, TEDLAR_CONTEXT

def calculate_lead_score(scores: Dict[str, float]) -> float:
    """
    Calculate weighted lead score based on multiple criteria.
    
    This weighted approach ensures that the most important factors
    (industry relevance and product fit) have greater influence on
    the final qualification score.
    
    Args:
        scores: Dictionary of criterion scores (0-10 scale)
        
    Returns:
        Weighted score on 0-10 scale
    """
    # Extract weights from configuration
    weights = {
        criterion: data["weight"] 
        for criterion, data in LEAD_SCORING["criteria"].items()
    }
    
    # Calculate weighted score
    weighted_score = 0.0
    total_weight_applied = 0.0
    
    for criterion, weight in weights.items():
        if criterion in scores:
            weighted_score += scores[criterion] * weight
            total_weight_applied += weight
    
    # Normalize if not all criteria were provided
    if total_weight_applied > 0:
        weighted_score = weighted_score / total_weight_applied * 10.0
    
    return round(weighted_score, 1)

def get_lead_priority(score: float) -> str:
    """
    Determine lead priority based on qualification score.
    
    This function determines how much attention and resource 
    should be allocated to a particular lead.
    
    Args:
        score: Lead qualification score (0-10)
        
    Returns:
        Priority level string
    """
    thresholds = LEAD_SCORING["thresholds"]
    
    if score >= thresholds["exceptional"]:
        return "exceptional"
    elif score >= thresholds["high_priority"]:
        return "high_priority"
    elif score >= thresholds["minimum_qualification"]:
        return "qualified"
    else:
        return "unqualified"

def should_use_premium_model(score: float) -> bool:
    """
    Determine if a premium LLM model should be used for this lead.
    
    This function helps optimize the $200 budget by reserving premium
    models for high-potential leads.
    
    Args:
        score: Lead qualification score (0-10)
        
    Returns:
        Boolean indicating whether to use premium model
    """
    # Use premium models only for high priority and exceptional leads
    return score >= LEAD_SCORING["thresholds"]["high_priority"]

def identify_customer_segment(company_description: str) -> str:
    """
    Identify which of Tedlar's customer segments a company belongs to.
    
    This function analyzes company description to match it with one of
    the six defined customer segments.
    
    Args:
        company_description: Text describing the company's business
        
    Returns:
        Name of the most likely customer segment
    """
    segments = TEDLAR_CONTEXT["target_customer_segments"]
    segment_keywords = {
        "Large Format Print Providers": ["large format", "print", "printing", "wide format", "banner"],
        "Fleet Graphics Specialists": ["fleet", "vehicle", "wrap", "automotive", "transit"],
        "Architectural Graphics Manufacturers": ["architectural", "building", "facade", "interior", "wayfinding"],
        "Outdoor Advertising Companies": ["billboard", "outdoor advertising", "signage", "out-of-home"],
        "Sign Manufacturing Companies": ["sign", "signage", "display", "visual communication"],
        "Material Distributors & Converters": ["distributor", "converter", "reseller", "supplier"]
    }
    
    # Count keyword matches for each segment
    match_counts = {segment: 0 for segment in segment_keywords}
    company_description_lower = company_description.lower()
    
    for segment, keywords in segment_keywords.items():
        for keyword in keywords:
            if keyword.lower() in company_description_lower:
                match_counts[segment] += 1
    
    # Find segment with highest match count
    best_segment = max(match_counts.items(), key=lambda x: x[1])
    
    # If no matches, return default
    if best_segment[1] == 0:
        return "Unknown"
    
    return best_segment[0]

def get_segment_decision_makers(segment: str) -> List[str]:
    """
    Get the typical decision-maker roles for a specific customer segment.
    
    Args:
        segment: Name of the customer segment
        
    Returns:
        List of typical decision-maker job titles for that segment
    """
    for segment_info in TEDLAR_CONTEXT["target_customer_segments"]:
        if segment_info["segment"] == segment:
            return segment_info["decision_makers"]
    
    # Default generic decision makers if segment not found
    return ["Production Manager", "Operations Director", "Purchasing Manager"]

def get_segment_pain_points(segment: str) -> List[str]:
    """
    Get the typical pain points for a specific customer segment.
    
    Args:
        segment: Name of the customer segment
        
    Returns:
        List of typical pain points for that segment
    """
    for segment_info in TEDLAR_CONTEXT["target_customer_segments"]:
        if segment_info["segment"] == segment:
            return segment_info["pain_points"]
    
    # Default generic pain points if segment not found
    return ["Premature graphic failure", "Warranty claims", "Color fading"]

def identify_relevant_product_lines(use_cases: List[str]) -> List[Dict[str, str]]:
    """
    Identify which Tedlar product lines are most relevant based on use cases.
    
    Args:
        use_cases: List of potential use cases for the lead
        
    Returns:
        List of relevant Tedlar product lines with descriptions
    """
    product_lines = TEDLAR_CONTEXT["product_lines"]
    use_cases_lower = [case.lower() for case in use_cases]
    
    relevant_products = []
    
    # Map keywords to product lines
    product_keywords = {
        "Tedlar CLR": ["clear", "transparency", "color", "visibility"],
        "Tedlar TWH": ["white", "backlit", "illuminated", "light", "bright"],
        "Tedlar TMT": ["matte", "glare", "reflection", "non-reflective"],
        "Tedlar TCW": ["wide", "large", "custom width", "oversized"],
        "Tedlar TAW": ["architectural", "building", "facade", "interior"]
    }
    
    for product in product_lines:
        for keyword in product_keywords.get(product["name"], []):
            if any(keyword in case for case in use_cases_lower):
                relevant_products.append(product)
                break
    
    # If no matches, return top 2 most versatile products
    if not relevant_products:
        return [product_lines[0], product_lines[2]]
    
    return relevant_products

def generate_qualification_rationale(
    company_name: str,
    scores: Dict[str, float],
    justifications: Dict[str, str],
    use_cases: List[str],
    pain_points: List[str],
    customer_segment: Optional[str] = None
) -> str:
    """
    Generate a detailed qualification rationale for a lead.
    
    This narrative explanation helps the sales team understand
    why a particular company is considered a good lead for Tedlar.
    
    Args:
        company_name: Name of the company
        scores: Dictionary of criterion scores
        justifications: Detailed justifications for each score
        use_cases: Potential use cases for Tedlar
        pain_points: Company pain points Tedlar can address
        customer_segment: Identified customer segment, if known
        
    Returns:
        Formatted qualification rationale
    """
    overall_score = calculate_lead_score(scores)
    priority = get_lead_priority(overall_score)
    
    # Identify customer segment if not provided
    if not customer_segment:
        company_desc = " ".join(justifications.values())
        customer_segment = identify_customer_segment(company_desc)
    
    # Get relevant product lines
    relevant_products = identify_relevant_product_lines(use_cases)
    
    # Format the rationale
    rationale = f"## Qualification Rationale for {company_name}\n\n"
    
    if customer_segment != "Unknown":
        rationale += f"**Customer Segment:** {customer_segment}\n"
    
    rationale += f"**Overall Score:** {overall_score}/10 ({priority.replace('_', ' ').title()})\n\n"
    
    rationale += "### Scoring Breakdown\n\n"
    for criterion, score in scores.items():
        criterion_name = criterion.replace('_', ' ').title()
        rationale += f"**{criterion_name}:** {score}/10\n"
        if criterion in justifications:
            rationale += f"- {justifications[criterion]}\n\n"
    
    # Include relevant product lines
    if relevant_products:
        rationale += "### Recommended Tedlar Products\n\n"
        for product in relevant_products:
            rationale += f"- **{product['name']}**: {product['description']}\n"
        rationale += "\n"
    
    if use_cases:
        rationale += "### Potential Use Cases\n\n"
        for use_case in use_cases:
            rationale += f"- {use_case}\n"
        rationale += "\n"
    
    if pain_points:
        rationale += "### Addressable Pain Points\n\n"
        for pain_point in pain_points:
            rationale += f"- {pain_point}\n"
        rationale += "\n"
    
    # Get typical decision-makers for this segment
    decision_makers = get_segment_decision_makers(customer_segment)
    if decision_makers:
        rationale += "### Target Decision Makers\n\n"
        for role in decision_makers:
            rationale += f"- {role}\n"
        rationale += "\n"
    
    # Add recommendation based on priority
    rationale += "### Recommendation\n\n"
    if priority == "exceptional":
        rationale += "**High-priority target for immediate outreach.** "
        rationale += f"Use premium resources for personalized engagement with specific focus on addressing {pain_points[0] if pain_points else 'key pain points'}. "
        rationale += f"Emphasize Tedlar's 30-40% lower lifetime costs despite premium pricing, with specific focus on the {relevant_products[0]['name']} product line."
    elif priority == "high_priority":
        rationale += "**Strong prospect for focused outreach.** "
        rationale += "Allocate resources for detailed personalization. "
        rationale += f"Focus messaging on {pain_points[0] if pain_points else 'industry challenges'} and Tedlar's proven performance advantages."
    elif priority == "qualified":
        rationale += "**Qualified lead worth pursuing.** "
        rationale += "Standard outreach approach recommended with segment-specific messaging. "
        rationale += f"Highlight Tedlar's benefits for {use_cases[0] if use_cases else 'relevant applications'}."
    else:
        rationale += "**Below qualification threshold.** "
        rationale += "Consider for awareness campaigns only or revisit if circumstances change."
    
    return rationale