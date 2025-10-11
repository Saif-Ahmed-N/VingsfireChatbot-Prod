from fpdf import FPDF
import os
from datetime import datetime

COMPANY_EMAIL = "saifahmedn2004@gmail.com"
COMPANY_PHONE = "+91 9884777171"

# --- PDF Class for the Client Proposal (Unchanged) ---
class PDF(FPDF):
    def header(self):
        self.set_fill_color(0, 51, 102)
        self.set_text_color(255, 255, 255)
        self.set_font("DejaVu", "B", 16)
        self.cell(0, 12, "Personalized Development Proposal", ln=True, align="C", fill=True)
        self.ln(10)
    # ... (rest of the class is unchanged)
    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "I", 8)
        self.set_text_color(128)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")
    def section_title(self, title):
        self.set_font("DejaVu", "B", 12)
        self.set_fill_color(230, 230, 230)
        self.cell(0, 8, title, ln=True, fill=True, align="L")
        self.ln(4)

# --- create_proposal_pdf function (Unchanged) ---
def create_proposal_pdf(user_details, proposal_text, proposal_costs, country_info, output_path):
    # This entire function is unchanged. I've included it for completeness.
    pdf = PDF()
    font_path = os.path.join(os.path.dirname(__file__), "fonts") 
    if not os.path.exists(os.path.join(font_path, "DejaVuSans.ttf")):
        pdf.set_font("Arial", "B", 12) 
    else:
        pdf.add_font("DejaVu", "", os.path.join(font_path, "DejaVuSans.ttf"), uni=True)
        pdf.add_font("DejaVu", "B", os.path.join(font_path, "DejaVuSans-Bold.ttf"), uni=True)
        pdf.add_font("DejaVu", "I", os.path.join(font_path, "DejaVuSans-Oblique.ttf"), uni=True)
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.section_title("Client & Project Overview")
    pdf.set_font("DejaVu", "", 11)
    pdf.cell(40, 7, "Date:"); pdf.set_font("DejaVu", "B", 11); pdf.cell(0, 7, datetime.now().strftime("%B %d, %Y"), ln=True)
    pdf.set_font("DejaVu", "", 11)
    pdf.cell(40, 7, "Company:"); pdf.set_font("DejaVu", "B", 11); pdf.cell(0, 7, user_details.get('company', 'N/A'), ln=True)
    pdf.set_font("DejaVu", "", 11)
    pdf.cell(40, 7, "Contact Person:"); pdf.set_font("DejaVu", "B", 11); pdf.cell(0, 7, user_details.get('name', 'N/A'), ln=True)
    pdf.set_font("DejaVu", "", 11)
    pdf.cell(40, 7, "Email:"); pdf.set_font("DejaVu", "B", 11); pdf.cell(0, 7, user_details.get('email', 'N/A'), ln=True)
    pdf.set_font("DejaVu", "", 11)
    pdf.cell(40, 7, "Contact Phone:"); pdf.set_font("DejaVu", "B", 11); pdf.cell(0, 7, user_details.get('contact', 'N/A'), ln=True)
    pdf.set_font("DejaVu", "", 11)
    pdf.cell(40, 7, "Project:"); pdf.set_font("DejaVu", "B", 11); pdf.cell(0, 7, user_details.get('category', 'N/A'), ln=True)
    pdf.ln(8)
    pdf.section_title("Introduction")
    pdf.set_font("DejaVu", "", 11)
    pdf.multi_cell(0, 7, proposal_text.get('introduction', ''))
    pdf.ln(8)
    pdf.section_title("Estimated Cost Breakdown")
    pdf.set_font("DejaVu", "B", 10)
    pdf.set_fill_color(0, 51, 102); pdf.set_text_color(255, 255, 255)
    pdf.cell(130, 8, "Component", 1, 0, "C", fill=True)
    pdf.cell(60, 8, "Estimated Cost", 1, 1, "C", fill=True)
    pdf.set_font("DejaVu", "", 10); pdf.set_text_color(0)
    for item in proposal_costs.get('cost_breakdown', []):
        pdf.cell(130, 8, item.get('item', ''), 1, 0, "L")
        pdf.cell(60, 8, item.get('cost', ''), 1, 1, "R")
    pdf.set_font("DejaVu", "B", 10)
    pdf.cell(130, 8, "Subtotal", 1, 0, "R"); pdf.cell(60, 8, proposal_costs.get('subtotal_str', ''), 1, 1, "R")
    pdf.set_text_color(34, 139, 34)
    pdf.cell(130, 8, f"Volume Discount ({proposal_costs.get('discount_rate_str', '0%')})", 1, 0, "R")
    pdf.cell(60, 8, proposal_costs.get('discount_str', ''), 1, 1, "R")
    pdf.set_text_color(0); pdf.set_font("DejaVu", "B", 12)
    pdf.cell(130, 10, "Final Estimated Total", 1, 0, "R"); pdf.cell(60, 10, proposal_costs.get('final_total_str', ''), 1, 1, "R")
    pdf.ln(10)
    pdf.section_title("Contact Us to Get Started")
    pdf.set_font("DejaVu", "", 10); pdf.set_text_color(0)
    pdf.cell(0, 6, f"Email: {COMPANY_EMAIL}", ln=True)
    pdf.cell(0, 6, f"Phone: {COMPANY_PHONE}", ln=True)
    try: pdf.output(output_path)
    except Exception as e: print(f"Error while saving PDF: {e}")

# --- NEW PROFESSIONAL LEAD SUMMARY PDF ---
def create_lead_summary_pdf(user_details, output_path):
    pdf = FPDF()
    font_path = os.path.join(os.path.dirname(__file__), "fonts")
    if os.path.exists(os.path.join(font_path, "DejaVuSans.ttf")):
        pdf.add_font("DejaVu", "", os.path.join(font_path, "DejaVuSans.ttf"), uni=True)
        pdf.add_font("DejaVu", "B", os.path.join(font_path, "DejaVuSans-Bold.ttf"), uni=True)
    else:
        pdf.set_font("Arial", "B", 12)
    
    pdf.add_page()
    
    # Professional Header
    pdf.set_fill_color(45, 55, 72) # slate-800
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("DejaVu", "B", 18)
    pdf.cell(0, 15, "New Chatbot Lead Notification", 0, 1, 'C', fill=True)
    pdf.ln(12)

    pdf.set_text_color(0)
    pdf.set_font("DejaVu", "", 11)
    
    # Logic to handle "Others" project name
    project_display = user_details.get('category', 'N/A')
    custom_name = user_details.get('custom_category_name')
    if project_display == "Custom Service" and custom_name:
        project_display = f"Others ({custom_name})"

    details_to_include = {
        "Date": datetime.now().strftime("%B %d, %Y"),
        "Contact Person": user_details.get('name', 'N/A'),
        "Company": user_details.get('company', 'N/A'),
        "Email": user_details.get('email', 'N/A'),
        "Phone": user_details.get('phone', 'N/A'),
        "Country": user_details.get('country', 'N/A'),
        "Company Size": user_details.get('company_size', 'N/A'),
        "Budget": user_details.get('budget', 'N/A'),
        "Service": user_details.get('main_service', 'N/A'),
        "Project": project_display, # Use the new display value
        "Additional Details": user_details.get('description', 'N/A')
    }

    # Draw table-like structure
    for key, value in details_to_include.items():
        pdf.set_font("DejaVu", "B", 11)
        pdf.set_fill_color(243, 244, 246) # gray-100
        pdf.cell(55, 10, f" {key}:", 1, 0, 'L', fill=True)
        pdf.set_font("DejaVu", "", 11)
        pdf.multi_cell(0, 10, f" {str(value)}", 1, 'L')

    try:
        pdf.output(output_path)
    except Exception as e:
        print(f"Error while saving lead summary PDF: {e}")