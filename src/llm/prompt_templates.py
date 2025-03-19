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
import json

# Base context for all prompts - reduces redundant information in each prompt
BASE_TEDLAR_CONTEXT = f"""
You are assisting with lead generation for DuPont Tedlar's Graphics & Signage team.

PRODUCT INFORMATION:
DuPont Tedlar produces premium polyvinyl fluoride (PVF) protective films with over 60 years of technology development. 
These films extend the life of graphics applications in challenging environments by 5-7 years longer than standard laminates.

Key product lines include:
- Tedlar CLR: Clear protective overlaminates for maximum color clarity
- Tedlar TWH: White films for backlit signage applications
- Tedlar TMT: Matte finish films for glare reduction
- Tedlar TCW: Customizable width films for large format applications
- Tedlar TAW: Architectural grade films for building graphics

Key performance capabilities:
- Superior UV resistance (blocks >99% of damaging UV radiation)
- Exceptional color retention (<3 Delta E shift after 10 years)
- Chemical resistance to 300+ substances
- Temperature range from -70°F to 302°F
- Anti-delamination technology preventing edge lifting and peeling

IDEAL CUSTOMER SEGMENTS:
1. Large Format Print Providers ($5M-$50M revenue, 50-250 employees)
   - Pain points: Premature graphic failure, warranty claims, color fading
   - Decision makers: Operations Directors, Production Managers, R&D Directors

2. Fleet Graphics Specialists ($2M-$20M revenue, 25-100 employees)
   - Pain points: Graphics degradation in harsh transit conditions, fleet downtime
   - Decision makers: Fleet Graphics Directors, Product Development Managers

3. Architectural Graphics Manufacturers ($10M-$100M revenue, 100-500 employees)
   - Pain points: Extended warranties, installation complexity, material longevity
   - Decision makers: VP of Product Development, Materials Engineering Directors

4. Outdoor Advertising Companies ($20M-$500M revenue, 100-1,000 employees)
   - Pain points: Weather damage, maintenance costs, extended installation lifespans
   - Decision makers: Production Directors, Materials Procurement Managers

5. Sign Manufacturing Companies ($1M-$25M revenue, 20-150 employees)
   - Pain points: UV degradation, color consistency, delamination
   - Decision makers: Production Managers, Technical Directors

COMPETITIVE POSITIONING:
Despite being priced 15-30% higher than standard protective films, Tedlar delivers 30-40% lower lifetime costs
through superior durability, outperforming competitors like 3M Scotchcal, Avery Dennison MPI, and ORAFOL Oraguard
in accelerated weathering tests by 30-50%.

KEY INDUSTRY ASSOCIATIONS:
- International Sign Association (ISA): 2,300+ sign and graphics companies
- PRINTING United Alliance: 7,000+ companies across printing technologies
- FESPA: Global federation with strong European presence
- Society for Experiential Graphic Design (SEGD): Focus on architectural and wayfinding graphics
- National Association of Sign Supply Distributors (NASSD): Key distributors of sign materials
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

I already know about these major events, so don't include them in your analysis:
- ISA International Sign Expo 2024 (April 10-12, Orlando)
- PRINTING United Expo 2024 (September 10-12, Las Vegas)
- FESPA Global Print Expo 2024 (May 21-24, Amsterdam)
- Graphics Pro Expo 2024 (various regional US events)

Instead, focus on identifying 3-5 additional niche or specialized events that might have high concentrations of
Tedlar's specific target customer segments.

For each event, provide:
- Event name
- Date (if available)
- Location
- Brief description
- Website (if available)
- Why this event is relevant to Tedlar's target market
- Estimated relevance score (1-10)
- Which specific Tedlar customer segments would likely attend

FORMAT YOUR RESPONSE AS JSON with an array of event objects.
"""

EVENT_QUALIFICATION_PROMPT = f"""
{BASE_TEDLAR_CONTEXT}

TASK: Analyze the following event to determine its relevance for DuPont Tedlar lead generation.

EVENT DETAILS:
{{event_details}}

Evaluate this event on the following criteria:
1. Attendee alignment with Tedlar's specific customer segments (0-10)
   - Consider which of Tedlar's 6 target segments would attend and in what proportion
   - Estimate potential concentration of decision-makers like Production Directors or R&D leaders

2. Relevance to protective film use cases (0-10)
   - Evaluate connections to Tedlar's key applications: transit/fleet, architectural, outdoor signage, specialty
   - Consider if attendees face the specific pain points Tedlar addresses (UV degradation, chemical exposure, etc.)

3. Competitive environment (0-10)
   - Consider presence of competitors like 3M, Avery Dennison, and ORAFOL
   - Assess opportunity for Tedlar's differentiation (30-50% longer life, chemical resistance, etc.)

4. Lead generation potential (0-10)
   - Estimate number of qualified leads possible from this event
   - Consider quality of potential business conversations and networking opportunities

5. Overall event priority (0-10)
   - Provide a weighted final score
   - Recommend whether this should be a high, medium, or low priority event

For each criterion, provide a score AND a detailed justification with specific references to Tedlar's
product benefits, customer segments, and qualification factors.

FORMAT YOUR RESPONSE AS JSON with scores and detailed justifications.
"""

# COMPANY ANALYSIS PROMPTS

COMPANY_DISCOVERY_PROMPT = f"""
{BASE_TEDLAR_CONTEXT}

TASK: Identify companies likely to attend the following event that match 
DuPont Tedlar's ideal customer profile.

EVENT: {{event_name}}
DETAILS: {{event_details}}

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

COMPANY_QUALIFICATION_PROMPT = f"""
{BASE_TEDLAR_CONTEXT}

TASK: Perform an in-depth qualification analysis of the following company 
as a potential customer for DuPont Tedlar protective films.

COMPANY: {{company_name}}
DETAILS: {{company_details}}

Evaluate this company against our lead scoring criteria:
{LEAD_SCORING}

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

# STAKEHOLDER IDENTIFICATION PROMPTS

STAKEHOLDER_IDENTIFICATION_PROMPT = f"""
{BASE_TEDLAR_CONTEXT}

TASK: Identify key decision-makers at the following company who would be involved in 
purchasing protective films for graphics and signage applications.

COMPANY: {{company_name}}
DETAILS: {{company_details}}
CUSTOMER SEGMENT: {{customer_segment}}

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

FORMAT YOUR RESPONSE AS JSON with stakeholder details and decision-making assessment.
Include a priority ranking of which stakeholders to contact first.
"""

LINKEDIN_QUERY_TEMPLATE = f"""
{BASE_TEDLAR_CONTEXT}

TASK: Create a LinkedIn Sales Navigator search query to find decision-makers at 
the following company who would be interested in protective films for graphics applications.

COMPANY: {{company_name}}
DETAILS: {{company_details}}
CUSTOMER SEGMENT: {{customer_segment}}

Based on the company's customer segment, create targeted Sales Navigator search queries
that will find the exact decision-maker roles we need to reach.

Generate:

1. Primary search query for technical decision-makers:
   - Use the exact job titles from our customer segment research
   - Include industry-specific keywords related to materials, production, or R&D
   - Add function/department filters to narrow results
   - Include appropriate seniority levels (Director and above for larger companies)

2. Secondary search query for business approvers:
   - Focus on roles with purchasing or budget authority
   - Include procurement, operations, or business development keywords
   - Add appropriate seniority filters

For each query, provide:
- The exact Sales Navigator search syntax
- Explanation of why each parameter was chosen
- How to refine the search if it returns too many/few results

FORMAT YOUR RESPONSE AS STRUCTURED SEARCH QUERIES with explanations for each parameter.
"""

# OUTREACH GENERATION PROMPTS

OUTREACH_MESSAGE_PROMPT = f"""
{BASE_TEDLAR_CONTEXT}

TASK: Create a highly personalized outreach message to the following stakeholder 
at a qualified company, emphasizing Tedlar's value proposition for their specific needs.

STAKEHOLDER: {{stakeholder_name}}, {{stakeholder_title}}
COMPANY: {{company_name}}
COMPANY DETAILS: {{company_details}}
CUSTOMER SEGMENT: {{customer_segment}}
EVENT CONTEXT: {{event_name}}
QUALIFICATION RATIONALE: {{qualification_rationale}}

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

# Helper function to customize prompts with specific details
def customize_prompt(prompt_template: str, **kwargs) -> str:
    """
    Customize a prompt template with specific details.
    
    This function allows efficient reuse of prompt templates while
    inserting context-specific information.
    """
    # Add any missing keys that might be in the template
    if "'criteria'" in prompt_template or "{criteria}" in prompt_template:
        kwargs["criteria"] = json.dumps(LEAD_SCORING, indent=2)
    
    try:
        return prompt_template.format(**kwargs)
    except KeyError as e:
        print(f"Warning: Missing key in prompt template: {e}")
        # Add the missing key with a placeholder value
        key = str(e).strip("'")
        kwargs[key] = f"<{key} not provided>"
        return prompt_template.format(**kwargs)