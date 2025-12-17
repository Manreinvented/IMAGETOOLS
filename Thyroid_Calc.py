import streamlit as st
import math
from datetime import datetime, timedelta
from fpdf import FPDF
import io

# --- Constants & Logic ---
HALF_LIFE_HOURS = 13.2235
DECAY_CONSTANT_LAMBDA = math.log(2) / HALF_LIFE_HOURS

def calculate_decay(elapsed_hours):
    return math.exp(-DECAY_CONSTANT_LAMBDA * elapsed_hours)

# --- PDF Generation Function ---
def create_pdf(results_text, p_name, p_mrn, p_dob, p_sex, p_phys):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "THYROID UPTAKE WORKSHEET", ln=True, align='C')
    pdf.ln(5)
    
    # Patient Info Section
    pdf.set_font("Arial", size=11)
    fields = [
        ("Patient Name", p_name), ("MRN", p_mrn), 
        ("DOB", p_dob), ("SEX", p_sex), 
        ("Referring Physician", p_phys)
    ]
    for label, val in fields:
        pdf.cell(45, 8, f"{label}:", ln=False)
        pdf.cell(0, 8, f"{val if val else '____________________'}", ln=True)
    
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Results Section
    pdf.set_font("Courier", size=10)
    for line in results_text.split('\n'):
        pdf.cell(0, 6, line, ln=True)
        
    pdf.ln(10)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Footer
    pdf.set_font("Arial", size=11)
    pdf.cell(45, 8, "Technologist:", ln=False)
    pdf.cell(0, 8, "____________________", ln=True)
    pdf.cell(45, 8, "Date:", ln=False)
    pdf.cell(0, 8, f"{datetime.now().strftime('%Y-%m-%d')}", ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# --- Streamlit UI ---
st.set_page_config(page_title="Thyroid Uptake", page_icon="🦋")

st.title("Thyroid Uptake Calculator")

# Patient Information (Collapsible to save space on mobile)
with st.expander("Patient Information (for PDF)", expanded=False):
    col1, col2 = st.columns(2)
    p_name = col1.text_input("Patient Name")
    p_mrn = col2.text_input("MRN")
    p_dob = col1.text_input("DOB")
    p_sex = col2.selectbox("Sex", ["", "M", "F", "Other"])
    p_phys = st.text_input("Referring Physician")

# Zero Hour Inputs
st.subheader("1. Zero Hour (Standard)")
t0_date = st.date_input("Zero Date", datetime.now())
t0_time = st.time_input("Zero Time", datetime.now())
std_zero = st.number_input("Dose in phantom (cpm)", value=50000.0, step=100.0)
bkg_zero = st.number_input("Background (cpm)", value=50.0, step=1.0)

# 4 Hour Inputs
st.subheader("2. 4-Hour Measurement")
t4_date = st.date_input("4hr Date", datetime.now())
t4_time = st.time_input("4hr Time", datetime.now() + timedelta(hours=4))
n4 = st.number_input("4hr Neck CPM", value=0.0)
th4 = st.number_input("4hr Thigh CPM", value=0.0)

# 24 Hour Inputs
st.subheader("3. 24-Hour Measurement")
t24_date = st.date_input("24hr Date", datetime.now())
t24_time = st.time_input("24hr Time", datetime.now() + timedelta(hours=24))
n24 = st.number_input("24hr Neck CPM", value=0.0)
th24 = st.number_input("24hr Thigh CPM", value=0.0)

if st.button("Calculate and Generate Report", type="primary", use_container_width=True):
    # Time logic
    t0 = datetime.combine(t0_date, t0_time)
    t4 = datetime.combine(t4_date, t4_time)
    t24 = datetime.combine(t24_date, t24_time)
    
    h4 = (t4 - t0).total_seconds() / 3600.0
    h24 = (t24 - t0).total_seconds() / 3600.0
    
    # Math logic
    d4, d24 = calculate_decay(h4), calculate_decay(h24)
    net_std = std_zero - bkg_zero
    corr_4, corr_24 = net_std * d4, net_std * d24
    up4 = ((n4 - th4) / corr_4) * 100
    up24 = ((n24 - th24) / corr_24) * 100
    
    results = f"""--- THYROID UPTAKE RESULTS ---

Zero Hour (Time: {t0.strftime('%Y-%m-%d %H:%M')})
  Net (standard)           | {net_std:.1f}

4 Hour Uptake (Elapsed: {h4:.2f} hrs)
  Net Neck                 | {n4 - th4:.1f}
  Decay correction factor  | x {d4:.3f}
  4 hour uptake            = {up4:.2f}%

24 Hour Uptake (Elapsed: {h24:.2f} hrs)
  Net Neck                 | {n24 - th24:.1f}
  Decay correction factor  | x {d24:.3f}
  24 hour uptake           = {up24:.2f}%

*Normal Range: 4h (5-20%), 24h (15-35%)"""

    st.code(results)
    
    # PDF Generation
    pdf_bytes = create_pdf(results, p_name, p_mrn, p_dob, p_sex, p_phys)
    
    st.download_button(
        label="Download PDF Report",
        data=pdf_bytes,
        file_name=f"Thyroid_{p_mrn if p_mrn else 'Report'}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
