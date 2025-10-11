from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List

import os
from datetime import datetime
import phonenumbers
from email_validator import validate_email, EmailNotValidError
import sys

from excel_handler import load_service_data
from country_data import countries
from proposal_logic import prepare_proposal_data
from llm_handler import generate_descriptive_text, get_general_response, estimate_custom_service_cost
from pdf_writer import create_proposal_pdf, create_lead_summary_pdf
from mongo_handler import save_lead, update_lead_details
from utils import send_email_with_attachment

app = FastAPI(
    title="Infinite Tech AI Proposal API",
    description="API for the chatbot to handle conversations and generate proposals.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://vingsfire-chatbot-prod.vercel.app",  # Your Vercel frontend
        # Add your other WordPress site URLs here if needed
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

services_data, main_services, sub_categories_others, app_sub_category_definitions = load_service_data()
if not services_data:
    raise RuntimeError("FATAL: Could not load service data.")

BACK_COMMAND = "__GO_BACK__"

class ChatRequest(BaseModel):
    stage: str
    user_details: Dict[str, Any]
    user_input: str | None = None

class ChatResponse(BaseModel):
    next_stage: str
    bot_message: str
    user_details: Dict[str, Any]
    ui_elements: Dict[str, Any] | None = None

class ProposalRequest(BaseModel):
    user_details: Dict[str, Any]
    category: str
    custom_category_name: str | None = None
    custom_category_data: Dict[str, Any] | None = None

def generate_local_budget_options(country_info):
    base_budgets_inr = [(100000, 400000), (500000, 800000), (800000, 1000000), (1000000, None)]
    exchange_rate = country_info['exchange_rate_from_inr']
    symbol = country_info['currency_symbol']
    options = []
    for low, high in base_budgets_inr:
        low_local = low * exchange_rate
        if high:
            high_local = high * exchange_rate
            options.append(f"{symbol}{low_local:,.0f} - {symbol}{high_local:,.0f}")
        else:
            options.append(f"{symbol}{low_local:,.0f}+")
    return options

def generate_and_send_proposal_task(user_details, category, custom_category_name, custom_category_data):
    try:
        # --- PART 1: SEND PROPOSAL TO CLIENT ---
        print("--- CLIENT PROPOSAL PROCESS STARTED ---")
        if custom_category_name and custom_category_data:
            data_source = custom_category_data
            user_details['category'] = custom_category_name
        else:
            main_service = user_details['main_service']
            sub_cat = user_details.get('sub_category', '_default')
            data_source = services_data[main_service][sub_cat][category]
        user_details['contact'] = user_details.get('phone', 'N/A')
        update_lead_details(user_details["email"], user_details)
        country_info = countries[user_details['country']]
        proposal_costs = prepare_proposal_data(data_source, country_info, user_details['company_size'])
        proposal_text = generate_descriptive_text(data_source, user_details.get('category'))
        if not proposal_text: raise ValueError("AI failed to generate text.")
        output_dir = "proposals"; os.makedirs(output_dir, exist_ok=True)
        project_name_slug = user_details['category'].replace(' ', '_').replace('/', '_')
        client_pdf_filename = f"{user_details['company'].replace(' ', '_')}_{project_name_slug}_{datetime.now().strftime('%Y%m%d')}.pdf"
        client_pdf_path = os.path.join(output_dir, client_pdf_filename)
        create_proposal_pdf(user_details, proposal_text, proposal_costs, country_info, client_pdf_path)
        send_email_with_attachment(
            receiver_email=user_details['email'],
            subject=f"Your Personalized Proposal from Infinite Tech for {user_details['category']}",
            body=f"Dear {user_details['name']},\n\nAs requested, please find your detailed project proposal attached.\n\nBest Regards,\nThe Infinite Tech Team",
            attachment_path=client_pdf_path
        )
        print(f"--- CLIENT PROPOSAL SENT to {user_details['email']} ---")

        # --- PART 2: SEND LEAD NOTIFICATION TO SALES ---
        print("--- SALES NOTIFICATION PROCESS STARTED ---")
        sales_email = "partha@infinitetechai.com"
        sales_pdf_filename = f"Lead_Summary_{user_details['company'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        sales_pdf_path = os.path.join(output_dir, sales_pdf_filename)
        create_lead_summary_pdf(user_details, sales_pdf_path)
        send_email_with_attachment(
            receiver_email=sales_email,
            subject=f"New Chatbot Lead: {user_details.get('company', 'N/A')} - {user_details.get('category', 'N/A')}",
            body=f"A new lead has been generated by the chatbot. Please find the summary attached.",
            attachment_path=sales_pdf_path
        )
        print(f"--- SALES NOTIFICATION SENT to {sales_email} ---")
    except Exception as e:
        print(f"--- BACKGROUND TASK FAILED: ERROR in background proposal task: {e} ---"); sys.stdout.flush()

def go_back_to_stage(previous_stage: str, user_details: Dict[str, Any]) -> ChatResponse:
    if previous_stage == "get_name": user_details.pop('name', None); return ChatResponse(next_stage="get_name", bot_message="Hello! I am the Infinite Tech AI assistant. To get started, please tell me your full name.", user_details=user_details)
    elif previous_stage == "initial_choice": return ChatResponse(next_stage="initial_choice", bot_message=f"Welcome, {user_details.get('name', 'there')}! How can I help you today?", user_details=user_details, ui_elements={"type": "buttons", "display_style": "pills", "options": ["Explore Products or Services", "Looking for a Job"]})
    elif previous_stage == "get_email": user_details.pop('email', None); return ChatResponse(next_stage="get_email", bot_message="What is your email address?", user_details=user_details)
    elif previous_stage == "get_phone": user_details.pop('phone', None); user_details.pop('country', None); return ChatResponse(next_stage="get_phone", bot_message="Please re-enter your country and contact phone number.", user_details=user_details, ui_elements={"type": "form", "form_type": "phone", "options": list(countries.keys())})
    elif previous_stage == "get_company": user_details.pop('company', None); return ChatResponse(next_stage="get_company", bot_message="What is your company's name?", user_details=user_details)
    elif previous_stage == "get_company_size": user_details.pop('company_size', None); return ChatResponse(next_stage="get_company_size", bot_message="What is the size of your company?", user_details=user_details, ui_elements={"type": "dropdown", "options": ["0-10", "10-100", "100-500", "500+"]})
    elif previous_stage == "get_budget":
        user_details.pop('budget', None); country_info = countries[user_details['country']]; budget_options = generate_local_budget_options(country_info)
        return ChatResponse(next_stage="get_budget", bot_message=f"What is your approximate budget for this project in your local currency ({country_info['currency_code']})?", user_details=user_details, ui_elements={"type": "buttons", "display_style": "pills", "options": budget_options})
    elif previous_stage == "get_main_service": user_details.pop('main_service', None); return ChatResponse(next_stage="get_main_service", bot_message="Which of our main services are you interested in?", user_details=user_details, ui_elements={"type": "buttons", "display_style": "cards", "options": main_services})
    elif previous_stage == "get_sub_category":
        user_details.pop('sub_category', None); main_service = user_details['main_service']
        if main_service == "App Development": return ChatResponse(next_stage="get_sub_category", bot_message="Please select the category that best fits your app idea.", user_details=user_details, ui_elements={"type": "buttons", "display_style": "cards", "options": list(app_sub_category_definitions.keys())})
        else: return ChatResponse(next_stage="get_main_service", bot_message="Which of our main services are you interested in?", user_details=user_details, ui_elements={"type": "buttons", "display_style": "cards", "options": main_services})
    elif previous_stage == "get_specific_service":
        user_details.pop('category', None); user_details.pop('custom_category_name', None)
        main_service = user_details['main_service']; sub_cat = user_details.get('sub_category', '_default')
        if main_service == "App Development": options = app_sub_category_definitions.get(sub_cat, []) + ["Others"]
        else: options = list(services_data.get(main_service, {}).get(sub_cat, {}).keys()) + ["Others"]
        return ChatResponse(next_stage="get_specific_service", bot_message=f"Which specific type of {sub_cat} are you looking for?", user_details=user_details, ui_elements={"type": "buttons", "display_style": "pills", "options": options})
    return ChatResponse(next_stage=previous_stage, bot_message="Cannot go back further.", user_details=user_details)

@app.post("/chat", response_model=ChatResponse)
async def handle_chat(request: ChatRequest):
    stage, user_details, user_input = request.stage, request.user_details, (request.user_input.strip() if request.user_input else "")
    if 'stage_history' not in user_details: user_details['stage_history'] = []
    user_input_lower = user_input.lower()
    if user_input == BACK_COMMAND:
        if user_details['stage_history']: return go_back_to_stage(user_details['stage_history'].pop(), user_details)
        else: return ChatResponse(next_stage=stage, bot_message="I can't go back any further.", user_details=user_details)
    if "new proposal" in user_input_lower and user_details.get('name'):
        user_details = {'name': user_details['name'], 'stage_history': []}
        return ChatResponse(next_stage="initial_choice", bot_message=f"Of course, {user_details['name']}! Let's start a new proposal.", user_details=user_details, ui_elements={"type": "buttons", "display_style": "pills", "options": ["Explore Products or Services", "Looking for a Job"]})
    if stage in ["general_chat", "final_generation"] and any(p in user_input_lower for p in ['connect', 'talk to']): return ChatResponse(next_stage='general_chat', bot_message="Of course. You can reach our team at **partha@infinitetechai.com**.", user_details=user_details)
    if stage not in ['ended', 'general_chat', 'final_generation', 'get_name']: user_details['stage_history'].append(stage)
    if stage == "get_name":
        user_details['name'] = user_input
        return ChatResponse(next_stage="initial_choice", bot_message=f"Welcome, {user_input}! How can I help?", user_details=user_details, ui_elements={"type": "buttons", "display_style": "pills", "options": ["Explore Products or Services", "Looking for a Job"]})
    elif stage == "initial_choice":
        if user_input == "Explore Products or Services": return ChatResponse(next_stage="get_email", bot_message="Great! What is your email address?", user_details=user_details)
        elif user_input == "Looking for a Job": return ChatResponse(next_stage="job_application", bot_message="You can reach our HR team at `partha@infinitetechai.com` or upload your CV below.", user_details=user_details, ui_elements={"type": "file_upload"})
    elif stage == "get_email":
        try:
            valid = validate_email(user_input, check_deliverability=False); user_details['email'] = valid.email
            return ChatResponse(next_stage="get_phone", bot_message="Thank you. Please select your country and enter your phone number.", user_details=user_details, ui_elements={"type": "form", "form_type": "phone", "options": list(countries.keys())})
        except EmailNotValidError: return ChatResponse(next_stage="get_email", bot_message="That email seems invalid. Please try again.", user_details=user_details)
    elif stage == "get_phone":
        try:
            country, phone_num = user_input.split(":", 1); country_info = countries[country]
            parsed_number = phonenumbers.parse(phone_num, country_info['iso_code'])
            if not phonenumbers.is_valid_number(parsed_number): raise ValueError("Invalid number.")
            user_details.update({'phone': phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164), 'country': country}); save_lead(user_details)
            return ChatResponse(next_stage="get_company", bot_message="Perfect. What is your company's name?", user_details=user_details)
        except Exception: return ChatResponse(next_stage="get_phone", bot_message="That phone number seems invalid. Please try again.", user_details=user_details, ui_elements={"type": "form", "form_type": "phone", "options": list(countries.keys())})
    elif stage == "get_company":
        user_details['company'] = user_input
        return ChatResponse(next_stage="get_company_size", bot_message="Got it. What's the size of your company?", user_details=user_details, ui_elements={"type": "dropdown", "options": ["0-10", "10-100", "100-500", "500+"]})
    elif stage == "get_company_size":
        user_details['company_size'] = user_input; country_info = countries[user_details['country']]
        return ChatResponse(next_stage="get_budget", bot_message=f"Thank you. What's your approximate budget in {country_info['currency_code']}?", user_details=user_details, ui_elements={"type": "buttons", "display_style": "pills", "options": generate_local_budget_options(country_info)})
    elif stage == "get_budget":
        user_details['budget'] = user_input
        return ChatResponse(next_stage="get_main_service", bot_message="Understood. Which of our main services are you interested in?", user_details=user_details, ui_elements={"type": "buttons", "display_style": "cards", "options": main_services})
    elif stage == "get_main_service":
        user_details['main_service'] = user_input
        if user_input == "App Development": return ChatResponse(next_stage="get_sub_category", bot_message="Great. Please select the category that best fits your app idea.", user_details=user_details, ui_elements={"type": "buttons", "display_style": "cards", "options": list(app_sub_category_definitions.keys())})
        elif user_input in sub_categories_others: return ChatResponse(next_stage="get_sub_category", bot_message="Please select a more specific category.", user_details=user_details, ui_elements={"type": "buttons", "display_style": "cards", "options": sub_categories_others[user_input]})
        else:
            options = list(services_data.get(user_input, {}).get('_default', {}).keys()) + ["Others"]
            return ChatResponse(next_stage="get_specific_service", bot_message=f"Excellent. Which specific type of {user_input} do you need?", user_details=user_details, ui_elements={"type": "buttons", "display_style": "cards", "options": options})
    elif stage == "get_sub_category":
        user_details['sub_category'] = user_input; main_service = user_details['main_service']
        if main_service == "App Development": options = app_sub_category_definitions.get(user_input, []) + ["Others"]
        else: options = list(services_data.get(main_service, {}).get(user_input, {}).keys()) + ["Others"]
        return ChatResponse(next_stage="get_specific_service", bot_message=f"Perfect. Which specific type of {user_input} are you looking for?", user_details=user_details, ui_elements={"type": "buttons", "display_style": "pills", "options": options})
    elif stage == "get_specific_service":
        user_details['category'] = user_input
        main_service, sub_cat = user_details['main_service'], user_details.get('sub_category', '_default')
        category_exists = user_input in services_data.get(main_service, {}).get(sub_cat, {})
        if user_input == "Others" or not category_exists:
            if not category_exists: user_details.update({'custom_category_name': user_input, 'category': "Custom Service"})
            return ChatResponse(next_stage="get_other_service_name", bot_message=f"I don't have a standard estimate for **{user_input}**. Please briefly describe the application you need, and I'll prepare a custom estimate.", user_details=user_details)
        else: return ChatResponse(next_stage="get_optional_features", bot_message="Perfect. Are there any specific features to add? (Optional, you can skip)", user_details=user_details)
    elif stage == "get_other_service_name":
        if 'custom_category_name' not in user_details: user_details['custom_category_name'] = user_input
        main_service = user_details['main_service']
        all_examples = [item for sub in services_data.get(main_service, {}).values() for item in sub.values()]
        ai_estimate = estimate_custom_service_cost(user_details['custom_category_name'], main_service, all_examples)
        if ai_estimate: return ChatResponse(next_stage="get_optional_features", bot_message="I've prepared a preliminary estimate. Any other specific features to add? (Optional)", user_details=user_details, ui_elements={"type": "store_data", "data": ai_estimate})
        else: return ChatResponse(next_stage="get_specific_service", bot_message="I'm sorry, I couldn't generate an estimate. Please try rephrasing or select an option.", user_details=user_details)
    elif stage == "get_optional_features":
        user_details['description'] = user_input or "No additional features requested."
        project_name = user_details.get('custom_category_name', user_details.get('category'))
        additional_info = f"\n- **Additional Details:** {user_details['description']}" if user_details.get('description') and user_details['description'] != "No additional features requested." else ""
        summary = f"Please confirm your details:\n- **Email:** {user_details['email']}\n- **Phone:** {user_details['phone']}\n- **Company:** {user_details['company']}\n- **Project:** {project_name}{additional_info}\n\nShall I generate and email the full proposal now?"
        return ChatResponse(next_stage="confirm_proposal", bot_message=summary, user_details=user_details, ui_elements={"type": "buttons", "display_style": "pills", "options": ["Yes, Send Proposal", "No, I Have Questions"]})
    elif stage == "confirm_proposal":
        if user_input_lower == "yes, send proposal": return ChatResponse(next_stage="final_generation", bot_message="Excellent. Generating your proposal now...", user_details=user_details)
        else: return ChatResponse(next_stage="general_chat", bot_message="No problem. How else can I help?", user_details=user_details)
    elif stage in ["general_chat", "final_generation", "job_application"]:
        if stage == "job_application" and user_input.startswith("Uploaded:"):
            bot_message = "Thank you for uploading your resume. Our HR team will review it and get in touch if there is a suitable opening. Is there anything else I can help with?"
            return ChatResponse(next_stage="general_chat", bot_message=bot_message, user_details=user_details)
        if any(p in user_input_lower for p in ['where is my', 'get the proposal', 'send it']): return ChatResponse(next_stage="general_chat", bot_message="Your proposal was sent to your email. Please check your inbox and spam folder.", user_details=user_details)
        if any(p in user_input_lower for p in ['no', 'bye', 'goodbye']): return ChatResponse(next_stage="ended", bot_message="You're welcome! Have a great day.", user_details=user_details)
        answer = get_general_response(user_input)
        return ChatResponse(next_stage="general_chat", bot_message=answer, user_details=user_details)
    raise HTTPException(status_code=400, detail=f"Invalid chat stage: {stage}")

@app.post("/generate-proposal", status_code=202)
async def create_proposal(request: ProposalRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(generate_and_send_proposal_task, request.user_details, request.category, request.custom_category_name, request.custom_category_data)
    return {"message": "Proposal generation accepted."}