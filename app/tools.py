def calculate_subsidy(farmer_type: str, equipment_cost: float, equipment_type: str) -> str:
    """
    Mock function calling tool for calculating subsidy based on TN Govt schemes.
    """
    farmer_type = farmer_type.lower()
    equipment_type = equipment_type.lower()
    
    if equipment_type == "tractor":
        if farmer_type in ["small", "marginal", "sc/st", "women"]:
            subsidy_percent = 0.50
        else:
            subsidy_percent = 0.40
        return f"For a {farmer_type} farmer buying a {equipment_type} costing Rs. {equipment_cost}, the expected subsidy is Rs. {equipment_cost * subsidy_percent} ({subsidy_percent*100}%)."
        
    elif equipment_type == "power tiller":
        if farmer_type in ["small", "marginal", "sc/st", "women"]:
            subsidy = min(equipment_cost * 0.50, 85000)
        else:
            subsidy = min(equipment_cost * 0.40, 70000)
        return f"For a {farmer_type} farmer buying a {equipment_type} costing Rs. {equipment_cost}, the expected subsidy is Rs. {subsidy} (Capped)."
        
    else:
        return "Subsidy information not available for this equipment type via calculator. Please check scheme documents."

# Dictionary mapping tool names to actual functions
AVAILABLE_TOOLS = {
    "calculate_subsidy": calculate_subsidy
}
