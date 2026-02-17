import streamlit as st
import anthropic
import PyPDF2
import pandas as pd
import urllib.parse
from datetime import date

# --- APP CONFIG ---
st.set_page_config(page_title="Wintel: Team Intel", page_icon="🚀", layout="wide")

# --- INITIALIZE DATABASE ---
if 'prospect_db' not in st.session_state:
    st.session_state['prospect_db'] = pd.DataFrame(columns=['Date','University','Role','Priority','Status','Output_Preview'])

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main-header {font-size: 2.5rem; font-weight: 800; color: #1E3A8A;}
    .card {background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e5e7eb; margin-bottom: 20px; color: #1f2937;}
    .success-card {background-color: #f0fdf4; padding: 15px; border-radius: 10px; border: 2px solid #22c55e; margin-bottom: 20px;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🚀 Wintel: Team Sales Intelligence</p>', unsafe_allow_html=True)

# --- SIDEBAR: SETTINGS & TOOLS ---
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
    fn = st.text_input("First Name").lower().strip()
    ln = st.text_input("Last Name").lower().strip()
    dom = st.text_input("Domain (e.g. bu.edu)").lower().strip()
    if fn and ln and dom:
        email = f"{fn}.{ln}@{dom}"
        st.code(email)

    st.markdown("---")
    st.header("📊 Dashboard")
    if len(st.session_state['prospect_db']) > 0:
        st.metric("Total Prospects", len(st.session_state['prospect_db']))
        st.metric("Universities", st.session_state['prospect_db']['University'].nunique())

# --- MAIN INTERFACE ---
tab_research, tab_pool = st.tabs(["🎯 New Research", "📊 Team Prospect Pool"])

with tab_research:
    col1, col2 = st.columns(2)
    with col1: uni = st.text_input("🎓 University Name")
    with col2: role = st.selectbox("👔 Target Role", ["Director of Counseling", "VP of Student Affairs", "Dean of Students", "Director of Mental Health"])
    
    if uni:
        st.markdown("### 🕵️‍♂️ Quick Recon")
        c1, c2, c3 = st.columns(3)
        with c1: st.link_button("🔍 LinkedIn", f"https://www.google.com/search?q={urllib.parse.quote(role + ' ' + uni + ' site:linkedin.com/in/')}")
        with c2: st.link_button("📰 Student News", f"https://www.google.com/search?q={urllib.parse.quote(uni + ' student newspaper mental health')}")
        with c3: st.link_button("👥 Directory", f"https://www.google.com/search?q={urllib.parse.quote(uni + ' counseling center staff directory')}")

    st.markdown("---")
    uploaded_file = st.file_uploader("📄 Upload Research Material (PDF)", type="pdf")

    if st.button("🚀 Generate & Log Strategy", use_container_width=True):
        if not uni or not uploaded_file or not api_key:
            st.warning("Please provide a University name, a PDF, and an API Key.")
        else:
            try:
                # 1. Extract PDF
                reader = PyPDF2.PdfReader(uploaded_file)
                text = ""
                for page in reader.pages: text += page.extract_text()
                
                # 2. Call AI
                client = anthropic.Anthropic(api_key=api_key)
                with st.spinner("🤖 Claude is analyzing..."):
                    prompt = f"Role: Sean O'Connell, BDR at Uwill. Research: {text[:8000]}. Write 3 subject lines, a human email to {role} at {uni}, and AE Briefing notes with a Priority Score (1-10)."
                    message = client.messages.create(model="claude-3-haiku-20240307", max_tokens=1500, messages=[{"role": "user", "content": prompt}])
                    res = message.content[0].text
                
                # 3. Log to DB
                new_entry = pd.DataFrame([{
                    'Date': str(date.today()), 
                    'University': uni, 
                    'Role': role, 
                    'Priority': 'Assessed', 
                    'Status': 'Researched',
                    'Output_Preview': res[:150] + "..."
                }])
                st.session_state['prospect_db'] = pd.concat([st.session_state['prospect_db'], new_entry], ignore_index=True)
                
                st.markdown('<div class="success-card">✅ Strategy Logged to Pool</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="card">{res}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {e}")

with tab_pool:
    st.subheader("📁 Saved Prospect Pool")
    if not st.session_state['prospect_db'].empty:
        st.dataframe(st.session_state['prospect_db'], use_container_width=True)
        csv = st.session_state['prospect_db'].to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Pool to CSV", csv, "uwill_prospects.csv", "text/csv")
    else:
        st.info("No prospects researched yet.")
