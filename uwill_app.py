import streamlit as st
import anthropic
from newspaper import Article
import PyPDF2
import csv
import io

# --- APP CONFIG ---
st.set_page_config(page_title="Uwill Strategic Intel", page_icon="🚀", layout="wide")

# Custom CSS for clean, bold look
st.markdown("""
    <style>
    .main-header {font-size: 2.5rem; font-weight: 800; color: #1E3A8A;}
    .sub-header {font-size: 1.5rem; font-weight: 700; color: #1E3A8A; margin-top: 20px;}
    .card {background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #e9ecef; margin-bottom: 10px;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🚀 Uwill Strategic Intelligence</p>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    # AUTO-LOGIN LOGIC (ROBUST VERSION)
    # Tries to load key from cloud secrets; defaults to text box if running locally.
    try:
        if "ANTHROPIC_API_KEY" in st.secrets:
            st.success("✅ API Key Loaded from Cloud")
            api_key = st.secrets["ANTHROPIC_API_KEY"]
        else:
            api_key = st.text_input("Anthropic API Key", type="password", key="sidebar_key")
    except Exception:
        # If running locally without a secrets file, show the input box
        api_key = st.text_input("Anthropic API Key", type="password", key="sidebar_key")
    
    st.markdown("---")
    st.header("📧 Email Guesser")
    with st.expander("Find Email Format"):
        f_name = st.text_input("First Name", placeholder="e.g. John")
        l_name = st.text_input("Last Name", placeholder="e.g. Doe")
        domain = st.text_input("Domain", placeholder="e.g. bu.edu")
        if f_name and l_name and domain:
            st.markdown(f"**Likely Combos:**")
            st.code(f"{f_name}.{l_name}@{domain}")
            st.code(f"{f_name[0]}{l_name}@{domain}")
            st.code(f"{f_name}{l_name}@{domain}")
    
    st.markdown("---")
    st.header("🎯 Strategy Controls")
    
    email_tone = st.selectbox(
        "Outreach Tone",
        ["Conversational (Sean's Voice)", "Direct & Bold", "Formal & Executive"],
        index=0
    )
    
    focus_point = st.selectbox(
        "Key Pain Point",
        ["Eliminating Waitlists (Speed)", "Diverse Student Needs (Choice)", "Crisis Support", "General/All"],
        index=0
    )
    
    st.markdown("---")
    include_prep = st.checkbox("Include AE Meeting Prep", value=True)
    include_intel = st.checkbox("Include Strategic Intel", value=True)
    
    st.info("🔒 Private Build for Sean O'Connell")

# --- INPUTS ---
col1, col2 = st.columns(2)
with col1:
    university = st.text_input("University Name", key="uni_main")
with col2:
    target_role = st.text_input("Target Role", value="Director of Counseling", key="role_main")

# --- RECONNAISSANCE DASHBOARD ---
if university:
    st.markdown("### 🕵️‍♂️ Quick Recon Links")
    r_col1, r_col2, r_col3, r_col4 = st.columns(4)
    
    # 1. LinkedIn Search
    with r_col1:
        if target_role:
            li_query = f"{target_role} {university} site:linkedin.com/in/"
            st.markdown(f"👉 **[Find on LinkedIn](https://www.google.com/search?q={li_query.replace(' ', '+')})**")
    
    # 2. "Dirty Laundry" Search (Student Newspaper)
    with r_col2:
        news_query = f"{university} student newspaper mental health waitlist crisis"
        st.markdown(f"📰 **[Scan Student News](https://www.google.com/search?q={news_query.replace(' ', '+')})**")
    
    # 3. Staff Directory Search
    with r_col3:
        staff_query = f"{university} counseling center staff directory"
        st.markdown(f"👥 **[Find Staff List](https://www.google.com/search?q={staff_query.replace(' ', '+')})**")
        
    # 4. Strategic Plan Search
    with r_col4:
        strat_query = f"{university} strategic plan 2030 student wellness"
        st.markdown(f"📈 **[Find Strategic Plan](https://www.google.com/search?q={strat_query.replace(' ', '+')})**")

st.markdown("---")
tab1, tab2 = st.tabs(["Link Scraper", "PDF Upload"])

with tab1:
    url = st.text_input("Paste Research Link", key="url_input")

with tab2:
    uploaded_file = st.file_uploader("Upload a PDF", type="pdf", key="pdf_input")

# --- EXECUTION ---
if st.button("Generate Campaign"):
    research_text = ""
    
    # 1. Gather Research
    if url:
        try:
            with st.spinner("Reading the news..."):
                article = Article(url)
                article.download()
                article.parse()
                research_text = "".join(c for c in article.text if c.isprintable())[:4000]
        except: st.error("Link error. Please check the URL.")
    
    elif uploaded_file:
        try:
            with st.spinner("Analyzing PDF..."):
                reader = PyPDF2.PdfReader(uploaded_file)
                for page in reader.pages:
                    research_text += page.extract_text()
                research_text = "".join(c for c in research_text if c.isprintable())[:4000]
        except: st.error("PDF error. Please try a different file.")

    # 2. Run AI Logic
    if research_text and api_key:
        try:
            client = anthropic.Anthropic(api_key=api_key)
            with st.spinner("Drafting campaign in your voice..."):
                
                # THE "HUMAN VOICE" PROMPT
                prompt = f"""
                ROLE: You are Sean O'Connell, a BDR at Uwill. You are helpful, human, and direct.
                PROSPECT: {target_role} at {university}.
                RESEARCH: "{research_text}"
                
                SETTINGS:
                - TONE: {email_tone}
                - FOCUS: {focus_point}
                
                INSTRUCTIONS:
                1. WRITE LIKE A HUMAN: Use "I" statements ("I noticed," "I was reading"). Avoid "We at Uwill" or robotic marketing speak.
                2. BE SPECIFIC: Cite the specific page, quote, or initiative from the research.
                3. BE BRIEF: No long intros. Get to the point.
                
                OUTPUT FORMAT (Use Markdown for Bold Headers):
                
                ### **1. Subject Lines**
                (Provide 3 options: Short, casual, lower-case is okay)

                ### **2. Cold Email Draft**
                (Max 120 words. Structure: Context -> Problem -> {focus_point} Solution -> 'Worth a chat?')

                ### **3. LinkedIn DM**
                (Casual. Under 300 chars. Reference the research.)

                ### **4. Voicemail Script**
                (30 seconds. Natural speech patterns.)

                """
                
                if include_prep:
                    prompt += """
                    ---
                    ### **5. AE Meeting Prep**
                    - **3 Discovery Questions** (Based on text gaps)
                    - **"Why Now?"** (Urgency driver)
                    - **Objection Handling** (Anticipate one pushback)
                    """

                if include_intel:
                    prompt += """
                    ---
                    ### **6. Strategic Intel**
                    - **Fit Score (0-10):** (Rate urgency)
                    - **Competitor Radar:** (Flag any mentions)
                    - **Stakeholders:** (List 2 other titles to target)
                    """

                message = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=2500,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                campaign_content = message.content[0].text
                
                # Display Results
                st.markdown("---")
                st.markdown(f'<p class="sub-header">Strategy for {university}</p>', unsafe_allow_html=True)
                
                with st.container():
                    st.write(campaign_content)
                
                # --- CSV EXPORT ---
                csv_buffer = io.StringIO()
                writer = csv.writer(csv_buffer)
                writer.writerow(["University", "Role", "Tone", "Focus", "Full Intelligence Pack"])
                writer.writerow([university, target_role, email_tone, focus_point, campaign_content])
                
                st.download_button(
                    label="Download Intelligence CSV",
                    data=csv_buffer.getvalue(),
                    file_name=f"{university}_intel.csv",
                    mime="text/csv"
                )
                
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please provide an API Key and some research (Link or PDF).")
