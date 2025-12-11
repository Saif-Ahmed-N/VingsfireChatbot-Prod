def get_discount_for_company_size(company_size: str):
    if company_size in "0-10": return 0.40
    if company_size in "10-100": return 0.25
    if company_size == "100-500": return 0.15
    if company_size == "500+": return 0.10
    return 0.0

def safe_float(value):
    try:
        if value is None or (isinstance(value, str) and not value.strip()): return 0.0
        return float(value)
    except (ValueError, TypeError): return 0.0

def prepare_proposal_data(category_data, country_info, company_size):
    exchange_rate = country_info['exchange_rate_from_inr']
    symbol = country_info['currency_symbol']
    discount_rate = get_discount_for_company_size(company_size)

    def convert_and_format(inr_amount):
        try:
            local_amount = float(inr_amount) * exchange_rate
            return f"{symbol}{local_amount:,.0f}"
        except Exception: return f"{symbol}0"

    cost_components_inr = {
        "UI/UX Design": safe_float(category_data.get('ui_ux_cost_inr')),
        "Frontend Development": safe_float(category_data.get('frontend_cost_inr')),
        "Backend Development": safe_float(category_data.get('backend_cost_inr')),
        "Testing & QA": safe_float(category_data.get('qa_cost_inr')),
        "Project Management": safe_float(category_data.get('pm_cost_inr'))
    }
    optional_addons_inr = safe_float(category_data.get('optional_addons_cost_inr'))

    # --- CRITICAL BUG FIX: ALWAYS CALCULATE SUBTOTAL FROM COMPONENTS ---
    subtotal_inr = sum(cost_components_inr.values()) + optional_addons_inr

    cost_breakdown = [
        {"item": name, "cost": convert_and_format(cost)} for name, cost in cost_components_inr.items()
    ]
    cost_breakdown.append({"item": "Optional Add-ons", "cost": convert_and_format(optional_addons_inr)})

    try:
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