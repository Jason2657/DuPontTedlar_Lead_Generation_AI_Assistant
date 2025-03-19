"""
Token Usage and Cost Tracking for DuPont Tedlar Lead Generation.

This module tracks and analyzes LLM token usage to optimize the $200 budget
allocation across the lead generation pipeline.
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from config.config import DATA_DIR, BUDGET_ALLOCATION

# Token usage file path
TOKEN_USAGE_FILE = DATA_DIR / "token_usage.json"

def get_current_usage() -> Dict[str, Any]:
    """
    Calculate current token usage and cost across the pipeline.
    
    This function provides visibility into budget utilization, helping
    to ensure we allocate resources appropriately across the workflow.
    
    Returns:
        Dictionary with usage statistics and remaining budget
    """
    if not TOKEN_USAGE_FILE.exists():
        return {
            "total_cost_usd": 0.0,
            "budget_used_percentage": 0.0,
            "budget_remaining_usd": 200.0,
            "usage_by_model": {},
            "usage_by_module": {}
        }
    
    # Read token usage records
    with open(TOKEN_USAGE_FILE, "r") as f:
        usage_records = [json.loads(line) for line in f if line.strip()]
    
    if not usage_records:
        return {
            "total_cost_usd": 0.0,
            "budget_used_percentage": 0.0,
            "budget_remaining_usd": 200.0,
            "usage_by_model": {},
            "usage_by_module": {}
        }
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(usage_records)
    
    # Calculate total cost
    total_cost = df["total_cost_usd"].sum()
    budget_remaining = 200.0 - total_cost
    budget_used_percentage = (total_cost / 200.0) * 100
    
    # Group by model
    model_usage = df.groupby("model").agg({
        "prompt_tokens": "sum",
        "completion_tokens": "sum",
        "total_tokens": "sum",
        "total_cost_usd": "sum"
    }).to_dict("index")
    
    # Group by module
    module_usage = df.groupby("module").agg({
        "total_tokens": "sum",
        "total_cost_usd": "sum"
    }).to_dict("index")
    
    # Calculate budget allocation vs actual
    module_budget_allocation = {
        module: 200.0 * percentage 
        for module, percentage in BUDGET_ALLOCATION.items()
        if module != "buffer"
    }
    
    module_budget_status = {}
    for module, allocation in module_budget_allocation.items():
        actual_spend = module_usage.get(module, {}).get("total_cost_usd", 0.0)
        module_budget_status[module] = {
            "allocated_usd": allocation,
            "spent_usd": actual_spend,
            "remaining_usd": allocation - actual_spend,
            "utilization_percentage": (actual_spend / allocation) * 100 if allocation > 0 else 0.0
        }
    
    return {
        "total_cost_usd": total_cost,
        "budget_used_percentage": budget_used_percentage,
        "budget_remaining_usd": budget_remaining,
        "usage_by_model": model_usage,
        "usage_by_module": module_usage,
        "budget_allocation": module_budget_status
    }

def log_usage_report() -> Dict[str, Any]:
    """
    Generate and save a detailed usage report.
    
    This function creates a snapshot of current budget utilization,
    helping to track spending and optimize remaining budget.
    
    Returns:
        Dictionary with the usage report data
    """
    current_usage = get_current_usage()
    
    # Create report with timestamp
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_cost_usd": current_usage["total_cost_usd"],
        "budget_remaining_usd": current_usage["budget_remaining_usd"],
        "budget_used_percentage": current_usage["budget_used_percentage"],
        "usage_by_model": current_usage["usage_by_model"],
        "usage_by_module": current_usage["usage_by_module"],
        "budget_allocation": current_usage["budget_allocation"]
    }
    
    # Save report
    reports_dir = DATA_DIR / "usage_reports"
    reports_dir.mkdir(exist_ok=True)
    
    report_file = reports_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    return report

def is_budget_available(module: str, estimated_cost: float) -> bool:
    """
    Check if sufficient budget is available for an operation.
    
    This function helps prevent budget overruns by checking if a
    planned operation fits within remaining allocations.
    
    Args:
        module: Pipeline module requesting budget
        estimated_cost: Estimated cost of the operation
        
    Returns:
        Boolean indicating whether budget is available
    """
    current_usage = get_current_usage()
    
    # Get module allocation and spending
    module_budget = 200.0 * BUDGET_ALLOCATION.get(module, 0.0)
    module_spent = current_usage["usage_by_module"].get(module, {}).get("total_cost_usd", 0.0)
    
    # Check if module has sufficient remaining budget
    if module_spent + estimated_cost <= module_budget:
        return True
    
    # If module budget exceeded, check buffer
    buffer_allocation = 200.0 * BUDGET_ALLOCATION.get("buffer", 0.0)
    buffer_used = current_usage["total_cost_usd"] - sum([
        current_usage["usage_by_module"].get(m, {}).get("total_cost_usd", 0.0)
        for m in BUDGET_ALLOCATION.keys()
        if m != "buffer"
    ])
    
    # Check if buffer has sufficient remaining budget
    buffer_remaining = buffer_allocation - buffer_used
    return buffer_remaining >= estimated_cost