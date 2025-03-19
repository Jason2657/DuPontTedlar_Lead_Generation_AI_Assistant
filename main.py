"""
DuPont Tedlar Lead Generation AI System
Main entry point for the application

This system helps DuPont Tedlar's Graphics & Signage team generate high-quality leads
by researching relevant industry events, identifying potential customers, locating
key decision-makers, and crafting personalized outreach messages.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from src.utils.cost_tracker import get_current_usage, log_usage_report
from config.config import DATA_DIR

def init_project():
    """
    Initialize project directories and files.
    
    Creates necessary data directories and initializes tracking files.
    """
    # Ensure data directories exist
    for data_dir in [
        DATA_DIR,
        DATA_DIR / "events",
        DATA_DIR / "companies",
        DATA_DIR / "stakeholders",
        DATA_DIR / "outreach",
        DATA_DIR / "usage_reports"
    ]:
        data_dir.mkdir(exist_ok=True)
    
    # Create token usage file if it doesn't exist
    token_usage_file = DATA_DIR / "token_usage.json"
    if not token_usage_file.exists():
        token_usage_file.touch()
    
    print("Project initialized successfully!")
    print(f"Data directory: {DATA_DIR}")

def show_project_status():
    """
    Display current project status.
    
    Shows token usage, budget status, and data processing progress.
    """
    # Get current usage
    usage = get_current_usage()
    
    print("\n===== PROJECT STATUS =====")
    print(f"Total cost so far: ${usage['total_cost_usd']:.2f}")
    print(f"Budget remaining: ${usage['budget_remaining_usd']:.2f}")
    print(f"Budget utilization: {usage['budget_used_percentage']:.2f}%")
    
    # Show module-specific budget status
    if "budget_allocation" in usage:
        print("\n===== BUDGET ALLOCATION =====")
        for module, status in usage["budget_allocation"].items():
            print(f"{module.title()}:")
            print(f"  Allocated: ${status['allocated_usd']:.2f}")
            print(f"  Spent: ${status['spent_usd']:.2f}")
            print(f"  Remaining: ${status['remaining_usd']:.2f}")
            print(f"  Utilization: {status['utilization_percentage']:.2f}%")
    
    # Count existing data
    event_count = len(list(Path(DATA_DIR / "events").glob("*.json")))
    company_count = len(list(Path(DATA_DIR / "companies").glob("*.json")))
    stakeholder_count = len(list(Path(DATA_DIR / "stakeholders").glob("*.json")))
    outreach_count = len(list(Path(DATA_DIR / "outreach").glob("*.json")))
    
    print("\n===== DATA STATUS =====")
    print(f"Events researched: {event_count}")
    print(f"Companies analyzed: {company_count}")
    print(f"Stakeholders identified: {stakeholder_count}")
    print(f"Outreach messages generated: {outreach_count}")
    
    print("\n===== NEXT STEPS =====")
    if event_count == 0:
        print("1. Research industry events (run python -m src.data_processing.event_research)")
    elif company_count == 0:
        print("1. Identify companies from events (run python -m src.data_processing.company_analysis)")
    elif stakeholder_count == 0:
        print("1. Identify stakeholders for companies (run python -m src.data_processing.stakeholder_identification)")
    elif outreach_count == 0:
        print("1. Generate outreach messages (run python -m src.outreach.message_generation)")
    else:
        print("1. Launch dashboard to view results (run streamlit run dashboard/app.py)")

if __name__ == "__main__":
    init_project()
    show_project_status()