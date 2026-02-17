import streamlit as st
import anthropic
import PyPDF2
import pandas as pd
import urllib.parse
from datetime import date

# --- 1. INITIAL APP SETUP ---
st.set_page_config(page_title="Wintel: Team Intel", page_icon="🚀", layout="wide")

# This is the "Brain" that stores your prospects for the current session
if 'prospect_db' not in st.session_state:
    st.session_state['prospect_db'] = pd.DataFrame(columns=['Date','University','Role','Priority','Status','Output_Preview'])

# --- 2. PROFESSIONAL STYLING ---
st.markdown("""
    <style>
    .main-header {font-size: 2.5rem; font-weight: 800; color: #1E3A8A;}
    .card {background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e5e7eb; margin-bottom: 20px; color: #1f2937; line-height: 1.6;}
    .stButton>button {background-color: #1E3A8A; color: white; border-radius: 8px; width: 100%; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🚀 Wintel: Team Sales Intelligence</p>', unsafe_allow_html=True)

# --- 3. SIDEBAR TOOLS ---
with st.sidebar:
    st.header("⚙️ Settings")
    # Tries to find your API key in the cloud secrets first
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
    fn = st.text_input("First Name").strip().lower()
    ln = st.text_input("Last Name").strip().lower()
    dom = st.text_input("Domain (e.g. bu.edu)").strip().lower()
    if fn and ln and dom:
        st.code(f"{fn}.{ln}@{dom}")
    
    st.markdown("---")
    if not st.session_state['prospect_db'].empty:
        st.metric("Prospects Researched", len(st.session_state['prospect_db']))

# --- 4. MAIN INTERFACE ---
tab_research, tab_pool = st.tabs(["🎯 New Research", "📊 Team Prospect Pool"])

with tab_research:
    col1, col2 = st.columns(2)
    with col1: university = st.text_input("🎓 University Name")
    with col2: target_role = st.selectbox("👔 Target Role", ["Director of Counseling", "VP of Student Affairs", "Dean of Students", "Director of Mental Health"])
    
    # Instant Recon Links
    if university:
        st.markdown("### 🕵️‍♂️ Quick Recon")
        c1, c2, c3 = st.columns(3)
        with c1: st.link_button("🔍 LinkedIn", f"https://www.google.com/search?q={urllib.parse.quote(target_role + ' ' + university + ' site:linkedin.com/in/')}")
        with c2: st.link_button("📰 Student News", f"https://www.google.com/search?q={urllib.parse.quote(university + ' student newspaper mental health')}")
        with c3: st.link_button("👥 Directory", f"https://www.google.com/search?q={urllib.parse.quote(university + ' counseling staff directory')}")

    st.markdown("---")
    uploaded_file = st.file_uploader("📄 Upload Research Material (PDF)", type="pdf")

    if st.button("🚀 Generate & Log Strategy"):
        if not university or not uploaded_file or not api_key:
            st.error("Missing Info: You need a University Name, a PDF, and an API Key.")
        else:
            try:
                # A. Read PDF
                reader = PyPDF2.PdfReader(uploaded_file)
                pdf_text = ""
                for page in reader.pages: pdf_text += page.extract_text()
                
                # B. Call AI (Sean's Voice)
                client = anthropic.Anthropic(api_key=api_key)
                with st.spinner("🤖 Claude is analyzing..."):
                    prompt = f"Role: Sean O'Connell, BDR at Uwill. Research: {pdf_text[:8000]}. Task: 3 subject lines, 1 personalized email to {target_role} at {university}, and a brief AE handoff note."
                    message = client.messages.create(model="claude-3-haiku-20240307", max_tokens=1500, messages=[{"role": "user", "content": prompt}])
                    ai_response = message.content[0].text
                
                # C. Save to the Pool
                new_row = pd.DataFrame([{
                    'Date': str(date.today()), 
                    'University': university, 
                    'Role': target_role, 
                    'Priority': 'Assessed', 
                    'Status': 'Researched',
                    'Output_Preview': ai_response[:100] + "..."
                }])
                st.session_state['prospect_db'] = pd.concat([st.session_state['prospect_db'], new_row], ignore_index=True)
                
                # D. Show Results
                st.success("Strategy Logged Successfully!")
                st.markdown(f'<div class="card">{ai_response}</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Something went wrong: {e}")

with tab_pool:
    st.subheader("📁 Saved Prospect Pool")
    if st.session_state['prospect_db'].empty:
        st.info("No research logged yet. Start in the New Research tab!")
    else:
        st.dataframe(st.session_state['prospect_db'], use_container_width=True)
        csv_data = st.session_state['prospect_db'].to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Pool to CSV", csv_data, "uwill_prospects.csv", "text/csv")
