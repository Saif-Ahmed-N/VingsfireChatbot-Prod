# backend/main.py

from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
import shutil
import os
from datetime import datetime
import phonenumbers
from email_validator import validate_email, EmailNotValidError
import sys
import re # Added for Regex patterns

# Internal imports
from excel_handler import load_service_data
from country_data import countries
from proposal_logic import prepare_proposal_data
from llm_handler import generate_descriptive_text, get_general_response, estimate_custom_service_cost
from pdf_writer import create_proposal_pdf, create_sales_lead_pdf
from mongo_handler import save_lead, update_lead_details, update_lead_with_resume
from utils import send_email_with_attachment

app = FastAPI(title="Infinite Tech AI Agent", version="3.5.0 (Enterprise)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- LOAD DATA ---
services_data, main_services, sub_categories_others, app_sub_category_definitions = load_service_data()
if not services_data: raise RuntimeError("FATAL: Could not load service data.")

BACK_COMMAND = "__GO_BACK__"
SALES_TEAM_EMAIL = "partha@infinitetechai.com"

# --- MODELS ---
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

# --- UTILITIES ---
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

def sanitize_filename(name):
    return "".join([c if c.isalnum() else "_" for c in name])

# --- BACKGROUND TASK ---
def generate_and_send_proposal_task(user_details, category, custom_category_name, custom_category_data):
    try:
        # 1. Determine Data Source
        if custom_category_name and custom_category_data:
            data_source = custom_category_data
            user_details['category'] = custom_category_name
        else:
            main_service = user_details['main_service']
            sub_cat = user_details.get('sub_category', '_default')
            try: data_source = services_data[main_service][sub_cat][category]
            except KeyError: data_source = {"cost": 0, "description": "Custom Requirement"}

        # 2. Update Database
        user_details['contact'] = user_details.get('phone', 'N/A')
        update_lead_details(user_details["email"], user_details)
        
        # 3. Calculations
        country_info = countries[user_details['country']]
        proposal_costs = prepare_proposal_data(data_source, country_info, user_details['company_size'])
        proposal_text = generate_descriptive_text(data_source, user_details.get('category'))
        if not proposal_text: proposal_text = {"introduction": f"Proposal for {user_details.get('category')}"}
        
        # 4. File Generation
        output_dir = "proposals"; os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        project_slug = sanitize_filename(user_details.get('custom_category_name', user_details['category']))
        
        client_pdf_path = os.path.join(output_dir, f"{sanitize_filename(user_details['company'])}_{project_slug}_{timestamp}_client.pdf")
        create_proposal_pdf(user_details, proposal_text, proposal_costs, country_info, client_pdf_path)
        
        # 5. Email Client
        send_email_with_attachment(
            receiver_email=user_details['email'],
            subject=f"Project Proposal: {user_details.get('custom_category_name', user_details['category'])} | Infinite Tech",
            body=f"Dear {user_details['name']},\n\nThank you for choosing Infinite Tech. Based on your requirements, we have prepared a detailed project proposal tailored to your needs.\n\nPlease find the document attached.\n\nBest Regards,\nThe Infinite Tech Team",
            attachment_path=client_pdf_path
        )

        # 6. Sales Lead
        sales_pdf_path = os.path.join(output_dir, f"{sanitize_filename(user_details['company'])}_{project_slug}_{timestamp}_sales.pdf")
        create_sales_lead_pdf(user_details, proposal_costs, sales_pdf_path)
        
        send_email_with_attachment(
            receiver_email=SALES_TEAM_EMAIL,
            subject=f"🔥 HOT LEAD: {user_details['company']} - {user_details.get('category')}",
            body=f"New Proposal Generated.\nClient: {user_details['name']}\nEmail: {user_details['email']}\nPhone: {user_details['phone']}\n\nSee full summary attached.",
            attachment_path=sales_pdf_path
        )
    except Exception as e:
        print(f"Background Task Critical Failure: {e}")

# --- BACK & RESET LOGIC ---
def go_back_to_stage(previous_stage: str, user_details: Dict[str, Any]) -> ChatResponse:
    # Intelligent re-prompting logic
    if previous_stage == "get_name":
        user_details.pop('name', None)
        return ChatResponse(next_stage="get_name", bot_message="Let's restart. May I have your **Full Name**?", user_details=user_details)
    elif previous_stage == "initial_choice":
        return ChatResponse(next_stage="initial_choice", bot_message=f"Welcome back, **{user_details.get('name')}**. How can we assist you?", user_details=user_details, ui_elements={"type": "buttons", "display_style": "pills", "options": ["Explore Services", "Career Opportunities"]})
    elif previous_stage == "get_email":
        return ChatResponse(next_stage="get_email", bot_message="Please enter your **Business Email Address**.", user_details=user_details)
    elif previous_stage == "get_phone":
        return ChatResponse(next_stage="get_phone", bot_message="Please confirm your **Mobile Number**.", user_details=user_details, ui_elements={"type": "form", "form_type": "phone", "options": list(countries.keys())})
    elif previous_stage == "get_company":
        return ChatResponse(next_stage="get_company", bot_message="What is the name of your **Company**?", user_details=user_details)
    
    return ChatResponse(next_stage=previous_stage, bot_message="Returning to previous step...", user_details=user_details)

# --- MAIN CHAT HANDLER ---
@app.post("/chat", response_model=ChatResponse)
async def handle_chat(request: ChatRequest):
    stage, user_details, user_input = request.stage, request.user_details, (request.user_input.strip() if request.user_input else "")
    if 'stage_history' not in user_details: user_details['stage_history'] = []
    user_input_lower = user_input.lower()

    # --- 1. HANDLE HIDDEN START COMMAND (Friendly Welcome) ---
    if user_input_lower == "new proposal":
        user_details = {'stage_history': []}
        return ChatResponse(
            next_stage="get_name", 
            # FIXED: Friendly welcome message instead of "System reset"
            bot_message="Hello! Welcome to **Infinite Tech**. To get started, please tell me your **Full Name**.", 
            user_details=user_details
        )

    # --- 2. HANDLE USER INTERRUPTS (Manual Reset) ---
    if user_input_lower in ["restart", "reset", "start over"]:
        user_details = {'stage_history': []}
        return ChatResponse(
            next_stage="get_name", 
            bot_message="System reset. Let's start fresh. May I have your **Full Name**?", 
            user_details=user_details
        )
    
    if user_input_lower in ["help", "support", "agent"]:
        return ChatResponse(next_stage=stage, bot_message="I am an AI agent designed to generate proposals. If you need human assistance, please email **support@infinitetech.in**.", user_details=user_details)

    # Handle Back Button
    if user_input == BACK_COMMAND:
        if user_details['stage_history']: return go_back_to_stage(user_details['stage_history'].pop(), user_details)
        else: return ChatResponse(next_stage=stage, bot_message="We are at the beginning of the conversation.", user_details=user_details)

    # History Tracking
    if stage not in ['ended', 'general_chat', 'final_generation', 'get_name', 'confirm_proposal', 'post_engagement']: 
        if not user_details['stage_history'] or user_details['stage_history'][-1] != stage:
             user_details['stage_history'].append(stage)

    # --- 3. CONVERSATION STAGES ---

    if stage == "get_name":
        # Check if user accidentally typed "new proposal" or just hit enter
        if len(user_input) < 2 or user_input_lower == "new proposal":
             return ChatResponse(next_stage="get_name", bot_message="Could you please provide your **Full Name**?", user_details=user_details)
        
        user_details['name'] = user_input
        return ChatResponse(
            next_stage="initial_choice", 
            bot_message=f"Pleasure to meet you, **{user_input}**. I am the Infinite Tech AI. How may I assist you today?", 
            user_details=user_details, 
            ui_elements={"type": "buttons", "display_style": "pills", "options": ["Explore Services", "Career Opportunities"]}
        )

    elif stage == "initial_choice":
        if "Service" in user_input: 
            return ChatResponse(next_stage="get_email", bot_message="Excellent choice. To generate a custom proposal, I first need your **Business Email Address**.", user_details=user_details)
        elif "Career" in user_input: 
            return ChatResponse(next_stage="get_email_for_job", bot_message="We are always looking for exceptional talent. Please provide your **Email Address** to start the application.", user_details=user_details)
        else:
            # Fallback for "gibberish" or unrecognized input
            return ChatResponse(next_stage="initial_choice", bot_message="I didn't catch that. Please select one of the options below.", user_details=user_details, ui_elements={"type": "buttons", "display_style": "pills", "options": ["Explore Services", "Career Opportunities"]})

    # --- STRICT EMAIL VALIDATION ---
    elif stage == "get_email":
        try:
            valid = validate_email(user_input, check_deliverability=False)
            user_details['email'] = valid.email
            return ChatResponse(next_stage="get_phone", bot_message="Thank you. Now, please select your **Country** and enter your **Mobile Number**.", user_details=user_details, ui_elements={"type": "form", "form_type": "phone", "options": list(countries.keys())})
        except EmailNotValidError:
            # Polite Re-ask Loop
            return ChatResponse(next_stage="get_email", bot_message="I apologize, but that email format seems incorrect. Please enter a valid **name@company.com** address.", user_details=user_details)

    elif stage == "get_email_for_job":
        try:
            valid = validate_email(user_input, check_deliverability=False); user_details['email'] = valid.email
            return ChatResponse(next_stage="job_application", bot_message="Perfect. Please **upload your Resume/CV** (PDF or Docx).", user_details=user_details, ui_elements={"type": "file_upload", "upload_to": "/upload-resume", "user_email": user_details['email']})
        except: return ChatResponse(next_stage="get_email_for_job", bot_message="Please provide a valid **Email Address** for our HR team.", user_details=user_details)

    # --- STRICT PHONE VALIDATION ---
    elif stage == "get_phone":
        try:
            if ":" not in user_input: raise ValueError
            c, p = user_input.split(":", 1)
            # Remove spaces/dashes
            p_clean = p.replace(" ", "").replace("-", "")
            if len(p_clean) < 7 or not p_clean.isdigit(): raise ValueError
            
            user_details.update({'phone': p, 'country': c})
            save_lead(user_details)
            return ChatResponse(next_stage="get_company", bot_message="Details saved. What is the name of your **Company or Organization**?", user_details=user_details)
        except:
            return ChatResponse(next_stage="get_phone", bot_message="That phone number appears invalid. Please ensure you select your **Country** and enter a numeric **Mobile Number**.", user_details=user_details, ui_elements={"type": "form", "form_type": "phone", "options": list(countries.keys())})

    elif stage == "get_company":
        if len(user_input) < 2: return ChatResponse(next_stage="get_company", bot_message="Could you please provide the full **Company Name**?", user_details=user_details)
        user_details['company'] = user_input
        return ChatResponse(next_stage="get_company_size", bot_message="Noted. What is your current **Team Size**?", user_details=user_details, ui_elements={"type": "dropdown", "options": ["1-10", "11-50", "51-200", "200+"]})

    elif stage == "get_company_size":
        user_details['company_size'] = user_input
        ci = countries.get(user_details['country'], countries['India'])
        return ChatResponse(next_stage="get_budget", bot_message=f"What is your estimated **Project Budget** ({ci['currency_code']})?", user_details=user_details, ui_elements={"type": "buttons", "display_style": "pills", "options": generate_local_budget_options(ci)})

    elif stage == "get_budget":
        user_details['budget'] = user_input
        return ChatResponse(next_stage="get_main_service", bot_message="Which **Service Category** are you interested in?", user_details=user_details, ui_elements={"type": "buttons", "display_style": "cards", "options": main_services})

    # --- SERVICE SELECTION LOGIC ---
    elif stage == "get_main_service":
        user_details['main_service'] = user_input
        if user_input == "App Development": 
            return ChatResponse(next_stage="get_sub_category", bot_message="Please specify the **App Platform**.", user_details=user_details, ui_elements={"type": "buttons", "display_style": "cards", "options": list(app_sub_category_definitions.keys())})
        elif user_input in sub_categories_others: 
            return ChatResponse(next_stage="get_sub_category", bot_message="Please select a **Specific Category**.", user_details=user_details, ui_elements={"type": "buttons", "display_style": "cards", "options": sub_categories_others[user_input]})
        elif user_input in services_data:
            opts = list(services_data.get(user_input, {}).get('_default', {}).keys()) + ["Other Requirement"]
            return ChatResponse(next_stage="get_specific_service", bot_message="Please select the **Service Type**.", user_details=user_details, ui_elements={"type": "buttons", "display_style": "cards", "options": opts})
        else:
             # Robust Fallback
             return ChatResponse(next_stage="get_main_service", bot_message="Please select one of the available services.", user_details=user_details, ui_elements={"type": "buttons", "display_style": "cards", "options": main_services})

    elif stage == "get_sub_category":
        user_details['sub_category'] = user_input; ms = user_details['main_service']
        if ms == "App Development": opts = app_sub_category_definitions.get(user_input, []) + ["Other Requirement"]
        else: opts = list(services_data.get(ms, {}).get(user_input, {}).keys()) + ["Other Requirement"]
        return ChatResponse(next_stage="get_specific_service", bot_message="Please refine your selection.", user_details=user_details, ui_elements={"type": "buttons", "display_style": "pills", "options": opts})

    elif stage == "get_specific_service":
        if "Other" in user_input:
            user_details['category'] = "Others"; return ChatResponse(next_stage="get_other_service_name", bot_message="Please briefly **describe your specific requirement**.", user_details=user_details)
        user_details['category'] = user_input; user_details.pop('custom_category_name', None)
        return ChatResponse(next_stage="get_optional_features", bot_message="Are there any **Specific Features** or integrations you need?", user_details=user_details)

    elif stage == "get_other_service_name":
        user_details['custom_category_name'] = user_input
        return ChatResponse(next_stage="get_optional_features", bot_message="Understood. Any **additional requirements**?", user_details=user_details)

    elif stage == "get_optional_features":
        user_details['description'] = user_input
        summary = f"**Proposal Ready**\n\n• **Service:** {user_details.get('custom_category_name', user_details.get('category'))}\n• **Budget:** {user_details.get('budget')}\n• **Email:** {user_details['email']}\n\nShall I generate the PDF now?"
        return ChatResponse(next_stage="confirm_proposal", bot_message=summary, user_details=user_details, ui_elements={"type": "buttons", "display_style": "pills", "options": ["Yes, Generate Proposal", "No, Cancel"]})

    elif stage == "confirm_proposal":
        if "Yes" in user_input:
            return ChatResponse(next_stage="final_generation", bot_message="Processing your request. Please wait...", user_details=user_details)
        elif "No" in user_input:
            return ChatResponse(next_stage="post_engagement", bot_message="Request cancelled. Is there anything else I can help you with?", user_details=user_details, ui_elements={"type": "buttons", "options": ["Create New Proposal", "Contact Support"]})
        else:
            return ChatResponse(next_stage="confirm_proposal", bot_message="Please confirm: Shall I generate the proposal?", user_details=user_details, ui_elements={"type": "buttons", "options": ["Yes, Generate Proposal", "No, Cancel"]})

    elif stage == "final_generation":
        # Note: This message is fetched BEFORE the PDF is done in the background.
        # Ideally, frontend waits for the "202 Accepted" then this triggers.
        # But we want the "Continuous Flow".
        return ChatResponse(
            next_stage="post_engagement", 
            bot_message="**Success!** Your proposal has been sent to your email.\n\nWhile you wait, would you like to explore more?", 
            user_details=user_details,
            ui_elements={"type": "buttons", "options": ["Create Another Proposal", "Visit Website", "Contact Sales"]}
        )

    # --- 3. CONTINUOUS ENGAGEMENT (The Loop) ---
    elif stage == "post_engagement":
        if "Create" in user_input:
             # Loop back to start (skip name)
             user_details['stage_history'] = []
             return ChatResponse(next_stage="initial_choice", bot_message=f"Certainly, **{user_details.get('name')}**. What service are you looking for this time?", user_details=user_details, ui_elements={"type": "buttons", "display_style": "pills", "options": ["Explore Services", "Career Opportunities"]})
        elif "Visit" in user_input:
             return ChatResponse(next_stage="post_engagement", bot_message="You can visit us at **infinitetechai.com**.", user_details=user_details, ui_elements={"type": "buttons", "options": ["Create Another Proposal", "Contact Sales"]})
        elif "Sales" in user_input or "Support" in user_input:
             return ChatResponse(next_stage="post_engagement", bot_message="You can reach our sales team at **sales@infinitetech.in** or +91 9884777171.", user_details=user_details, ui_elements={"type": "buttons", "options": ["Create Another Proposal", "Main Menu"]})
        elif "Main Menu" in user_input:
             return ChatResponse(next_stage="initial_choice", bot_message="Main Menu:", user_details=user_details, ui_elements={"type": "buttons", "display_style": "pills", "options": ["Explore Services", "Career Opportunities"]})
        
        return ChatResponse(next_stage="post_engagement", bot_message="How else can I help?", user_details=user_details, ui_elements={"type": "buttons", "options": ["Create Another Proposal", "Main Menu"]})

    elif stage == "job_application":
        if "Uploaded" in user_input: 
            return ChatResponse(next_stage="post_engagement", bot_message="Resume received successfully. Our HR team will review it. Good luck!", user_details=user_details, ui_elements={"type": "buttons", "options": ["Main Menu", "Visit Website"]})
    
    # Fallback to AI General Chat for unknown inputs
    return ChatResponse(next_stage="general_chat", bot_message=get_general_response(user_input), user_details=user_details)

# --- OTHER ENDPOINTS ---
@app.post("/upload-resume")
async def handle_resume_upload(email: str = Form(...), resume: UploadFile = File(...)):
    os.makedirs("resumes", exist_ok=True)
    file_path = f"resumes/{email}_{resume.filename}"
    with open(file_path, "wb") as buffer: shutil.copyfileobj(resume.file, buffer)
    return {"message": "Success"}

@app.post("/generate-proposal", status_code=202)
async def create_proposal(request: ProposalRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(generate_and_send_proposal_task, request.user_details, request.category, request.custom_category_name, request.custom_category_data)
    return {"message": "Accepted"}