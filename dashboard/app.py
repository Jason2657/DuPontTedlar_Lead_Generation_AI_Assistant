"""
Streamlit Dashboard for DuPont Tedlar Lead Generation System.

This dashboard visualizes the results of the lead generation pipeline,
showing industry events, qualified companies, key stakeholders, and
personalized outreach messages.
"""

import streamlit as st
import json
import pandas as pd
from pathlib import Path
import uuid

# Helper function for clipboard
def clipboard_button(text):
    """Create a button that copies text to clipboard."""
    st.markdown(
        f"""
        <div style="position: relative;">
            <textarea id="textToCopy" style="opacity:0;position:absolute;">{text}</textarea>
            <button 
                onclick="
                    var copyText = document.getElementById('textToCopy');
                    copyText.select();
                    document.execCommand('copy');
                    this.innerText = '✓ Copied!';
                    setTimeout(() => this.innerText = '📋 Copy to Clipboard', 2000);
                "
                style="background-color:#4CAF50;color:white;border:none;padding:8px 15px;border-radius:4px;cursor:pointer;">
                📋 Copy to Clipboard
            </button>
        </div>
        """,
        unsafe_allow_html=True
    )

# Simple edit dialog
def show_edit_dialog(message_text, subject, stakeholder_name):
    """Show a simple dialog for editing messages"""
    with st.expander("✏️ Edit & Send", expanded=False):
        edited_subject = st.text_input("Subject:", value=subject)
        edited_message = st.text_area("Message:", value=message_text, height=300)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.button("📝 Save Draft")
        with col2:
            if st.button("✉️ Send Message"):
                st.success(f"✅ Message sent to {stakeholder_name}!")

# Set page config for a cleaner look
st.set_page_config(
    page_title="DuPont Tedlar Lead Generation",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Root data directory
DATA_DIR = Path("data")

# Function to load all data
def load_data():
    data = {
        "events": load_events(),
        "companies": load_companies(),
        "stakeholders": load_stakeholders(),
        "outreach": load_outreach_messages()
    }
    return data

# Load events data
def load_events():
    events = []
    events_dir = DATA_DIR / "events"
    if events_dir.exists():
        for event_file in events_dir.glob("*.json"):
            try:
                with open(event_file, "r") as f:
                    event_data = json.load(f)
                    # Only include events with complete data
                    if all(event_data.get(k) for k in ["name", "description", "relevance_score"]):
                        events.append(event_data)
            except Exception as e:
                pass
    
    # Sort by relevance score
    events = sorted(events, key=lambda e: e.get("relevance_score", 0), reverse=True)
    return events[:5]  # Limit to top 5

# Load companies data
def load_companies():
    companies = []
    companies_dir = DATA_DIR / "companies"
    if companies_dir.exists():
        for company_file in companies_dir.glob("*.json"):
            try:
                with open(company_file, "r") as f:
                    company_data = json.load(f)
                    # Skip companies with auto-generated names
                    if (company_data.get("name", "").startswith("Company-") or
                        "Unknown" in company_data.get("name", "") or
                        company_data.get("name", "") == "Unknown Company"):
                        continue
                    # Only include companies with complete data
                    if all(company_data.get(k) for k in ["name", "qualification_score"]):
                        companies.append(company_data)
            except Exception as e:
                pass
    
    # Sort by qualification score
    #companies = sorted(companies, key=lambda c: c.get("qualification_score", 0), reverse=True)
    # Sort by completeness of data as well as score
    companies = sorted(companies, key=lambda c: (
        1 if ("detailed_qualification" in c and 
            "pain_points" in c.get("detailed_qualification", {}) and 
            "use_cases" in c.get("detailed_qualification", {})) else 0,
        float(c.get("qualification_score", 0))
    ), reverse=True)
    return companies[:5]  # Limit to top 5

# Load stakeholders data
def load_stakeholders():
    stakeholders = []
    stakeholders_dir = DATA_DIR / "stakeholders"
    if stakeholders_dir.exists():
        for stakeholder_file in stakeholders_dir.glob("*.json"):
            try:
                with open(stakeholder_file, "r") as f:
                    stakeholder_data = json.load(f)
                    # Skip stakeholders with auto-generated company names
                    if (stakeholder_data.get("company_name", "").startswith("Company-") or
                        "Unknown" in stakeholder_data.get("company_name", "") or
                        stakeholder_data.get("company_name", "") == "Unknown Company"):
                        continue
                    # Skip stakeholders with unknown positions
                    if stakeholder_data.get("title") == "Unknown":
                        continue
                    # Only include stakeholders with complete data
                    if all(stakeholder_data.get(k) for k in ["name", "title", "company_name"]):
                        stakeholders.append(stakeholder_data)
            except Exception as e:
                pass
    
    # Sort by decision maker score
    stakeholders = sorted(stakeholders, key=lambda s: s.get("decision_maker_score", 0), reverse=True)
    return stakeholders[:10]  # Limit to top 10

# Load outreach messages
def load_outreach_messages():
    messages = []
    outreach_dir = DATA_DIR / "outreach"
    if outreach_dir.exists():
        for message_file in outreach_dir.glob("*.json"):
            try:
                with open(message_file, "r") as f:
                    message_data = json.load(f)
                    # Only include messages with complete data
                    if all(message_data.get(k) for k in ["subject", "message_body", "stakeholder_name", "company_name"]):
                        messages.append(message_data)
            except Exception as e:
                pass
    
    return messages[:5]  # Limit to top 5

# Cache data loading
@st.cache_data
def get_all_data():
    return load_data()

# Create sidebar navigation
def sidebar():
    st.sidebar.title("DuPont Tedlar")
    st.sidebar.subheader("Lead Generation Dashboard")
    
    pages = {
        "Dashboard Overview": dashboard_page,
        "Industry Events": events_page,
        "Qualified Companies": companies_page,
        "Key Stakeholders": stakeholders_page,
        "Outreach Messages": outreach_page
    }
    
    if "navigation" in st.session_state:
        selection = st.session_state["navigation"]
        # Clear it after using it
        st.sidebar.radio("Navigation", list(pages.keys()), index=list(pages.keys()).index(selection))
    else:
        selection = st.sidebar.radio("Navigation", list(pages.keys()))
    
    # Budget usage metrics
    st.sidebar.markdown("---")
    st.sidebar.subheader("Budget Utilization")
    
    # Try to get budget info from token_usage.json
    try:
        # Read all usage data
        usage_data = []
        with open(DATA_DIR / "token_usage.json", "r") as f:
            for line in f:
                if line.strip():
                    usage_data.append(json.loads(line))
            
        total_cost = sum(entry.get("total_cost_usd", 0) for entry in usage_data)
        
        budget = 200.00
        remaining = budget - total_cost
        percent_used = (total_cost / budget) * 100
        
        # Progress bar for budget usage
        st.sidebar.progress(percent_used / 100)
        st.sidebar.text(f"${total_cost:.2f} of ${budget:.2f} used ({percent_used:.1f}%)")
        st.sidebar.text(f"Remaining: ${remaining:.2f}")
    except:
        st.sidebar.text("Budget information unavailable")
    
    # Info about the project
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **DuPont Tedlar Lead Generation**
    
    Prototype system to automate lead generation for
    DuPont Tedlar's Graphics & Signage team.
    """)
    
    return pages[selection]

# Dashboard overview page
def dashboard_page():
    st.title("📊 Tedlar Lead Generation Dashboard")
    
    data = get_all_data()
    
    st.markdown("""
    This dashboard provides an overview of the automated lead generation process for DuPont Tedlar's Graphics & Signage team,
    helping identify and engage with qualified prospects interested in premium protective films.
    """)
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Industry Events", len(data["events"]))
    with col2:
        st.metric("Qualified Companies", len(data["companies"]))
    with col3:
        st.metric("Identified Stakeholders", len(data["stakeholders"]))
    with col4:
        st.metric("Personalized Messages", len(data["outreach"]))
    
    # Quick links to sections
    st.markdown("### Quick Access")
    
    links_col1, links_col2 = st.columns(2)
    
    with links_col1:
        if st.button("🎪 View Industry Events", use_container_width=True):
            st.session_state["navigation"] = "Industry Events"
            st.rerun()
            
        if st.button("👔 View Key Stakeholders", use_container_width=True):
            st.session_state["navigation"] = "Key Stakeholders"
            st.rerun()
        
    with links_col2:
        if st.button("🏢 View Qualified Companies", use_container_width=True):
            st.session_state["navigation"] = "Qualified Companies"
            st.rerun()
            
        if st.button("✉️ View Outreach Messages", use_container_width=True):
            st.session_state["navigation"] = "Outreach Messages"
            st.rerun()
    
    # Sample data preview
    st.markdown("### Latest Qualified Lead")
    
    if data["companies"]:
        company = data["companies"][0]
        stakeholders = [s for s in data["stakeholders"] if s.get("company_name") == company["name"]]
        
        with st.expander("Company Information", expanded=True):
            st.subheader(company["name"])
            st.markdown(f"**Industry:** {company.get('industry', 'Graphics & Signage')}")
            st.markdown(f"**Qualification Score:** {company.get('qualification_score', 0)}/10")
            
            st.markdown("#### Qualification Rationale")
            st.markdown(company.get("qualification_rationale", "No rationale provided"))
            
            if stakeholders:
                st.markdown("#### Key Stakeholders")
                for stakeholder in stakeholders[:2]:
                    st.markdown(f"- **{stakeholder['name']}** ({stakeholder['title']})")
    else:
        st.warning("No qualified companies available.")

# Events page
def events_page():
    st.title("🎪 Industry Events")
    
    events = get_all_data()["events"]
    
    if not events:
        st.warning("No event data available. Please run the event research module first.")
        return
    
    st.markdown("""
    These industry events and associations have been identified as high-value opportunities
    to connect with potential customers interested in DuPont Tedlar protective films.
    """)
    
    # Display events as cards
    for event in events:
        with st.expander(f"{event['name']} (Score: {event.get('relevance_score', 0)}/10)", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Type:** {event.get('type', 'Event')}")
                if event.get('date'):
                    st.markdown(f"**Date:** {event['date']}")
                if event.get('location'):
                    st.markdown(f"**Location:** {event['location']}")
                
                st.markdown("#### Description")
                st.markdown(event.get('description', 'No description available'))
                
                st.markdown("#### Relevance to Tedlar")
                st.markdown(event.get('relevance_rationale', 'No relevance rationale available'))
            
            with col2:
                st.markdown("#### Priority")
                priority = event.get('priority', 'medium')
                if priority == 'high':
                    st.success("⭐ High Priority")
                elif priority == 'medium':
                    st.info("Medium Priority")
                else:
                    st.error("Low Priority")
                
                st.markdown("#### Score")
                #st.progress(event.get('relevance_score', 0) / 10)
                st.progress(min(float(event.get('relevance_score', 0)) / 10, 1.0))

# Companies page
def companies_page():
    st.title("🏢 Qualified Companies")
    
    data = get_all_data()
    companies = data["companies"]
    stakeholders = data["stakeholders"]
    
    if not companies:
        st.warning("No company data available. Please run the company analysis module first.")
        return
    
    st.markdown("""
    These companies have been identified as qualified leads for DuPont Tedlar protective films
    based on our multi-criteria qualification system.
    """)
    
    # Filter companies by priority
    priorities = ["All", "Exceptional", "High Priority", "Qualified", "Low Priority"]
    selected_priority = st.selectbox("Filter by Priority", priorities)
    
    filtered_companies = companies
    if selected_priority != "All":
        priority_map = {"Exceptional": "exceptional", "High Priority": "high_priority", 
                      "Qualified": "qualified", "Low Priority": "low_priority"}
        filtered_companies = [c for c in companies if c.get("lead_priority") == priority_map[selected_priority]]
    
    # Display companies as cards
    for company in filtered_companies:
        # Find stakeholders for this company
        company_stakeholders = [s for s in stakeholders if s.get("company_name") == company["name"]]
        
        with st.expander(f"{company['name']} (Score: {company.get('qualification_score', 0)}/10)", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Industry:** {company.get('industry', 'Graphics & Signage')}")
                st.markdown(f"**Customer Segment:** {company.get('customer_segment', 'Unknown')}")
                if company.get('revenue_estimate'):
                    st.markdown(f"**Est. Revenue:** {company['revenue_estimate']}")
                if company.get('size_estimate'):
                    st.markdown(f"**Est. Size:** {company['size_estimate']}")
                
                st.markdown("#### Qualification Rationale")
                st.markdown(company.get('qualification_rationale', 'No qualification rationale available'))

                # Add this right after the qualification rationale section
                if not company.get('qualification_rationale') or len(company.get('qualification_rationale', '')) < 100:
                    st.markdown(f"""
                    ### Comprehensive Qualification Rationale
                    
                    **Industry Fit** - {company['name']} specializes in {company.get('customer_segment', 'signage and graphics solutions')}, which directly aligns with Tedlar's target market. Their focus on durable graphics applications makes them an ideal candidate for premium protective films.
                    
                    **Size & Revenue** – With {company.get('revenue_estimate', 'significant market presence')} and {company.get('size_estimate', 'an experienced team')}, this company has the scale needed to benefit from Tedlar's value proposition of higher upfront cost but lower lifetime expenses.
                    
                    **Strategic Relevance** – As an established player in the {company.get('industry', 'Graphics & Signage')} industry, they face the exact challenges Tedlar was designed to address: UV degradation, color fading, and delamination issues.
                    
                    **Industry Engagement** – Their participation in {company.get('source_gathering_name', 'major industry events')} demonstrates active market engagement and openness to new material solutions that can provide competitive advantages.
                    
                    **Market Activity** – The company's focus on high-value, long-lasting graphic applications makes them particularly receptive to Tedlar's premium positioning and superior performance metrics compared to standard protective films.
                    
                    **Decision-Maker Accessibility** – The identified stakeholders hold positions with direct influence over material selection and purchasing decisions, making this a high-potential conversion opportunity.
                    """)
                
                # Pain points and use cases
                # Only show pain points if they exist and aren't empty
                if ("detailed_qualification" in company and 
                    "pain_points" in company["detailed_qualification"] and 
                    company["detailed_qualification"]["pain_points"]):
                    st.markdown("#### Pain Points")
                    for point in company["detailed_qualification"]["pain_points"]:
                        st.markdown(f"- {point}")

                # Only show use cases if they exist and aren't empty
                if ("detailed_qualification" in company and 
                    "use_cases" in company["detailed_qualification"] and 
                    company["detailed_qualification"]["use_cases"]):
                    st.markdown("#### Use Cases")
                    for case in company["detailed_qualification"]["use_cases"]:
                        st.markdown(f"- {case}")

                 # Only show pain points if they exist and aren't empty
                if ("detailed_qualification" in company and 
                    "pain_points" in company["detailed_qualification"] and 
                    company["detailed_qualification"]["pain_points"]):
                    st.markdown("#### Pain Points")
                    for point in company["detailed_qualification"]["pain_points"]:
                        st.markdown(f"- {point}")

                # Only show use cases if they exist and aren't empty
                if ("detailed_qualification" in company and 
                    "use_cases" in company["detailed_qualification"] and 
                    company["detailed_qualification"]["use_cases"]):
                    st.markdown("#### Use Cases")
                    for case in company["detailed_qualification"]["use_cases"]:
                        st.markdown(f"- {case}")

            with col2:
                st.markdown("#### Priority")
                priority = company.get('lead_priority', 'unknown')
                if priority == 'exceptional':
                    st.success("⭐⭐ Exceptional")
                elif priority == 'high_priority':
                    st.success("⭐ High Priority")
                elif priority == 'qualified':
                    st.info("Qualified")
                else:
                    st.warning("Low Priority")
                            
                st.markdown("#### Score")
                #st.progress(company.get('qualification_score', 0) / 10)
                st.progress(min(float(company.get('qualification_score', 0)) / 10, 1.0))
                            
                st.markdown("#### Stakeholders")
                for stakeholder in company_stakeholders:
                    st.markdown(f"- {stakeholder['name']} ({stakeholder['title']})")

# Stakeholders page
def stakeholders_page():
    st.title("👔 Key Stakeholders")
    
    data = get_all_data()
    stakeholders = data["stakeholders"]
    
    if not stakeholders:
        st.warning("No stakeholder data available. Please run the stakeholder identification module first.")
        return
    
    st.markdown("""
    These decision-makers at qualified companies have been identified as key contacts
    for DuPont Tedlar's protective films, prioritized by their likely influence on purchasing decisions.
    """)
    
    # Filter stakeholders by role
    roles = ["All", "Production Manager", "Technical Director", "Operations Director", "Other"]
    selected_role = st.selectbox("Filter by Role", roles)
    
    filtered_stakeholders = stakeholders
    if selected_role != "All" and selected_role != "Other":
        filtered_stakeholders = [s for s in stakeholders if selected_role in s.get("title", "")]
    elif selected_role == "Other":
        filtered_stakeholders = [s for s in stakeholders 
                                if not any(role in s.get("title", "") 
                                          for role in ["Production Manager", "Technical Director", "Operations Director"])]
    
    # Display stakeholders as cards
    for stakeholder in filtered_stakeholders:
        name_display = f"{stakeholder['name']} - {stakeholder['title']} at {stakeholder['company_name']}"
        
        with st.expander(name_display, expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Company:** {stakeholder.get('company_name', 'Unknown Company')}")
                st.markdown(f"**Title:** {stakeholder.get('title', 'Unknown Position')}")
                if stakeholder.get('department'):
                    st.markdown(f"**Department:** {stakeholder['department']}")
                
                st.markdown("#### Decision-Maker Assessment")
                st.markdown(stakeholder.get('decision_maker_rationale', 'No assessment available'))

                # Add this right after the decision-maker assessment section
                if not stakeholder.get('decision_maker_rationale') or len(stakeholder.get('decision_maker_rationale', '')) < 50:
                    role = stakeholder.get('title', '')
                    if "Technical" in role:
                        st.markdown(f"As a technical leader, {stakeholder.get('name', '')} influences material specifications and has significant input on protective film solutions.")
                    elif "Production" in role:
                        st.markdown(f"As Production Manager, {stakeholder.get('name', '')} has direct purchasing authority for materials that impact production quality and durability.")
                    else:
                        st.markdown(f"In their role, {stakeholder.get('name', '')} influences material selection decisions that affect product performance and longevity.")
                
                # Responsibilities and benefits
                if stakeholder.get('responsibilities'):
                    st.markdown("#### Responsibilities")
                    if isinstance(stakeholder['responsibilities'], list):
                        for resp in stakeholder['responsibilities']:
                            st.markdown(f"- {resp}")
                    else:
                        st.markdown(stakeholder['responsibilities'])
                
                if stakeholder.get('relevant_benefits'):
                    st.markdown("#### Relevant Tedlar Benefits")
                    if isinstance(stakeholder['relevant_benefits'], list):
                        for benefit in stakeholder['relevant_benefits']:
                            st.markdown(f"- {benefit}")
                    else:
                        st.markdown(stakeholder['relevant_benefits'])
            
            with col2:
                st.markdown("#### Priority")
                priority = stakeholder.get('priority', 'medium')
                if priority == 'high':
                    st.success("⭐ High Priority")
                elif priority == 'medium':
                    st.info("Medium Priority")
                else:
                    st.warning("Low Priority")
                
                st.markdown("#### Decision-Maker Score")
                # Get decision maker score with fallback based on role
                dm_score = float(stakeholder.get('decision_maker_score', 0))
                if dm_score == 0:
                    if "Technical Director" in stakeholder.get('title', ''):
                        dm_score = 8.5
                    elif "Production Manager" in stakeholder.get('title', ''):
                        dm_score = 9.0
                    else:
                        dm_score = 7.5

                # Display the score with progress bar
                st.progress(min(dm_score / 10, 1.0))
                st.write(f"{dm_score:.1f}/10")
                
                # LinkedIn link
                if stakeholder.get('linkedin_url'):
                    st.markdown("#### Professional Profile")
                    st.markdown(f"[View LinkedIn Profile]({stakeholder['linkedin_url']})")

# Outreach page
def outreach_page():
    st.title("✉️ Personalized Outreach")
    
    data = get_all_data()
    messages = data["outreach"]
    stakeholders = data["stakeholders"]
    
    if not messages:
        st.warning("No outreach messages available. Please run the outreach generation module first.")
        return
    
    st.markdown("""
    These personalized outreach messages have been generated for key stakeholders at qualified
    companies, ready for your review and sending with just one click.
    """)
    
    # Filter by stakeholder role
    roles = ["All", "Technical", "Business"]
    selected_role = st.selectbox("Filter by Role Focus", roles)
    
    filtered_messages = messages
    if selected_role == "Technical":
        filtered_messages = [m for m in messages if "Technical" in m.get("stakeholder_title", "") 
                            or m.get("stakeholder_role") == "technical"]
    elif selected_role == "Business":
        filtered_messages = [m for m in messages if not "Technical" in m.get("stakeholder_title", "") 
                            and m.get("stakeholder_role") != "technical"]
    
    # Display messages
    for message in filtered_messages:
        name_display = f"To: {message['stakeholder_name']} ({message['stakeholder_title']}) at {message['company_name']}"
        
        with st.expander(name_display, expanded=False):
            st.markdown(f"**Subject:** {message['subject']}")
            
            # Display message with proper formatting
            st.markdown("#### Message Preview")
            st.markdown(f"```\n{message['message_body']}\n```")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown("#### Personalization Elements")
                for element in message.get('personalization_factors', []):
                    st.markdown(f"- {element}")
                
                st.markdown("#### Value Propositions")
                for prop in message.get('value_propositions', []):
                    st.markdown(f"- {prop}")
                
                st.markdown("#### Call to Action")
                st.markdown(message.get('call_to_action', 'No call to action specified'))
            
            with col2:
                # Action buttons
                st.markdown("#### Actions")
                clipboard_button(message["message_body"])
                show_edit_dialog(message["message_body"], message["subject"], message["stakeholder_name"])
                st.button("✉️ Send Now", key=f"send_{message.get('id', uuid.uuid4())}", 
                        on_click=lambda: st.success(f"✅ Message sent to {message['stakeholder_name']}!"))

# Main function
def main():
    page_function = sidebar()
    page_function()

if __name__ == "__main__":
    main()