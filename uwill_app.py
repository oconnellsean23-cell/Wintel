import streamlit as st
import anthropic
from newspaper import Article
import PyPDF2
import pandas as pd
import io
import urllib.parse
from datetime import date

# --- APP CONFIG ---
st.set_page_config(page_title="Wintel: Team Intel", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    .main-header {font-size: 2.5rem; font-weight: 800; color: #1E3A8A;}
    .card {background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e5e7eb; margin-bottom: 20px;}
    .metric-box {background-color: #EFF6FF; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #BFDBFE;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🚀 Wintel: Team Sales Intelligence</p>', unsafe_allow_html=True)

# --- DATABASE LOGIC (INTERNAL PANDAS) ---
if 'prospect_db' not in st.session_state:
    st.session_state['prospect_db'] = pd.DataFrame(columns=['Date','University','Role','Hook','Priority','Brief','Status'])

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Team Settings")
    try:
        api_key = st.secrets["ANTHROPIC_API_KEY"] if "ANTHROPIC_API_KEY" in st.secrets else st.text_input("API Key", type="password")
    except: api_key = st.text_input("API Key", type="password")
    
    st.markdown("---")
    st.info("📍 Territory: Stoneham / New England")
    st.write(f"Total Leads in Pool: {len(st.session_state['prospect_db'])}")

# --- TABS ---
tab_research, tab_pool = st.tabs(["🎯 New Research", "📊 Team Prospect Pool"])

with tab_research:
    col1, col2 = st.columns(2)
    with col1: university = st.text_input("Target University")
    with col2: target_role = st.text_input("Target Role", value="Director of Counseling")
    
    st.markdown("---")
    subcol1, subcol2 = st.columns(2)
    with subcol1: url = st.text_input("Research Link (News/Article)")
    with subcol2: uploaded_file = st.file_uploader("Upload Strategic Plan (PDF)", type="pdf")

    if st.button("Generate & Log Intelligence"):
        research_text = ""
        # (Scraping/PDF Logic remains same as previous versions)
        if url:
            article = Article(url); article.download(); article.parse()
            research_text = article.text[:4000]
        elif uploaded_file:
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages: research_text += page.extract_text()
            research_text = research_text[:4000]

        if research_text and api_key:
            client = anthropic.Anthropic(api_key=api_key)
            with st.spinner("Building Team Intelligence Pack..."):
                prompt = f"""
                Research: {research_text}
                Prospect: {target_role} at {university}
                
                Task: Generate a high-impact sales pack:
                1. Cold Email Draft (Sean's Voice)
                2. AE Brief (3 sentences on why this is a 'win' for an Account Executive)
                3. Priority Score (1-10) based on urgency in text
                4. Potential Landmines (Competitors/Budget issues)
                """
                
                message = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                res = message.content[0].text
                
                # Update Internal DB
                new_data = {
                    'Date': str(date.today()),
                    'University': university,
                    'Role': target_role,
                    'Hook': "Cited Research",
                    'Priority': "High", # Simplified for demo
                    'Brief': "Strategic Fit identified via plan",
                    'Status': "Researched"
                }
                st.session_state['prospect_db'] = pd.concat([st.session_state['prospect_db'], pd.DataFrame([new_data])], ignore_index=True)
                
                st.markdown("### 📝 Outreach Draft & AE Brief")
                st.markdown(f'<div class="card">{res}</div>', unsafe_allow_html=True)

with tab_pool:
    st.subheader("📁 Master Prospect Pool")
    st.dataframe(st.session_state['prospect_db'], use_container_layout=True)
    
    # MASTER EXPORT
    csv = st.session_state['prospect_db'].to_csv(index=False).encode('utf-8')
    st.download_button("📥 Export Entire Pool to CSV", csv, "team_prospect_pool.csv", "text/csv")
