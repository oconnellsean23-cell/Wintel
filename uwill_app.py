import streamlit as st
import anthropic
import PyPDF2
import pandas as pd
import json
import os
import urllib.parse
from datetime import date
import logging

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONSTANTS ---
MODEL_NAME = "claude-3-haiku-20240307"
MAX_TOKENS = 2000
PDF_CHAR_LIMIT = 12000
DB_FILE = "prospect_db.json"

COMMON_ROLES = [
    "Director of Counseling",
    "VP of Student Affairs", 
    "Dean of Students",
    "Director of Mental Health",
    "Counseling Center Director",
    "Other (Custom)"
]

# --- APP CONFIG ---
st.set_page_config(page_title="Wintel: Team Intel", page_icon="🚀", layout="wide")

# --- DATABASE FUNCTIONS ---
def load_database():
    """Load prospect database from JSON file with fallback to session state"""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                data = json.load(f)
                return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error loading database: {e}")
            return pd.DataFrame(columns=['Date','University','Role','Priority','Status','Output_Preview'])
    return pd.DataFrame(columns=['Date','University','Role','Priority','Status','Output_Preview'])

def save_database(db):
    """Persist prospect database to JSON file"""
    try:
        db.to_json(DB_FILE, orient='records', indent=2)
    except Exception as e:
        logger.error(f"Error saving database: {e}")
        st.error("⚠️ Could not persist database to disk")

# Initialize or load database
if 'prospect_db' not in st.session_state:
    st.session_state['prospect_db'] = load_database()

# --- VALIDATION FUNCTIONS ---
def validate_input(value, field_name, min_length=2):
    """Validate text input"""
    if not value or len(value.strip()) < min_length:
        raise ValueError(f"{field_name} must be at least {min_length} characters long")
    return value.strip()

def validate_api_key(api_key):
    """Test if API key is valid by making a simple call"""
    if not api_key:
        raise ValueError("API key is required")
    try:
        client = anthropic.Anthropic(api_key=api_key)
        # Test with a minimal call
        client.messages.create(
            model=MODEL_NAME,
            max_tokens=10,
            messages=[{"role": "user", "content": "test"}]
        )
        return True
    except anthropic.AuthenticationError:
        raise ValueError("Invalid API key. Please check your Anthropic API key.")
    except anthropic.RateLimitError:
        raise ValueError("API rate limit exceeded. Please wait a moment and try again.")
    except anthropic.APIError as e:
        raise ValueError(f"API error: {str(e)}")

# --- HELPER FUNCTIONS ---
def extract_pdf_text(uploaded_file):
    """Extract text from PDF with error handling"""
    try:
        reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page_num, page in enumerate(reader.pages):
            try:
                text += page.extract_text()
            except Exception as e:
                logger.warning(f"Could not extract page {page_num}: {e}")
                continue
        
        if not text.strip():
            raise ValueError("PDF appears to be empty or unreadable")
        
        # Truncate with warning if necessary
        if len(text) > PDF_CHAR_LIMIT:
            st.warning(f"📄 PDF truncated from {len(text):,} to {PDF_CHAR_LIMIT:,} characters for processing")
            text = text[:PDF_CHAR_LIMIT]
        
        st.info(f"✅ Extracted {len(text):,} characters from PDF")
        return text
    except PyPDF2.PdfReadError as e:
        raise ValueError(f"PDF read error: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error processing PDF: {str(e)}")

def generate_ai_output(api_key, research_text, target_role, university):
    """Generate AI analysis with comprehensive error handling"""
    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        prompt = f"""Role: Sean O'Connell, BDR at Uwill

Research Material: {research_text}

Task: Generate a sales research package for {target_role} at {university}. Include:

1. **THREE SUBJECT LINES** (Most compelling first)
   - Subject line 1: 
   - Subject line 2: 
   - Subject line 3: 

2. **PERSONALIZED EMAIL DRAFT**
   [Write a compelling but natural 150-200 word email that references specific details from the research]

3. **AE BRIEFING NOTES**
   - Key insight #1:
   - Key insight #2:
   - Suggested follow-up:
   - Priority Score (1-10):
   - Confidence Level (High/Medium/Low):

Make the content specific, actionable, and ready to use immediately."""

        with st.spinner("🤖 Claude is analyzing your research..."):
            message = client.messages.create(
                model=MODEL_NAME,
                max_tokens=MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}]
            )
        
        return message.content[0].text
    
    except anthropic.AuthenticationError:
        raise ValueError("❌ API Authentication failed. Please check your API key.")
    except anthropic.RateLimitError:
        raise ValueError("❌ API rate limit exceeded. Please wait 60 seconds and try again.")
    except anthropic.APIError as e:
        raise ValueError(f"❌ API Error: {str(e)}")
    except Exception as e:
        raise ValueError(f"❌ Unexpected error: {str(e)}")

def log_prospect_entry(university, role, output):
    """Add entry to prospect database and save to disk"""
    try:
        output_preview = output[:200] + "..." if len(output) > 200 else output
        new_entry = pd.DataFrame([{'
            'Date': str(date.today()), 
            'University': university, 
            'Role': role, 
            'Priority': 'Assessed', 
            'Status': 'Researched',
            'Output_Preview': output_preview
        }])
        st.session_state['prospect_db'] = pd.concat(
            [st.session_state['prospect_db'], new_entry], 
            ignore_index=True
        )
        save_database(st.session_state['prospect_db'])
        return True
    except Exception as e:
        logger.error(f"Error logging prospect: {e}")
        raise ValueError(f"Error saving prospect: {str(e)}")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main-header {font-size: 2.5rem; font-weight: 800; color: #1E3A8A;}
    .card {background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e5e7eb; margin-bottom: 20px; color: #1f2937;}
    .success-card {background-color: #f0fdf4; padding: 20px; border-radius: 12px; border: 2px solid #22c55e; margin-bottom: 20px;}
    .copy-btn {background-color: #3b82f6; color: white; padding: 8px 16px; border-radius: 6px; cursor: pointer;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🚀 Wintel: Team Sales Intelligence</p>', unsafe_allow_html=True)

# --- SIDEBAR: SETTINGS & EMAIL GUESSER ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    # API Key Management
    try:
        if "ANTHROPIC_API_KEY" in st.secrets:
            api_key = st.secrets["ANTHROPIC_API_KEY"]
            st.success("✅ Cloud Key Active")
        else:
            api_key = st.text_input("Anthropic API Key", type="password", key="api_key_input")
            if api_key and st.button("🔐 Validate API Key"):
                try:
                    validate_api_key(api_key)
                    st.success("✅ API Key is valid!")
                except ValueError as e:
                    st.error(str(e))
    except KeyError:
        api_key = st.text_input("Anthropic API Key", type="password", key="api_key_input")
    except Exception as e:
        st.error(f"Settings error: {str(e)}")
        api_key = st.text_input("Anthropic API Key", type="password", key="api_key_input")
    
    st.markdown("---")
    
    # Email Guesser Tool
    st.header("📧 Email Guesser")
    fn = st.text_input("First Name")
    ln = st.text_input("Last Name")
    dom = st.text_input("Domain (e.g. bu.edu)")
    if fn and ln and dom:
        guessed_email = f"{fn.lower()}.{ln.lower()}@{dom}"
        st.code(guessed_email)
        if st.button("📋 Copy Email"):
            st.write(f"```
{guessed_email}
```")

# --- DASHBOARD ---
with st.sidebar:
    st.markdown("---")
    st.header("📊 Dashboard")
    if len(st.session_state['prospect_db']) > 0:
        st.metric("Total Prospects", len(st.session_state['prospect_db']))
        st.metric("Universities", st.session_state['prospect_db']['University'].nunique())
        st.metric("Target Roles", st.session_state['prospect_db']['Role'].nunique())
    else:
        st.info("No prospects researched yet. Start with the 🎯 New Research tab!")

# --- MAIN INTERFACE: TABS ---
tab_research, tab_pool = st.tabs(["🎯 New Research", "📊 Team Prospect Pool"])

# --- TAB 1: NEW RESEARCH ---
with tab_research:
    st.subheader("Enter Research Details")
    
    col1, col2 = st.columns(2)
    with col1:
        university = st.text_input("🎓 University Name", placeholder="e.g., Boston University")
    with col2:
        role_choice = st.selectbox("👔 Target Role", COMMON_ROLES)
        if role_choice == "Other (Custom)":
            target_role = st.text_input("Enter custom role", placeholder="e.g., Chief Student Affairs Officer")
        else:
            target_role = role_choice
    
    # Quick Research Links
    if university:
        st.markdown("### 🕵️‍♂️ Quick Recon Links")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.link_button(
                "🔍 LinkedIn",
                f"https://www.google.com/search?q={urllib.parse.quote(target_role + ' ' + university + ' site:linkedin.com/in/')}")
        with c2:
            st.link_button(
                "📰 Student News",
                f"https://www.google.com/search?q={urllib.parse.quote(university + ' student newspaper mental health')}")
        with c3:
            st.link_button(
                "👥 Directory",
                f"https://www.google.com/search?q={urllib.parse.quote(university + ' counseling staff directory')}")

    st.markdown("---")
    st.subheader("Upload Research Material")
    uploaded_file = st.file_uploader("📄 Upload Strategic Plan or Research (PDF)", type="pdf")
    
    if uploaded_file:
        st.info(f"File selected: {uploaded_file.name}")

    # Generate Strategy Button
    if st.button("🚀 Generate & Log Strategy", use_container_width=True):
        research_text = ""
        errors = []
        
        # Validation
        try:
            university = validate_input(university, "University Name")
            target_role = validate_input(target_role, "Target Role")
        except ValueError as e:
            st.error(f"❌ {str(e)}")
            st.stop()
        
        if not api_key:
            st.error("❌ API key is required. Please enter your Anthropic API key in Settings.")
            st.stop()
        
        if not uploaded_file:
            st.error("❌ Please upload a PDF file to analyze.")
            st.stop()
        
        # Extract PDF
        try:
            research_text = extract_pdf_text(uploaded_file)
        except ValueError as e:
            st.error(f"❌ PDF Error: {str(e)}")
            st.stop()
        
        # Generate AI Output
        try:
            output = generate_ai_output(api_key, research_text, target_role, university)
            
            # Log to database
            log_prospect_entry(university, target_role, output)
            
            # Display results
            st.markdown(f'<div class="success-card"><h3>✅ Strategy Generated Successfully</h3></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card">{output}</div>', unsafe_allow_html=True)
            
            # Copy button
            if st.button("📋 Copy Output to Clipboard"):
                st.code(output, language="text")
            
        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")
            logger.error(f"Generation error: {e}")

# --- TAB 2: PROSPECT POOL ---
with tab_pool:
    st.subheader("📁 Saved Prospect Pool")
    
    if len(st.session_state['prospect_db']) > 0:
        st.dataframe(st.session_state['prospect_db'], use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            csv = st.session_state['prospect_db'].to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export to CSV", csv, "prospect_pool.csv", "text/csv")
        
        with col2:
            json_data = st.session_state['prospect_db'].to_json(orient='records', indent=2).encode('utf-8')
            st.download_button("📥 Export to JSON", json_data, "prospect_pool.json", "application/json")
        
        with col3:
            if st.button("🗑️ Clear All Data"):
                st.session_state['prospect_db'] = pd.DataFrame(columns=['Date','University','Role','Priority','Status','Output_Preview'])
                save_database(st.session_state['prospect_db'])
                st.success("Database cleared!")
                st.rerun()
    else:
        st.info("📭 No prospects saved yet. Start researching in the 🎯 New Research tab!")
