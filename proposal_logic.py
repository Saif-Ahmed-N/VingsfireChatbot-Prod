def get_discount_for_company_size(company_size: str):
    """
    Calculates the discount percentage based on the company size.
    """
    if company_size in "0-10":
        return 0.40 # 40%
    if company_size in "10-100":
        return 0.25 # 25%
    if company_size == "100-500":
        return 0.15 # 15%
    if company_size == "500+":
        return 0.10 # 10%
    return 0.0 # Default to 0% discount

def safe_float(value):
    """Converts value to float, defaulting to 0.0 if value is None, empty, or non-numeric."""
    try:
        if value is None or (isinstance(value, str) and not value.strip()):
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def prepare_proposal_data(category_data, country_info, company_size):
    """
    Performs all business logic calculations for the proposal.
    - Applies discounts based on company size.
    - Converts INR costs to the local currency.
    - Calculates subtotal, discount, and final total.
    """
    exchange_rate = country_info['exchange_rate_from_inr']
    symbol = country_info['currency_symbol']
    discount_rate = get_discount_for_company_size(company_size)

    def convert_and_format(inr_amount):
        """Helper function to convert, format, and handle potential errors."""
        try:
            local_amount = float(inr_amount) * exchange_rate
            return f"{symbol}{local_amount:,.0f}"
        except Exception:
            return f"{symbol}0"

    # --- Use safe_float for all data retrieval to ensure numeric integrity ---
    
    # Convert all individual costs from the Excel row
    cost_breakdown = [
        {"item": "UI/UX Design", "cost": convert_and_format(safe_float(category_data.get('ui_ux_cost_inr')))},
        {"item": "Frontend Development", "cost": convert_and_format(safe_float(category_data.get('frontend_cost_inr')))},
        {"item": "Backend Development", "cost": convert_and_format(safe_float(category_data.get('backend_cost_inr')))},
        {"item": "Testing & QA", "cost": convert_and_format(safe_float(category_data.get('qa_cost_inr')))},
        {"item": "Project Management", "cost": convert_and_format(safe_float(category_data.get('pm_cost_inr')))},
        {"item": "Optional Add-ons", "cost": convert_and_format(safe_float(category_data.get('optional_addons_cost_inr')))}
    ]

    # Calculate subtotal, discount, and final total in the local currency
    try:
        base_cost_inr = safe_float(category_data.get('avg_cost_inr'))
        addons_cost_inr = safe_float(category_data.get('optional_addons_cost_inr'))

        subtotal_inr = base_cost_inr + addons_cost_inr
        subtotal_local = subtotal_inr * exchange_rate
        
        discount_local = subtotal_local * discount_rate
        final_total_local = subtotal_local - discount_local
    except Exception:
        subtotal_local, discount_local, final_total_local = 0, 0, 0

    return {
        "cost_breakdown": cost_breakdown,
        "subtotal_str": f"{symbol}{subtotal_local:,.0f}",
        "discount_rate_str": f"{discount_rate:.0%}",
        "discount_str": f"-{symbol}{discount_local:,.0f}",
        "final_total_str": f"{symbol}{final_total_local:,.0f}"
    }