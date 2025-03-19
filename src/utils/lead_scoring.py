"""
Lead Qualification Scoring System for DuPont Tedlar.

This module implements a multi-criteria scoring system to identify and prioritize
high-quality leads based on DuPont Tedlar's preference for conversion-focused leads.
"""

from typing import Dict, Any, List, Optional
from config.config import LEAD_SCORING

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

def generate_qualification_rationale(
    company_name: str,
    scores: Dict[str, float],
    justifications: Dict[str, str],
    use_cases: List[str],
    pain_points: List[str]
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
        
    Returns:
        Formatted qualification rationale
    """
    overall_score = calculate_lead_score(scores)
    priority = get_lead_priority(overall_score)
    
    # Format the rationale
    rationale = f"## Qualification Rationale for {company_name}\n\n"
    rationale += f"**Overall Score:** {overall_score}/10 ({priority.replace('_', ' ').title()})\n\n"
    
    rationale += "### Scoring Breakdown\n\n"
    for criterion, score in scores.items():
        criterion_name = criterion.replace('_', ' ').title()
        rationale += f"**{criterion_name}:** {score}/10\n"
        if criterion in justifications:
            rationale += f"- {justifications[criterion]}\n\n"
    
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
    
    # Add recommendation based on priority
    if priority == "exceptional":
        rationale += "**Recommendation:** High-priority target for immediate outreach. "
        rationale += "Use premium resources for personalized engagement."
    elif priority == "high_priority":
        rationale += "**Recommendation:** Strong prospect for focused outreach. "
        rationale += "Allocate resources for detailed personalization."
    elif priority == "qualified":
        rationale += "**Recommendation:** Qualified lead worth pursuing. "
        rationale += "Standard outreach approach recommended."
    else:
        rationale += "**Recommendation:** Below qualification threshold. "
        rationale += "Consider for awareness campaigns only."
    
    return rationale