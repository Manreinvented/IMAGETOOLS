import streamlit as st
import math
from datetime import datetime, timedelta
from fpdf import FPDF
import io

# --- Constants ---
HALF_LIFE_HOURS = 13.2235
DECAY_CONSTANT_LAMBDA = math.log(2) / HALF_LIFE_HOURS

# --- Session State Initialization (for "Clear All" and "Now" buttons) ---
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.t0_dt = datetime.now()
    st.session_state.t4_dt = datetime.now() + timedelta(hours=4)
    st.session_state.t24_dt = datetime.now() + timedelta(hours=24)

def set_now(key_prefix):
    st.session_state[f"{key_prefix}_date"] = datetime.now().date()
    st.session_state[f"{key_prefix}_time"] = datetime.now().time()

def clear_all():
    for key in st.session_state.keys():
        if key != 'initialized':
            del st.session_state[key]
    st.rerun()

# --- PDF Generation Function ---
def create_pdf(results_text, p_info):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "THYROID UPTAKE WORKSHEET", ln=True, align='C')
    pdf.ln(5)
    
    # Patient Info Header with Lines
    pdf.set_font("Arial", size=11)
    for label, val in p_info.items():
        pdf.cell(45, 10, f"{label}:", ln=False)
        line_content = val if val else "____________________________________"
        pdf.cell(0, 10, line_content, ln=True)
    
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Results Section (Monospaced)
    pdf.set_font("Courier", size=10)
    for line in results_text.split('\n'):
        pdf.cell(0, 6, line, ln=True)
        
    pdf.ln(10)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Footer Section with Lines
    pdf.set_font("Arial", size=11)
    pdf.cell(45, 10, "Technologist:", ln=False)
    pdf.cell(0, 10, "____________________________________", ln=True)
    pdf.cell(45, 10, "Date:", ln=False)
    pdf.cell(0, 10, f"{datetime.now().strftime('%Y-%m-%d')}", ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# --- Streamlit UI ---
st.set_page_config(page_title="Thyroid Calculator", page_icon="🦋")

st.title("Thyroid Uptake Calculator")

# Patient Information Section
with st.expander("Patient Information", expanded=False):
    p_name = st.text_input("Patient Name", key="p_name")
    p_mrn = st.text_input("MRN", key="p_mrn")
    p_dob = st.text_input("DOB", key="p_dob")
    p_sex = st.selectbox("Sex", ["", "M", "F", "Other"], key="p_sex")
    p_phys = st.text_input("Referring Physician", key="p_phys")

# 1. Zero Hour
st.subheader("1. Zero Hour (Standard)")
col_t0_1, col_t0_2 = st.columns(2)
t0_date = col_t0_1.date_input("Zero Date", value=st.session_state.t0_dt.date(), key="t0_date")
# step=60 ensures minute-by-minute selection
t0_time = col_t0_2.time_input("Zero Time", value=st.session_state.t0_dt.time(), key="t0_time", step=60)
if st.button("Set Zero Hour to Now", use_container_width=True):
    set_now("t0")
    st.rerun()

col_std_1, col_std_2 = st.columns(2)
std_zero = col_std_1.number_input("Dose in phantom (cpm)", value=50000.0, key="std_zero")
bkg_zero = col_std_2.number_input("Background (cpm)", value=50.0, key="bkg_zero")

# 2. 4-Hour
st.subheader("2. 4-Hour Measurement")
col_t4_1, col_t4_2 = st.columns(2)
t4_date = col_t4_1.date_input("4hr Date", value=st.session_state.t4_dt.date(), key="t4_date")
t4_time = col_t4_2.time_input("4hr Time", value=st.session_state.t4_dt.time(), key="t4_time", step=60)
if st.button("Set 4hr Time to Now", use_container_width=True):
    set_now("t4")
    st.rerun()

col_n4_1, col_n4_2 = st.columns(2)
n4 = col_n4_1.number_input("4hr Neck CPM", value=0.0, key="n4")
th4 = col_n4_2.number_input("4hr Thigh CPM", value=0.0, key="th4")

# 3. 24-Hour
st.subheader("3. 24-Hour Measurement")
col_t24_1, col_t24_2 = st.columns(2)
t24_date = col_t24_1.date_input("24hr Date", value=st.session_state.t24_dt.date(), key="t24_date")
t24_time = col_t24_2.time_input("24hr Time", value=st.session_state.t24_dt.time(), key="t24_time", step=60)
if st.button("Set 24hr Time to Now", use_container_width=True):
    set_now("t24")
    st.rerun()

col_n24_1, col_n24_2 = st.columns(2)
n24 = col_n24_1.number_input("24hr Neck CPM", value=0.0, key="n24")
th24 = col_n24_2.number_input("24hr Thigh CPM", value=0.0, key="th24")

# Action Buttons
st.divider()
calc_col, clear_col = st.columns(2)

if calc_col.button("Calculate", type="primary", use_container_width=True):
    t0 = datetime.combine(t0_date, t0_time)
    t4 = datetime.combine(t4_date, t4_time)
    t24 = datetime.combine(t24_date, t24_time)
    
    h4 = (t4 - t0).total_seconds() / 3600.0
    h24 = (t24 - t0).total_seconds() / 3600.0
    
    d4 = math.exp(-DECAY_CONSTANT_LAMBDA * h4)
    d24 = math.exp(-DECAY_CONSTANT_LAMBDA * h24)
    
    net_std = std_zero - bkg_zero
    up4 = ((n4 - th4) / (net_std * d4)) * 100
    up24 = ((n24 - th24) / (net_std * d24)) * 100
    
    results = f"""--- THYROID UPTAKE RESULTS ---

Zero Hour (Time: {t0.strftime('%Y-%m-%d %H:%M')})
  Dose in phantom (standard) | {std_zero}
  Background               | {bkg_zero}
  Net (standard)           | {net_std}

4 Hour Uptake (Time: {t4.strftime('%Y-%m-%d %H:%M')}, Elapsed: {h4:.2f} hrs)
  Neck counts              | {n4}
  Thigh (background)       | {th4}
  Net Neck                 | {n4-th4}
  Decay correction factor  | x {d4:.3f}
  4 hour uptake            = {up4:.2f}%

24 Hour Uptake (Time: {t24.strftime('%Y-%m-%d %H:%M')}, Elapsed: {h24:.2f} hrs)
  Neck counts              | {n24}
  Thigh (background)       | {th24}
  Net Neck                 | {n24-th24}
  Decay correction factor  | x {d24:.3f}
  24 hour uptake           = {up24:.2f}%

*Normal Range: 4h (5-20%), 24h (15-35%)"""

    st.code(results)
    
    p_info = {
        "Patient Name": p_name, "MRN": p_mrn, "DOB": p_dob, 
        "SEX": p_sex, "Referring Physician": p_phys
    }
    pdf_bytes = create_pdf(results, p_info)
    
    st.download_button(
        label="Download PDF Report",
        data=pdf_bytes,
        file_name=f"Thyroid_{p_mrn if p_mrn else 'Uptake'}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

if clear_col.button("Clear All", use_container_width=True):
    clear_all()
