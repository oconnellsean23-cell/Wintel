import streamlit as st
import pandas as pd
import anthropic
import PyPDF2
from gnews import GNews
import urllib.parse
from datetime import date
import requests

# --- 1. INITIAL APP SETUP ---
st.set_page_config(page_title="Wintel: Team Intel", page_icon="🚀", layout="wide")

# This is the "Brain" that stores your prospects for the current session
if 'prospect_db' not in st.session_state:
    st.session_state['prospect_db'] = pd.DataFrame(columns=['Date', 'University', 'Role', 'Priority', 'Status', 'Output_Preview'])

# --- 2. PROFESSIONAL STYLING ---
st.markdown("""
    <style>
    .main-header {font-size: 2.5rem; font-weight: 800; color: #1E3A8A;}
    .card {background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e5e7eb; margin-bottom: 20px; color: #1f2937; line-height: 1.6;}
    .stButton>button {background-color: #1E3A8A; color: white; border-radius: 8px; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-header">🚀 Wintel: Team Sales Intelligence</p>', unsafe_allow_html=True)

# --- 3. SIDEBAR TOOLS ---
with st.sidebar:
    st.header("⚙️ Settings")
    try:
        if "ANTHROPIC_API_KEY" in st.secrets:
            api_key = st.secrets["ANTHROPIC_API_KEY"]
            st.success("✅ Anthropic Cloud Key Active")
        else:
            api_key = st.text_input("Anthropic API Key", type="password")
    except:
        api_key = st.text_input("Anthropic API Key", type="password")
        
    st.markdown("---")
    
    # FEATURE 1: Upgraded Email Guesser & Verifier
    st.header("📧 Email Guesser")
    fn = st.text_input("First Name").strip().lower()
    ln = st.text_input("Last Name").strip().lower()
    dom = st.text_input("Domain (e.g. bu.edu)").strip().lower()
    
    if fn and ln and dom:
        guessed_email = f"{fn}.{ln}@{dom}"
        st.code(guessed_email)
        
        if st.button("Verify Email"):
            if "@" in guessed_email and "." in dom:
                st.success("✅ Valid syntax structure.")
                st.info("💡 To ping live servers and check for bounces, add a free Hunter.io API key to your st.secrets!")
            else:
                st.error("❌ Invalid email structure.")
                
    st.markdown("---")
    if not st.session_state['prospect_db'].empty:
        st.metric("Prospects Researched", len(st.session_state['prospect_db']))

# --- 4. MAIN INTERFACE TABS ---
# FEATURE 4: Added Analytics Tab
tab_research, tab_pool, tab_news, tab_analytics = st.tabs([
    "🎯 New Research", 
    "📊 Team Prospect Pool", 
    "📰 Territory Intel & Grants",
    "📈 BDR Analytics"
])

# --- TAB 1: NEW RESEARCH ---
with tab_research:
    col1, col2 = st.columns(2)
    with col1: university = st.text_input("🎓 University Name")
    with col2: target_role = st.selectbox("👔 Target Role", ["Director of Counseling", "VP of Student Affairs", "Dean of Students", "Director of Mental Health"])
    
    if university:
        st.markdown("### 🕵️ Quick Recon")
        c1, c2, c3 = st.columns(3)
        with c1: st.link_button("🔍 LinkedIn", f"https://www.google.com/search?q={urllib.parse.quote(target_role + ' ' + university + ' site:linkedin.com/in/')}")
        with c2: st.link_button("📰 Student News", f"https://www.google.com/search?q={urllib.parse.quote(university + ' student newspaper mental health')}")
        with c3: st.link_button("👥 Directory", f"https://www.google.com/search?q={urllib.parse.quote(university + ' counseling staff directory')}")
        
    st.markdown("---")
    uploaded_file = st.file_uploader("📄 Upload Research Material (PDF)", type="pdf")
    
    if st.button("🚀 Generate & Log Strategy", type="primary"):
        if not university or not uploaded_file or not api_key:
            st.error("Missing Info: You need a University Name, a PDF, and an API Key.")
        else:
            try:
                reader = PyPDF2.PdfReader(uploaded_file)
                pdf_text = "".join([page.extract_text() for page in reader.pages])
                
                client = anthropic.Anthropic(api_key=api_key)
                with st.spinner("🤖 Claude is analyzing..."):
                    prompt = f"Role: BDR. Research: {pdf_text[:8000]}. Task: 3 subject lines, 1 personalized email to {target_role} at {university} regarding student mental health."
                    message = client.messages.create(model="claude-3-haiku-20240307", max_tokens=1500, messages=[{"role": "user", "content": prompt}])
                    ai_response = message.content[0].text
                
                new_row = pd.DataFrame([{
                    'Date': str(date.today()),
                    'University': university,
                    'Role': target_role,
                    'Priority': 'Assessed',
                    'Status': 'Researched',
                    'Output_Preview': ai_response[:100] + "..."
                }])
                st.session_state['prospect_db'] = pd.concat([st.session_state['prospect_db'], new_row], ignore_index=True)
                
                st.success("Strategy Logged Successfully!")
                st.markdown(f'<div class="card">{ai_response}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Something went wrong: {e}")

# --- TAB 2: TEAM PROSPECT POOL (FEATURE 3: CRM EXPORT) ---
with tab_pool:
    st.subheader("🗄️ Saved Prospect Pool")
    if st.session_state['prospect_db'].empty:
        st.info("No research logged yet. Start in the New Research tab!")
    else:
        df = st.session_state['prospect_db']
        st.dataframe(df, use_container_width=True)
        
        st.markdown("### Export to CRM")
        export_format = st.selectbox("Select Target CRM format:", ["Standard CSV", "Salesforce (Leads)", "Outreach"])
        
        if export_format == "Salesforce (Leads)":
            export_df = df.rename(columns={"University": "Company", "Role": "Title"})
        elif export_format == "Outreach":
            export_df = df.rename(columns={"University": "Account", "Role": "Title"})
        else:
            export_df = df
            
        csv_data = export_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Formatted CSV", csv_data, f"prospects_{export_format.lower().replace(' ', '_')}.csv", "text/csv")

# --- TAB 3: TERRITORY INTEL & GRANTS ---
with tab_news:
    st.subheader("📰 Territory News & Funding Scraper")
    
    schools_input = st.text_area("Target Schools (Paste a list, one per line)", height=150, placeholder="Boston College\nAssumption University\nPingree School")
    timeframe = st.selectbox("Timeframe:", ["1d", "7d", "30d"], key="news_timeframe")
    
    # FEATURE 3: Toggle between standard news and financial/grant news
    search_type = st.radio("Intelligence Type:", ["General Wellness News", "Grant & Funding Announcements"])

    if st.button("Search Territory", type="primary"):
        schools_list = [s.strip() for s in schools_input.split('\n') if s.strip()]
        
        if schools_list:
            master_news_list = []
            progress_bar = st.progress(0, text="Starting search...")
            google_news = GNews(language='en', country='US', period=timeframe, max_results=5)
            
            if search_type == "General Wellness News":
                keywords = ["mental health", "wellness", "counseling", "teletherapy", "psychiatric"]
            else:
                keywords = ["grant", "funding", "award", "donation", "million", "budget"]
            
            for index, school in enumerate(schools_list):
                progress_bar.progress((index + 1) / len(schools_list), text=f"Scraping {school}...")
                
                # Base query always includes mental health context
                keyword_string = " OR ".join([f'"{kw}"' for kw in keywords])
                query = f'"{school}" AND "mental health" AND ({keyword_string})'
                
                articles = google_news.get_news(query)
                if articles:
                    for article in articles:
                        if any(kw in article['title'].lower() for kw in keywords):
                            article['Target Account'] = school
                            master_news_list.append(article)
                            
            progress_bar.empty()
            
            if master_news_list:
                st.success(f"Found {len(master_news_list)} highly relevant signals!")
                res_df = pd.DataFrame(master_news_list)[['Target Account', 'title', 'published date', 'url']]
                res_df['published date'] = pd.to_datetime(res_df['published date']).dt.strftime('%b %d, %Y')
                st.dataframe(res_df, column_config={"url": st.column_config.LinkColumn("Read")}, hide_index=True, use_container_width=True)
            else:
                st.warning(f"No {search_type.lower()} found for those schools recently.")
        else:
            st.error("Please paste at least one school name.")

# --- TAB 4: BDR ANALYTICS (FEATURE 4) ---
with tab_analytics:
    st.subheader("📈 Workflow Analytics")
    if st.session_state['prospect_db'].empty:
        st.info("Log some strategies in the Research tab to populate your dashboard!")
    else:
        df = st.session_state['prospect_db']
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Strategies Generated by Role**")
            role_counts = df['Role'].value_counts()
            st.bar_chart(role_counts)
        with c2:
            st.markdown("**Daily Output Velocity**")
            date_counts = df['Date'].value_counts()
            st.line_chart(date_counts)