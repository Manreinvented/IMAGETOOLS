import streamlit as st
import math
from datetime import datetime, timedelta
from fpdf import FPDF
import io

# --- Constants ---
HALF_LIFE_HOURS = 13.2235
DECAY_CONSTANT_LAMBDA = math.log(2) / HALF_LIFE_HOURS

# --- Session State Initialization ---
if 't0_dt' not in st.session_state:
    st.session_state.t0_dt = datetime.now()
if 't4_dt' not in st.session_state:
    st.session_state.t4_dt = datetime.now() + timedelta(hours=4)
if 't24_dt' not in st.session_state:
    st.session_state.t24_dt = datetime.now() + timedelta(hours=24)

# Functions to update state without causing API Errors
def update_t0():
    st.session_state.t0_dt = datetime.now()

def update_t4():
    st.session_state.t4_dt = datetime.now()

def update_t24():
    st.session_state.t24_dt = datetime.now()

def clear_all():
    st.session_state.t0_dt = datetime.now()
    st.session_state.t4_dt = datetime.now() + timedelta(hours=4)
    st.session_state.t24_dt = datetime.now() + timedelta(hours=24)
    # Clear text inputs manually if needed, or just refresh
    st.rerun()

# --- PDF Generation Function ---
def create_pdf(results_text, p_info):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "THYROID UPTAKE WORKSHEET", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Arial", size=11)
    for label, val in p_info.items():
        pdf.cell(45, 10, f"{label}:", ln=False)
        pdf.cell(0, 10, f"{val if val else '____________________'}", ln=True)
    
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font("Courier", size=10)
    for line in results_text.split('\n'):
        pdf.cell(0, 6, line, ln=True)
        
    pdf.ln(10)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font("Arial", size=11)
    pdf.cell(45, 10, "Technologist:", ln=False)
    pdf.cell(0, 10, "____________________", ln=True)
    pdf.cell(45, 10, "Date:", ln=False)
    pdf.cell(0, 10, f"{datetime.now().strftime('%Y-%m-%d')}", ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# --- Main UI ---
st.set_page_config(page_title="Thyroid Calculator", page_icon="🦋")
st.title("Thyroid Uptake Calculator")

with st.expander("Patient Information", expanded=False):
    p_name = st.text_input("Patient Name")
    p_mrn = st.text_input("MRN")
    p_dob = st.text_input("DOB")
    p_sex = st.selectbox("Sex", ["", "M", "F", "Other"])
    p_phys = st.text_input("Referring Physician")

# 1. Zero Hour
st.subheader("1. Zero Hour (Standard)")
st.button("Set Zero Hour to Now 🕒", on_click=update_t0, use_container_width=True)
col1, col2 = st.columns(2)
t0_date = col1.date_input("Zero Date", value=st.session_state.t0_dt.date())
t0_time = col2.time_input("Zero Time", value=st.session_state.t0_dt.time(), step=60)

c1, c2 = st.columns(2)
std_zero = c1.number_input("Dose in phantom (cpm)", value=50000.0)
bkg_zero = c2.number_input("Background (cpm)", value=50.0)

# 2. 4-Hour
st.subheader("2. 4-Hour Measurement")
st.button("Set 4hr Time to Now 🕒", on_click=update_t4, use_container_width=True)
col3, col4 = st.columns(2)
t4_date = col3.date_input("4hr Date", value=st.session_state.t4_dt.date())
t4_time = col4.time_input("4hr Time", value=st.session_state.t4_dt.time(), step=60)

c3, c4 = st.columns(2)
n4 = c3.number_input("4hr Neck CPM", value=0.0)
th4 = c4.number_input("4hr Thigh CPM", value=0.0)

# 3. 24-Hour
st.subheader("3. 24-Hour Measurement")
st.button("Set 24hr Time to Now 🕒", on_click=update_t24, use_container_width=True)
col5, col6 = st.columns(2)
t24_date = col5.date_input("24hr Date", value=st.session_state.t24_dt.date())
t24_time = col6.time_input("24hr Time", value=st.session_state.t24_dt.time(), step=60)

c5, c6 = st.columns(2)
n24 = c5.number_input("24hr Neck CPM", value=0.0)
th24 = c6.number_input("24hr Thigh CPM", value=0.0)

# Calculation
st.divider()
if st.button("Calculate & Generate Report", type="primary", use_container_width=True):
    t0 = datetime.combine(t0_date, t0_time)
    t4 = datetime.combine(t4_date, t4_time)
    t24 = datetime.combine(t24_date, t24_time)
    
    h4 = (t4 - t0).total_seconds() / 3600.0
    h24 = (t24 - t0).total_seconds() / 3600.0
    
    d4, d24 = math.exp(-DECAY_CONSTANT_LAMBDA * h4), math.exp(-DECAY_CONSTANT_LAMBDA * h24)
    net_std = std_zero - bkg_zero
    up4 = ((n4 - th4) / (net_std * d4)) * 100
    up24 = ((n24 - th24) / (net_std * d24)) * 100
    
    results = f"""--- THYROID UPTAKE RESULTS ---
Zero Hour: {t0.strftime('%Y-%m-%d %H:%M')}
  Net Standard: {net_std:.1f}

4 Hour Uptake (Elapsed: {h4:.2f} hrs)
  Net Neck: {n4-th4:.1f}
  4 hour uptake: {up4:.2f}%

24 Hour Uptake (Elapsed: {h24:.2f} hrs)
  Net Neck: {n24-th24:.1f}
  24 hour uptake: {up24:.2f}%
"""
    st.code(results)
    
    p_info = {"Patient Name": p_name, "MRN": p_mrn, "DOB": p_dob, "SEX": p_sex, "Referring Physician": p_phys}
    pdf_bytes = create_pdf(results, p_info)
    st.download_button("Download PDF", data=pdf_bytes, file_name="Uptake_Report.pdf", mime="application/pdf", use_container_width=True)

if st.button("Clear All Data", use_container_width=True):
    clear_all()
