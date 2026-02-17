import streamlit as st
import anthropic
import PyPDF2
import pandas as pd
import io
import urllib.parse
from datetime import date

# --- APP CONFIG ---
st.set_page_config(page_title="Wintel: Team Intel", page_icon="🚀", layout="wide")

# --- DATABASE LOGIC ---
if 'prospect_db' not in st.session_state:
    st.session_state['prospect_db'] = pd.DataFrame(columns=['Date','University','Role','Priority','Status'])

# Custom CSS
st.markdown("""
    <style>
    .main-header {font-size: 2.5rem; font-weight: 800; color: #1E3A8A;}
    .card {background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e5e7eb; margin-bottom: 20px; color: #1f2937;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🚀 Wintel: Team Sales Intelligence</p>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    try:
        if "ANTHROPIC_API_KEY" in st.secrets:
            api_key = st.secrets["ANTHROPIC_API_KEY"]
            st.success("✅ Cloud Key Active")
        else:
            api_key = st.text_input("Anthropic API Key", type="password")
    except:
        api_key = st.text_input("Anthropic API Key", type="password")
    
    st.markdown("---")
    st.header("📧 Email Guesser")
    fn = st.text_input("First Name")
    ln = st.text_input("Last Name")
    dom = st.text_input("Domain (e.g. bu.edu)")
    if fn and ln and dom:
        st.code(f"{fn}.{ln}@{dom}")

# --- MAIN INTERFACE: TABS ---
tab_research, tab_pool = st.tabs(["🎯 New Research", "📊 Team Prospect Pool"])

with tab_research:
    col1, col2 = st.columns(2)
    with col1: university = st.text_input("University Name")
    with col2: target_role = st.text_input("Target Role", value="Director of Counseling")
    
    if university:
        st.markdown("### 🕵️‍♂️ Quick Recon")
        c1, c2, c3 = st.columns(3)
        with c1: st.link_button("🔍 LinkedIn", f"https://www.google.com/search?q={urllib.parse.quote(target_role + ' ' + university + ' site:linkedin.com/in/')}")
        with c2: st.link_button("📰 Student News", f"https://www.google.com/search?q={urllib.parse.quote(university + ' student newspaper mental health')}")
        with c3: st.link_button("👥 Directory", f"https://www.google.com/search?q={urllib.parse.quote(university + ' counseling staff directory')}")

    st.markdown("---")
    uploaded_file = st.file_uploader("Upload Strategic Plan or Research (PDF)", type="pdf")

    if st.button("Generate & Log Strategy"):
        research_text = ""
        if uploaded_file:
            try:
                reader = PyPDF2.PdfReader(uploaded_file)
                for page in reader.pages: research_text += page.extract_text()
                research_text = research_text[:6000] # Increased limit for better AI context
            except: st.error("PDF error.")

        if research_text and api_key:
            client = anthropic.Anthropic(api_key=api_key)
            with st.spinner("Analyzing..."):
                prompt = f"Role: Sean O'Connell, BDR at Uwill. Research: {research_text}. Task: Write 3 subject lines, a human email to {target_role} at {university}, and an AE Briefing with a priority score (1-10)."
                message = client.messages.create(model="claude-3-haiku-20240307", max_tokens=2000, messages=[{"role": "user", "content": prompt}])
                output = message.content[0].text
                
                # Log to Internal DB
                new_entry = pd.DataFrame([{'Date': str(date.today()), 'University': university, 'Role': target_role, 'Priority': 'Assessed', 'Status': 'Researched'}])
                st.session_state['prospect_db'] = pd.concat([st.session_state['prospect_db'], new_entry], ignore_index=True)
                
                st.markdown(f'<div class="card">{output}</div>', unsafe_allow_html=True)
        else:
            st.warning("Please upload a PDF and ensure your API key is active.")

with tab_pool:
    st.subheader("📁 Saved Prospect Pool")
    st.dataframe(st.session_state['prospect_db'], use_container_layout=True)
    csv = st.session_state['prospect_db'].to_csv(index=False).encode('utf-8')
    st.download_button("📥 Export to CSV", csv, "prospect_pool.csv", "text/csv")
