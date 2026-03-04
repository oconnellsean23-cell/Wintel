import streamlit as st
import anthropic
import PyPDF2
import pandas as pd
import urllib.parse
from datetime import date
from gnews import GNews
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
tab_research, tab_pool, tab_news = st.tabs(["🎯 New Research", "📊 Team Prospect Pool", "📰 Territory News"])

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
# --- 5. TERRITORY NEWS SCRAPER ---
with tab_news:
    st.subheader("📰 Territory News Scraper")
    st.write("Scrape the latest student wellness and mental health initiatives by school.")

    # 1. Swapped to text_area so you can paste a list
    schools_input = st.text_area(
        "Target Schools (Paste a list, one school per line)", 
        key="news_target_schools", 
        height=150,
        placeholder="Boston College\nAssumption University\nPingree School"
    )
    
    timeframe = st.selectbox("Timeframe:", ["1d", "7d", "30d"], key="news_timeframe")

    if st.button("Search Territory", type="primary"):
        # Convert the pasted text into a clean Python list
        schools_list = [school.strip() for school in schools_input.split('\n') if school.strip()]
        
        if schools_list:
            # We need a master list to hold the articles from all schools
            master_news_list = []
            
            # Setup a visual progress bar so the team knows it's working
            progress_bar = st.progress(0, text="Starting search...")
            
            google_news = GNews(language='en', country='US', period=timeframe, max_results=5)
            
            # The exact keywords we demand to see
            keywords = ["mental health", "wellness", "counseling", "teletherapy", "therapy", "well-being", "psychiatric"]
            
            for index, school in enumerate(schools_list):
                # Update the progress bar for each school
                progress_percentage = (index + 1) / len(schools_list)
                progress_bar.progress(progress_percentage, text=f"Scraping {school}...")
                
                # The broad Google search
                keyword_string = " OR ".join([f'"{kw}"' for kw in ["mental health", "student wellness", "counseling"]])
                query = f'"{school}" AND ({keyword_string})'
                
                articles = google_news.get_news(query)
                
                if articles:
                    for article in articles:
                        title_lower = article['title'].lower()
                        
                        # 2. THE DIALED-IN FILTER: Only keep it if a keyword is actually in the title
                        if any(kw in title_lower for kw in keywords):
                            # Tag the article with the school name so we know who it belongs to
                            article['Target Account'] = school
                            master_news_list.append(article)
            
            # Clear the progress bar when done
            progress_bar.empty()
            
            # Display the final, filtered results
            if master_news_list:
                st.success(f"Found {len(master_news_list)} highly relevant articles across your territory!")
                
                df = pd.DataFrame(master_news_list)
                
                # Reorder and select columns (now including the Target Account)
                df = df[['Target Account', 'title', 'published date', 'url']]
                
                # Clean up the date
                df['published date'] = pd.to_datetime(df['published date']).dt.strftime('%b %d, %Y')
                
                st.dataframe(
                    df,
                    column_config={
                        "Target Account": "School",
                        "title": "Article Title",
                        "published date": "Date Published",
                        "url": st.column_config.LinkColumn("Read Article")
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.warning("No highly relevant mental health news found for those schools in that timeframe.")
        else:
            st.error("Please paste at least one school name first.")