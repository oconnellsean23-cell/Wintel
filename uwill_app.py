import streamlit as st
import pandas as pd
import anthropic
import PyPDF2
from gnews import GNews
import urllib.parse
from datetime import date
import requests
from bs4 import BeautifulSoup
import time

# --- NEW: Import our utility functions ---
from news_utility import get_google_news, get_newsapi_articles

# --- 1. INITIAL APP SETUP ---
st.set_page_config(page_title="Wintel: Team Intel", page_icon="🚀", layout="wide")

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

# --- HELPER FUNCTION: WEB SCRAPER ---
def scrape_article_text(url):
    """Attempt to scrape the paragraph text from a news URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=5, allow_redirects=True)
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        text = " ".join([p.get_text() for p in paragraphs])
        return text[:3000] # Return first 3000 chars to save AI tokens
    except:
        return None

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
            else:
                st.error("❌ Invalid email structure.")
                
    st.markdown("---")
    if not st.session_state['prospect_db'].empty:
        st.metric("Prospects Researched", len(st.session_state['prospect_db']))

# --- 4. MAIN INTERFACE TABS ---
tab_research, tab_pool, tab_news, tab_analytics = st.tabs([
    "🎯 New Research", 
    "📊 Team Prospect Pool", 
    "📰 Territory Intel & Triggers",
    "📈 BDR Analytics"
])

# --- TAB 1: NEW RESEARCH (UNCHANGED) ---
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
                
                new_row = pd.DataFrame([{'Date': str(date.today()), 'University': university, 'Role': target_role, 'Priority': 'Assessed', 'Status': 'Researched', 'Output_Preview': ai_response[:100] + "..."}])
                st.session_state['prospect_db'] = pd.concat([st.session_state['prospect_db'], new_row], ignore_index=True)
                st.success("Strategy Logged Successfully!")
                st.markdown(f'<div class="card">{ai_response}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Something went wrong: {e}")

# --- TAB 2: TEAM PROSPECT POOL (UNCHANGED) ---
with tab_pool:
    st.subheader("🗄️ Saved Prospect Pool")
    if not st.session_state['prospect_db'].empty:
        df = st.session_state['prospect_db']
        st.dataframe(df, use_container_width=True)
        export_format = st.selectbox("Select Target CRM format:", ["Standard CSV", "Salesforce (Leads)", "Outreach"])
        if export_format == "Salesforce (Leads)":
            export_df = df.rename(columns={"University": "Company", "Role": "Title"})
        elif export_format == "Outreach":
            export_df = df.rename(columns={"University": "Account", "Role": "Title"})
        else:
            export_df = df
        csv_data = export_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Formatted CSV", csv_data, f"prospects_{export_format.lower().replace(' ', '_')}.csv", "text/csv")

# --- TAB 3: TERRITORY INTEL & TRIGGERS (UPDATED WITH NEW ALERTS) ---
with tab_news:
    
    # --- NEW: Automated Alert Tester Section ---
    st.subheader("🔔 NEW: Automated Team Alert Tester")
    st.write("Test the strict new Google RSS and NewsAPI feeds before we automate them for your team.")
    
    colA, colB = st.columns(2)
    with colA: alert_school = st.text_input("Alert Target School:", "Boston University")
    with colB: news_api_key_input = st.text_input("NewsAPI Key (for testing):", type="password")
    
    if st.button("Test Alert Feeds"):
        st.markdown(f"**Latest updates for {alert_school}**")
        
        # Google News RSS
        st.markdown("#### From Google News (Free/Real-time)")
        google_results = get_google_news(alert_school)
        if google_results:
            for article in google_results:
                st.write(f"- **[{article['title']}]({article['link']})**")
        else:
            st.write("No relevant Google News found.")
            
        # NewsAPI
        st.markdown("#### From NewsAPI (Structured)")
        if news_api_key_input:
            newsapi_results = get_newsapi_articles(alert_school, news_api_key_input)
            if newsapi_results:
                for article in newsapi_results:
                    st.write(f"- **[{article['title']}]({article['link']})** *(_{article['source']}_)*")
            else:
                st.write("No relevant NewsAPI articles found.")
        else:
            st.warning("Please enter a NewsAPI key to test this feed.")

    st.markdown("---")

    # --- EXISTING STRATEGY 3: STATE MANDATE TRACKER ---
    with st.expander("🏛️ Macro-Trend & State Mandate Tracker", expanded=False):
        st.write("Monitor states passing new legislation or budget mandates for student mental health.")
        state_input = st.text_input("Target State(s)", value="Massachusetts")
        if st.button("Search State Legislation"):
            with st.spinner("Hunting for legislative news..."):
                gn = GNews(language='en', country='US', period='30d', max_results=3)
                leg_news = gn.get_news(f'"{state_input}" AND ("student mental health" OR "campus mental health") AND (mandate OR legislation OR bill OR funding)')
                if leg_news:
                    for n in leg_news:
                        st.markdown(f"**[{n['title']}]({n['url']})** - _{n['published date']}_")
                else:
                    st.info("No major legislative news in the last 30 days.")

    st.markdown("---")
    st.subheader("📰 Deep-Dive Territory Scraper")
    
    schools_input = st.text_area("Target Schools", height=100, placeholder="Boston College\nAssumption University\nPingree School")
    
    colA, colB = st.columns(2)
    with colA: search_type = st.radio("Intelligence Type:", ["General Wellness News", "Grant & Funding Announcements"])
    with colB: use_ai = st.toggle("🤖 Enable AI 'So What?' Summaries (Takes longer)")

    if st.button("Run Territory Scan", type="primary"):
        schools_list = [s.strip() for s in schools_input.split('\n') if s.strip()]
        
        if schools_list:
            master_news_list = []
            progress_bar = st.progress(0, text="Starting search...")
            google_news = GNews(language='en', country='US', period='7d', max_results=3)
            
            competitors = ["timelycare", "mantra health", "talkspace", "betterhelp", "christie campus"]
            partner_keyword = "uwill"
            
            if search_type == "General Wellness News":
                keywords = ["mental health", "wellness", "counseling", "teletherapy", "psychiatric"]
            else:
                keywords = ["grant", "funding", "award", "donation", "million", "budget"]
            
            for index, school in enumerate(schools_list):
                progress_bar.progress((index + 1) / len(schools_list), text=f"Scraping {school}...")
                keyword_string = " OR ".join([f'"{kw}"' for kw in keywords])
                query = f'"{school}" AND "mental health" AND ({keyword_string})'
                
                articles = google_news.get_news(query)
                if articles:
                    for article in articles:
                        title_lower = article['title'].lower()
                        if any(kw in title_lower for kw in keywords):
                            
                            vendor_status = "None Detected"
                            if any(comp in title_lower for comp in competitors):
                                vendor_status = "🚨 COMPETITOR"
                            elif partner_keyword in title_lower:
                                vendor_status = "✅ UWILL MENTION"
                                
                            ai_pitch = "AI Disabled"
                            if use_ai:
                                try:
                                    scraped_text = scrape_article_text(article['url'])
                                    if scraped_text and len(scraped_text) > 100 and api_key:
                                        client = anthropic.Anthropic(api_key=api_key)
                                        prompt = f"You are a BDR. Read this news excerpt: {scraped_text[:2000]}. Provide a 1-sentence summary of the mental health initiative, and a 1-sentence cold email opener referencing it."
                                        msg = client.messages.create(model="claude-3-haiku-20240307", max_tokens=150, messages=[{"role": "user", "content": prompt}])
                                        ai_pitch = msg.content[0].text
                                    else:
                                        ai_pitch = "Could not scrape article text."
                                except:
                                    ai_pitch = "AI Processing Failed."

                            master_news_list.append({
                                'Target Account': school,
                                'Title': article['title'],
                                'Vendor Signal': vendor_status,
                                'AI Angle': ai_pitch,
                                'Published': article['published date'],
                                'URL': article['url']
                            })
                            
            progress_bar.empty()
            
            if master_news_list:
                st.success(f"Found {len(master_news_list)} highly relevant signals!")
                res_df = pd.DataFrame(master_news_list)
                res_df['Published'] = pd.to_datetime(res_df['Published']).dt.strftime('%b %d')
                
                cols_to_show = ['Target Account', 'Vendor Signal', 'Title']
                if use_ai: cols_to_show.append('AI Angle')
                cols_to_show.extend(['Published', 'URL'])
                
                st.dataframe(res_df[cols_to_show], column_config={"URL": st.column_config.LinkColumn("Read")}, hide_index=True, use_container_width=True)
            else:
                st.warning(f"No triggers found for those schools recently.")
        else:
            st.error("Please paste at least one school name.")

# --- TAB 4: BDR ANALYTICS (UNCHANGED) ---
with tab_analytics:
    st.subheader("📈 Workflow Analytics")
    if not st.session_state['prospect_db'].empty:
        df = st.session_state['prospect_db']
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Strategies Generated by Role**")
            st.bar_chart(df['Role'].value_counts())
        with c2:
            st.markdown("**Daily Output Velocity**")
            st.line_chart(df['Date'].value_counts())