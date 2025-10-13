# pdf_writer.py

from fpdf import FPDF
import os
from datetime import datetime

COMPANY_EMAIL = "Partha@infinitetechai.com"
COMPANY_PHONE = "+91 98847 77171"

class PDF(FPDF):
    def header(self):
        self.set_fill_color(0, 51, 102) # Dark blue
        self.set_text_color(255, 255, 255) # White text
        self.set_font("DejaVu", "B", 16)
        # Use different title for sales lead PDF
        if self.page_no() == 1 and hasattr(self, 'pdf_type') and self.pdf_type == 'sales_lead':
            self.cell(0, 12, "NEW LEAD: Client Request Summary", ln=True, align="C", fill=True)
        else:
            self.cell(0, 12, "Personalized Development Proposal", ln=True, align="C", fill=True)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "I", 8)
        self.set_text_color(128)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

    def section_title(self, title):
        self.set_font("DejaVu", "B", 12)
        self.set_fill_color(230, 230, 230) # Light grey
        self.set_text_color(0, 0, 0) # Black text
        self.cell(0, 8, title, ln=True, fill=True, align="L")
        self.ln(4)

# Function to setup fonts (reused by both PDF generation functions)
def setup_fonts(pdf_instance):
    font_path = os.path.join(os.path.dirname(__file__), "fonts") 
    if not os.path.exists(os.path.join(font_path, "DejaVuSans.ttf")):
        print("WARNING: DejaVu fonts not found. Using Arial.")
        pdf_instance.add_font("Arial", "", "Arial.ttf", uni=True) # Ensure Arial is registered for fallback
        pdf_instance.add_font("Arial", "B", "Arialbd.ttf", uni=True)
        pdf_instance.add_font("Arial", "I", "Arial.ttf", uni=True) # Assuming Arial.ttf has italics too
        pdf_instance.set_font("Arial", "B", 12)
    else:
        pdf_instance.add_font("DejaVu", "", os.path.join(font_path, "DejaVuSans.ttf"), uni=True)
        pdf_instance.add_font("DejaVu", "B", os.path.join(font_path, "DejaVuSans-Bold.ttf"), uni=True)
        pdf_instance.add_font("DejaVu", "I", os.path.join(font_path, "DejaVuSans-Oblique.ttf"), uni=True)


def create_proposal_pdf(user_details, proposal_text, proposal_costs, country_info, output_path):
    pdf = PDF()
    pdf.pdf_type = 'client_proposal' # Identify PDF type for header
    setup_fonts(pdf) # Setup fonts
    pdf.set_auto_page_break(auto=True, margin=15) # Adjust margin if needed
    pdf.add_page()
    pdf.set_text_color(0,0,0) # Reset text color to black

    # --- Client & Project Overview ---
    pdf.section_title("Client & Project Overview")
    pdf.set_font("DejaVu", "", 11)
    
    pdf.cell(40, 7, "Date:")
    pdf.set_font("DejaVu", "B", 11)
    pdf.cell(0, 7, datetime.now().strftime("%B %d, %Y"), ln=True)

    pdf.set_font("DejaVu", "", 11)
    pdf.cell(40, 7, "Company:")
    pdf.set_font("DejaVu", "B", 11)
    pdf.cell(0, 7, user_details.get('company', 'N/A'), ln=True)
    
    pdf.set_font("DejaVu", "", 11)
    pdf.cell(40, 7, "Contact Person:")
    pdf.set_font("DejaVu", "B", 11)
    pdf.cell(0, 7, user_details.get('name', 'N/A'), ln=True)

    pdf.set_font("DejaVu", "", 11)
    pdf.cell(40, 7, "Email:")
    pdf.set_font("DejaVu", "B", 11)
    pdf.cell(0, 7, user_details.get('email', 'N/A'), ln=True)

    pdf.set_font("DejaVu", "", 11)
    pdf.cell(40, 7, "Contact Phone:")
    pdf.set_font("DejaVu", "B", 11)
    pdf.cell(0, 7, user_details.get('contact', 'N/A'), ln=True)

    # --- FIX: Only one Project row, with CORRECT custom service in brackets ---
    pdf.set_font("DejaVu", "", 11)
    pdf.cell(40, 7, "Project:")
    pdf.set_font("DejaVu", "B", 11)
    
    project_display_name = user_details.get('category', 'N/A')
    custom_name = user_details.get('custom_category_name')

    # This logic now correctly checks if a custom name exists and the category is "Others" or "Custom Service"
    if custom_name and project_display_name in ["Others", "Custom Service"]:
        project_display_name = f"Others ({custom_name})"
    
    pdf.cell(0, 7, project_display_name, ln=True)
    pdf.ln(8)

    # --- Introduction ---
    pdf.section_title("Introduction")
    pdf.set_font("DejaVu", "", 11)
    pdf.multi_cell(0, 7, proposal_text.get('introduction', ''))
    pdf.ln(8)
    
    # --- Estimated Cost Breakdown ---
    pdf.section_title("Estimated Cost Breakdown")
    pdf.set_font("DejaVu", "B", 10)
    pdf.set_fill_color(0, 51, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(130, 8, "Component", 1, 0, "C", fill=True)
    pdf.cell(60, 8, "Estimated Cost", 1, 1, "C", fill=True)
    
    pdf.set_font("DejaVu", "", 10)
    pdf.set_text_color(0)
    for item in proposal_costs.get('cost_breakdown', []):
        pdf.cell(130, 8, item.get('item', ''), 1, 0, "L")
        pdf.cell(60, 8, item.get('cost', ''), 1, 1, "R")
    
    # --- FIX: Ensure enough spacing before footer for totals ---
    pdf.set_font("DejaVu", "B", 10)
    pdf.cell(130, 8, "Subtotal", 1, 0, "R")
    pdf.cell(60, 8, proposal_costs.get('subtotal_str', ''), 1, 1, "R")
    
    pdf.set_text_color(34, 139, 34) # Green for discount
    pdf.cell(130, 8, f"Volume Discount ({proposal_costs.get('discount_rate_str', '0%')})", 1, 0, "R")
    pdf.cell(60, 8, proposal_costs.get('discount_str', ''), 1, 1, "R")
    
    pdf.set_text_color(0) # Reset to black
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(130, 10, "Final Estimated Total", 1, 0, "R")
    pdf.cell(60, 10, proposal_costs.get('final_total_str', ''), 1, 1, "R")
    pdf.ln(15) # Increased spacing after total

    # --- Contact Us to Get Started ---
    pdf.section_title("Contact Us to Get Started")
    pdf.set_font("DejaVu", "", 10)
    pdf.set_text_color(0)
    pdf.cell(0, 6, f"Email: {COMPANY_EMAIL}", ln=True)
    pdf.cell(0, 6, f"Phone: {COMPANY_PHONE}", ln=True)
    
    try:
        pdf.output(output_path)
    except Exception as e:
        print(f"Error while saving client proposal PDF: {e}")

# --- NEW FUNCTION FOR SALES LEAD PDF ---
def create_sales_lead_pdf(user_details, proposal_costs, output_path):
    pdf = PDF()
    pdf.pdf_type = 'sales_lead'
    setup_fonts(pdf)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)

    # --- Main Title and Timestamp ---
    pdf.section_title(f"New Lead Summary: {user_details.get('company', 'N/A')}")
    
    # *** CHANGE 1: Ensure font is set to regular ("") instead of italic ("I") ***
    pdf.set_font("DejaVu", "", 10)
    
    pdf.set_text_color(128)
    
    # *** CHANGE 2: Remove the time from the date format ***
    pdf.cell(0, 6, f"Generated on: {datetime.now().strftime('%B %d, %Y')}", ln=True, align='L')
    
    pdf.ln(8)

    def add_detail_row(label, value):
        pdf.set_font("DejaVu", "B", 11)
        pdf.cell(50, 8, label, 0, 0, 'L')
        pdf.set_font("DejaVu", "", 11)
        pdf.multi_cell(0, 8, value, 0, 'L')
        pdf.ln(1)

    # --- Client & Company Information Section ---
    pdf.section_title("Client & Company Information")
    add_detail_row("Contact Person:", user_details.get('name', 'N/A'))
    add_detail_row("Company Name:", user_details.get('company', 'N/A'))
    add_detail_row("Email Address:", user_details.get('email', 'N/A'))
    add_detail_row("Phone Number:", user_details.get('phone', 'N/A'))
    pdf.ln(2)
    add_detail_row("Company Size:", user_details.get('company_size', 'N/A'))
    add_detail_row("Country:", user_details.get('country', 'N/A'))
    pdf.ln(8)

    # --- Project Details Section ---
    pdf.section_title("Project Details")
    main_service_display = user_details.get('main_service', 'N/A')
    sub_category_display = user_details.get('sub_category')
    if sub_category_display and sub_category_display != '_default':
        main_service_display += f" > {sub_category_display}"
    
    project_name_sales = user_details.get('custom_category_name') or user_details.get('category', 'N/A')

    add_detail_row("Service Category:", main_service_display)
    add_detail_row("Specific Request:", project_name_sales)
    add_detail_row("Stated Budget:", user_details.get('budget', 'N/A'))
    
    add_detail_row("Estimated Total:", proposal_costs.get('final_total_str', 'N/A'))
    pdf.ln(8)
    
    # --- Additional Client Notes Section ---
    pdf.section_title("Additional Client Notes")
    pdf.set_font("DejaVu", "", 11)
    description = user_details.get('description', 'No additional features requested.')
    pdf.multi_cell(0, 7, f'"{description}"', border=0, align='L')
    pdf.ln(5)

    try:
        pdf.output(output_path)
    except Exception as e:
        print(f"Error while saving sales lead PDF: {e}")