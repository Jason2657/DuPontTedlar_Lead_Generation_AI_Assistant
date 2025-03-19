"""
Prompt Templates for DuPont Tedlar Lead Generation System.

This module contains carefully designed prompt templates for each stage of the
lead generation pipeline, optimized for:
1. Token efficiency
2. High-quality reasoning
3. Consistent output formatting
4. Tedlar-specific context
"""

from config.config import TEDLAR_CONTEXT, LEAD_SCORING

# Base context for all prompts - reduces redundant information in each prompt
BASE_TEDLAR_CONTEXT = f"""
You are assisting with lead generation for DuPont Tedlar's Graphics & Signage team. 
Tedlar produces high-performance protective films that provide exceptional durability, 
UV protection, and weather resistance for graphics, signage, and architectural applications.

Key benefits of Tedlar protective films:
- Superior protection against UV degradation
- Excellent chemical resistance
- Extended graphic and color life
- Protection against environmental damage
- Enhanced durability in outdoor applications

Target industries include: graphics & signage, large format printing, architectural graphics,
vehicle wraps, and outdoor advertising.

The ideal customer profile includes companies that:
- Manufacture or distribute graphics products
- Produce signage or large format printing
- Supply materials for architectural applications
- Experience challenges with premature graphic fading
- Need extended durability for their products
- Have significant production volume

Example qualified customer: Avery Dennison Graphics Solutions
"""

# EVENT RESEARCH PROMPTS

EVENT_DISCOVERY_PROMPT = f"""
{BASE_TEDLAR_CONTEXT}

TASK: Identify the most relevant upcoming industry events where DuPont Tedlar's target customers 
are likely to attend.

Focus on events related to:
1. Graphics and signage industry
2. Protective films applications
3. Large format printing
4. Architectural graphics
5. Vehicle wraps and fleet graphics

For each event, provide:
- Event name
- Date (if available)
- Location
- Brief description
- Website (if available)
- Why this event is relevant to Tedlar's target market
- Estimated relevance score (1-10)

FORMAT YOUR RESPONSE AS JSON with an array of event objects.
"""

EVENT_QUALIFICATION_PROMPT = f"""
{BASE_TEDLAR_CONTEXT}

TASK: Analyze the following event to determine its relevance for DuPont Tedlar lead generation.

EVENT DETAILS:
{{event_details}}

Evaluate this event on the following criteria:
1. Attendee alignment with Tedlar's target industries (0-10)
2. Likelihood of decision-makers being present (0-10)
3. Relevance to protective film applications (0-10)
4. Potential for meaningful business conversations (0-10)
5. Overall lead generation potential (0-10)

For each criterion, provide a score AND a detailed justification.
Conclude with an overall relevance score (weighted average) and final recommendation.

FORMAT YOUR RESPONSE AS JSON with scores and detailed justifications.
"""

# COMPANY ANALYSIS PROMPTS

COMPANY_DISCOVERY_PROMPT = f"""
{BASE_TEDLAR_CONTEXT}

TASK: Identify companies likely to attend the following event that match 
DuPont Tedlar's ideal customer profile.

EVENT: {{event_name}}
DETAILS: {{event_details}}

For each potential company, provide:
- Company name
- Industry focus
- Brief description
- Why they might attend this event
- How they might use Tedlar protective films
- Initial qualification score (1-10)

Focus on quality over quantity. Identify 5-8 companies that are most likely to be 
strong prospects for Tedlar's protective films.

FORMAT YOUR RESPONSE AS JSON with an array of company objects.
"""

COMPANY_QUALIFICATION_PROMPT = f"""
{BASE_TEDLAR_CONTEXT}

TASK: Perform an in-depth qualification analysis of the following company 
as a potential customer for DuPont Tedlar protective films.

COMPANY: {{company_name}}
DETAILS: {{company_details}}

Evaluate this company against our lead scoring criteria:
{LEAD_SCORING}

For each criterion:
1. Assign a score (0-10)
2. Provide detailed justification
3. Identify specific use cases for Tedlar
4. Outline potential pain points that Tedlar can address

Calculate a weighted qualification score and provide a detailed qualification rationale.
Focus on conversion potential rather than general awareness.

FORMAT YOUR RESPONSE AS JSON with scores, justifications, and detailed analysis.
"""

# STAKEHOLDER IDENTIFICATION PROMPTS

STAKEHOLDER_IDENTIFICATION_PROMPT = f"""
{BASE_TEDLAR_CONTEXT}

TASK: Identify key decision-makers at the following company who would be involved in 
purchasing protective films for graphics and signage applications.

COMPANY: {{company_name}}
DETAILS: {{company_details}}

For each potential stakeholder:
1. Identify likely job title and department
2. Assess their potential role in purchasing decisions
3. Explain why they would care about Tedlar's benefits
4. Assign a decision-maker score (1-10)
5. Provide a detailed rationale for this score

Focus on 1-2 high-value stakeholders rather than an exhaustive list.
Consider both technical decision-makers and financial/business approvers.

FORMAT YOUR RESPONSE AS JSON with stakeholder details and decision-making assessment.
"""

LINKEDIN_QUERY_TEMPLATE = f"""
{BASE_TEDLAR_CONTEXT}

TASK: Create a LinkedIn Sales Navigator search query to find decision-makers at 
the following company who would be interested in protective films for graphics applications.

COMPANY: {{company_name}}
DETAILS: {{company_details}}

Generate:
1. Job title keywords to target
2. Department/function filters
3. Seniority levels to include
4. Industry specializations to look for
5. A structured query for Sales Navigator's search syntax

FORMAT YOUR RESPONSE AS A STRUCTURED SEARCH QUERY with explanations for each parameter.
"""

# OUTREACH GENERATION PROMPTS

OUTREACH_MESSAGE_PROMPT = f"""
{BASE_TEDLAR_CONTEXT}

TASK: Create a highly personalized outreach message to the following stakeholder 
at a qualified company, emphasizing Tedlar's value proposition for their specific needs.

STAKEHOLDER: {{stakeholder_name}}, {{stakeholder_title}}
COMPANY: {{company_name}}
COMPANY DETAILS: {{company_details}}
EVENT CONTEXT: {{event_name}}
QUALIFICATION RATIONALE: {{qualification_rationale}}

Your message should:
1. Reference the industry event as a conversation starter
2. Highlight specific Tedlar benefits relevant to their pain points
3. Include 2-3 tailored value propositions
4. Suggest a specific next step (call to action)
5. Be concise, professional, and conversion-focused

Focus on value and specificity rather than generic benefits.
The message should feel researched and personalized, not mass-produced.

FORMAT YOUR RESPONSE WITH:
- Email subject line
- Message body
- List of personalization elements used
"""

# Helper function to customize prompts with specific details
def customize_prompt(prompt_template: str, **kwargs) -> str:
    """
    Customize a prompt template with specific details.
    
    This function allows efficient reuse of prompt templates while
    inserting context-specific information.
    """
    return prompt_template.format(**kwargs)