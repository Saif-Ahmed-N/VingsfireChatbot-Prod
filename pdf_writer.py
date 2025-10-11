from fpdf import FPDF
import os
from datetime import datetime

COMPANY_EMAIL = "Partha@infinitetechai.com"
COMPANY_PHONE = "+91 98847 77171"

class PDF(FPDF):
    def header(self):
        self.set_fill_color(0, 51, 102)
        self.set_text_color(255, 255, 255)
        self.set_font("DejaVu", "B", 16)
        self.cell(0, 12, "Personalized Development Proposal", ln=True, align="C", fill=True)
        self.ln(10)

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

def create_proposal_pdf(user_details, proposal_text, proposal_costs, country_info, output_path):
    pdf = PDF()

    font_path = os.path.join(os.path.dirname(__file__), "fonts") 
    
    if not os.path.exists(os.path.join(font_path, "DejaVuSans.ttf")):
        print("WARNING: DejaVu fonts not found. Using Arial.")
        pdf.set_font("Arial", "B", 12) 
    else:
        pdf.add_font("DejaVu", "", os.path.join(font_path, "DejaVuSans.ttf"), uni=True)
        pdf.add_font("DejaVu", "B", os.path.join(font_path, "DejaVuSans-Bold.ttf"), uni=True)
        pdf.add_font("DejaVu", "I", os.path.join(font_path, "DejaVuSans-Oblique.ttf"), uni=True)

    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.section_title("Client & Project Overview")
    pdf.set_font("DejaVu", "", 11)

    # Determine the project name to display

    project_name = user_details.get('custom_category_name', user_details.get('category', 'N/A'))
    
    pdf.set_font("DejaVu", "", 11)
    pdf.cell(40, 7, "Project:")
    pdf.set_font("DejaVu", "B", 11)
    pdf.cell(0, 7, project_name, ln=True)
    # --- MODIFICATION END ---

    pdf.ln(8)
    
    # --- BUG FIX: ADDED DATE TO THE PROPOSAL ---
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

    pdf.set_font("DejaVu", "", 11)
    pdf.cell(40, 7, "Project:")
    pdf.set_font("DejaVu", "B", 11)
    pdf.cell(0, 7, user_details.get('category', 'N/A'), ln=True)
    pdf.ln(8)

    pdf.section_title("Introduction")
    pdf.set_font("DejaVu", "", 11)
    pdf.multi_cell(0, 7, proposal_text.get('introduction', ''))
    pdf.ln(8)
    
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
    
    pdf.set_font("DejaVu", "B", 10)
    pdf.cell(130, 8, "Subtotal", 1, 0, "R")
    pdf.cell(60, 8, proposal_costs.get('subtotal_str', ''), 1, 1, "R")
    
    pdf.set_text_color(34, 139, 34)
    pdf.cell(130, 8, f"Volume Discount ({proposal_costs.get('discount_rate_str', '0%')})", 1, 0, "R")
    pdf.cell(60, 8, proposal_costs.get('discount_str', ''), 1, 1, "R")
    
    pdf.set_text_color(0)
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(130, 10, "Final Estimated Total", 1, 0, "R")
    pdf.cell(60, 10, proposal_costs.get('final_total_str', ''), 1, 1, "R")
    pdf.ln(10)

    pdf.section_title("Contact Us to Get Started")
    pdf.set_font("DejaVu", "", 10)
    pdf.set_text_color(0)
    pdf.cell(0, 6, f"Email: {COMPANY_EMAIL}", ln=True)
    pdf.cell(0, 6, f"Phone: {COMPANY_PHONE}", ln=True)
    
    try:
        pdf.output(output_path)
    except Exception as e:
        print(f"Error while saving PDF: {e}")
