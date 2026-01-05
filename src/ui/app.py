import streamlit as st
import google.generativeai as genai
from tavily import TavilyClient
import json
import pandas as pd
import os
import re
from dotenv import load_dotenv

# Load Env
load_dotenv()

# --- Page Config & Custom CSS (Premium Glassmorphism) ---
st.set_page_config(page_title="Course Pilot v3.1", page_icon="✈️", layout="wide")

st.markdown("""
<style>
    /* Global Background */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    /* Glassmorphism Card */
    .glass-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 30px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
        margin-bottom: 25px;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #2d3748;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #4e54c8 0%, #8f94fb 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.5);
    }
    
    /* Inputs */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        padding: 10px;
    }
    
    /* Custom Classes */
    .highlight-text {
        color: #4e54c8;
        font-weight: bold;
    }
    .metric-box {
        background: #f7fafc;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        border: 1px solid #edf2f7;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if 'profile_confirmed' not in st.session_state:
    st.session_state['profile_confirmed'] = False
if 'user_profile' not in st.session_state:
    st.session_state['user_profile'] = {}

# --- Core Logic Functions ---

def clean_professor_name(name):
    if "," in name:
        parts = name.split(",")
        if len(parts) == 2:
            return f"{parts[1].strip()} {parts[0].strip()}"
    return name

def extract_json_from_text(text):
    try: return json.loads(text)
    except: pass
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        try: return json.loads(match.group(0))
        except: pass
    return []

def get_generative_model(api_key):
    genai.configure(api_key=api_key)
    # gemini-1.5-flash was not found in the available models list.
    # Using gemini-2.0-flash-lite as it is available and cost-effective.
    for model in ['gemini-2.0-flash-lite', 'gemini-flash-latest']:
        try:
            m = genai.GenerativeModel(model)
            # Quick check to ensure model works (optional, can be removed if quota is tight)
            # m.generate_content("Test") 
            return m
        except: continue
    return genai.GenerativeModel('gemini-2.0-flash-lite')

def parse_raw_text_with_gemini(text, api_key):
    if not api_key:
        st.error("❌ Missing Google API Key")
        return []
    try:
        model = get_generative_model(api_key)
        prompt = """
        Extract course info from this text.
        Output JSON list: [{"code": "...", "name": "...", "professor": "...", "time": "..."}]
        Rules:
        1. If professor is missing/Staff, use "TBD".
        2. Extract Time if available (e.g., "Mon 2:00PM", "TBD").
        3. Merge sections.
        Text:
        """ + text[:100000]
        response = model.generate_content(prompt)
        return extract_json_from_text(response.text)
    except Exception as e:
        st.error(f"Parse Error: {e}")
        return []

def fetch_degree_requirements(school, major, api_key):
    try:
        tavily = TavilyClient(api_key=api_key)
        query = f"{school} {major} degree requirements core courses electives pdf"
        result = tavily.search(query=query, search_depth="advanced", max_results=3)
        return "\n".join([f"- {r['content']} (Source: {r['url']})" for r in result['results']])
    except:
        return "Could not fetch requirements."

def analyze_course_with_tavily(course_info, user_query, user_profile, req_context, api_key):
    try:
        tavily = TavilyClient(api_key=api_key)
        prof_name = clean_professor_name(course_info['professor'])
        
        results = []
        
        # 1. RMP Specific Search (Targeting Stats)
        if prof_name != "TBD":
            rmp_query = f"{prof_name} {user_profile.get('school', '')} Rate My Professors"
            rmp_result = tavily.search(query=rmp_query, search_depth="advanced", max_results=2)
            results.extend(rmp_result['results'])
        
        # 2. General Review Search (Reddit, 1point3acres, Course Code)
        if prof_name == "TBD":
            review_query = f"{course_info['code']} {user_profile.get('school', '')} difficulty workload review reddit 1point3acres"
        else:
            review_query = f"{course_info['code']} {prof_name} {user_profile.get('school', '')} rating review difficulty workload reddit 1point3acres"
            
        review_result = tavily.search(query=review_query, search_depth="advanced", max_results=4)
        results.extend(review_result['results'])
        
        # 3. Extract RMP Stats (Lightweight Logic)
        rmp_rating = "N/A"
        rmp_summary = "No specific RMP summary found."
        
        # Try to find rating in RMP results
        for r in results:
            if "Rate My Professors" in r.get('title', '') or "ratemyprofessors.com" in r.get('url', ''):
                # Look for "X.X" or "Rating: X.X"
                match = re.search(r'(\d\.\d)/5', r['content'])
                if match:
                    rmp_rating = match.group(1)
                    rmp_summary = r['content'][:300] + "..." # Use snippet as summary
                    break
                
                # Fallback: Look for just a float like 3.5
                match_loose = re.search(r'\b([1-5]\.\d)\b', r['content'])
                if match_loose:
                    rmp_rating = match_loose.group(1)
                    rmp_summary = r['content'][:300] + "..."
                    break

        context = "\n".join([f"- Content: {r['content']}\n  Source: {r['url']}" for r in unique_results])
        
        model = get_generative_model(os.getenv("GOOGLE_API_KEY"))
        
        summary_prompt = f"""
        You are an expert academic advisor. 
        Analyze the course based on the following REAL data:
        
        Course: {course_info['code']}
        Professor: {prof_name}
        
        --- REAL RMP DATA ---
        Rating: {rmp_rating}/5
        Student Summary: {rmp_summary}
        ---------------------
        
        [Profile] School: {user_profile.get('school')}, Major: {user_profile.get('major')}, Goal: {user_profile.get('goal')}
        [Requirements] {req_context}
        [Reviews & Data] 
        {context}
        
        [Output - Markdown]
        ### 📊 Quick Stats (Professor: {prof_name})
        *   **RMP Rating**: {rmp_rating}/5 (Source: RateMyProfessors)
        *   **Would Take Again**: [Extract % from Reviews] or "N/A"
        *   **Difficulty**: [Extract X.X/5 from Reviews] or "N/A"
        *   **Graduation**: [Core/Elective based on Requirements]
        *   **Workload**: [High/Medium/Low]
        *   **Grading**: [Tough/Fair/Easy]
        
        ### 💡 Verdict: [Recommended/Caution/Avoid]
        (Explain based on goal "{user_profile.get('goal')}". Mix En/Ch.)
        
        ### 📝 Deep Dive (Comprehensive Review)
        *   **Workload & Grading**: 
            (Synthesize reviews from RMP, Reddit, etc. **MUST cite sources inline**, e.g., "RMP users say exams are hard (Source: [Link]).")
        *   **Professor Vibe**: 
            (Teaching style, accent, helpfulness. **Cite sources**.)
        *   **Forum Chatter**: 
            (Specific insights from Reddit/1point3acres. **Cite sources**.)
        
        ### ⚠️ Heads Up (Actionable)
        *   (Specific advice)
        """
        response = model.generate_content(summary_prompt)
        return response.text
    except Exception as e:
        return f"Analysis Error: {str(e)}"

def generate_schedule_recommendations(courses, user_profile, req_context, api_key):
    try:
        model = get_generative_model(api_key)
        course_list_str = "\n".join([f"- {c['code']} {c['name']} ({c['professor']})" for c in courses])
        prompt = f"""
        Role: "CourseMate" (Strategic Advisor).
        Task: Recommend a course combination.
        [Profile] School: {user_profile.get('school')}, Major: {user_profile.get('major')}, Goal: {user_profile.get('goal')}, Past: {user_profile.get('transcript')}
        [Requirements] {req_context}
        [Available] {course_list_str}
        
        [Output]
        1. **Recommended Combination**: Pick 3-4 courses.
        2. **Strategy**: Why this combo?
        3. **Gap Analysis**: What's missing?
        Use Mixed En/Ch.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"

# --- UI Logic ---

# 1. Onboarding Screen (If profile not confirmed)
if not st.session_state['profile_confirmed']:
    st.markdown("<h1 style='text-align: center; color: white; margin-bottom: 30px;'>✈️ Welcome to Course Pilot v3.1</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="glass-card">
            <h3 style="text-align: center;">🛠️ First, let's set up your profile</h3>
            <p style="text-align: center; color: #666;">To give you the best advice, I need to know where you're flying.</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("onboarding_form"):
            school = st.text_input("🏫 School / University (学校)", placeholder="e.g. NYU Tandon")
            major = st.text_input("🎓 Major (专业)", placeholder="e.g. Computer Science")
            year = st.selectbox("📅 Current Year (年级)", ["Master 1st Year", "Master 2nd Year", "PhD", "Undergrad"])
            transcript = st.text_area("📜 Transcript / Past Courses (已修课程)", placeholder="Paste your past courses here...", height=100)
            
            c1, c2 = st.columns(2)
            with c1:
                submitted = st.form_submit_button("✅ Save & Continue")
            with c2:
                skipped = st.form_submit_button("⏩ Skip for Now")
        
        if submitted:
            if school and major:
                st.session_state['user_profile'] = {
                    "school": school, "major": major, "year": year, "transcript": transcript, "goal": "Job Seeking", "avoid": []
                }
                st.session_state['profile_confirmed'] = True
                st.rerun()
            else:
                st.error("Please fill in School and Major!")
        
        if skipped:
            st.session_state['user_profile'] = {
                "school": "Unknown", "major": "Unknown", "year": "Unknown", "transcript": "", "goal": "Job Seeking", "avoid": []
            }
            st.session_state['profile_confirmed'] = True
            st.rerun()

# 2. Main Interface (If profile confirmed)
else:
    # Sidebar (Collapsed/Mini Profile)
    with st.sidebar:
        st.markdown("## ⚙️ Flight Controls")
        
        with st.expander("👤 Pilot Profile", expanded=True):
            p = st.session_state['user_profile']
            st.write(f"**School:** {p.get('school')}")
            st.write(f"**Major:** {p.get('major')}")
            if st.button("✏️ Edit Profile"):
                st.session_state['profile_confirmed'] = False
                st.rerun()
        
        st.markdown("### 🎯 Mission Goal")
        goal = st.radio("Goal", ["Job Seeking (找工)", "PhD/Research (读博)", "Easy A (水学分)", "Hardcore Tech (硬核)"], index=0)
        st.session_state['user_profile']['goal'] = goal
        
        st.markdown("### 🚫 No-Fly Zone")
        avoid_8am = st.checkbox("No 8am")
        avoid_math = st.checkbox("No Heavy Math")
        avoid_essay = st.checkbox("No Essays")
        st.session_state['user_profile']['avoid'] = []
        if avoid_8am: st.session_state['user_profile']['avoid'].append("8am classes")
        if avoid_math: st.session_state['user_profile']['avoid'].append("heavy math")
        if avoid_essay: st.session_state['user_profile']['avoid'].append("heavy writing")
        
    # Main Content
    st.markdown("""
    <div class="glass-card">
        <h1 style="margin:0;">✈️ Course Pilot <span style="font-size:0.5em; color:#666;">v3.1</span></h1>
        <p>Your Intelligent Course Advisor</p>
    </div>
    """, unsafe_allow_html=True)

    # Load Keys from Env
    google_api_key = os.getenv("GOOGLE_API_KEY", "")
    tavily_api_key = os.getenv("TAVILY_API_KEY", "")

    # Step 1: Paste
    st.markdown("### 1️⃣ Upload Flight Data (上传选课数据)")
    raw_text = st.text_area("", height=150, placeholder="Paste your course list here (Ctrl+V)...")
    
    if st.button("🔍 Parse Data (解析数据)"):
        if raw_text:
            with st.spinner("🤖 Decoding messy text..."):
                parsed = parse_raw_text_with_gemini(raw_text, google_api_key)
                if parsed:
                    st.session_state['courses'] = parsed
                    st.success(f"✅ Found {len(parsed)} courses!")

    # Step 2: Analyze
    if 'courses' in st.session_state and st.session_state['courses']:
        st.markdown("### 2️⃣ Select Targets & Analyze")
        
        # TBD Warning
        tbd_courses = [c['code'] for c in st.session_state['courses'] if c['professor'] == "TBD"]
        if tbd_courses:
            st.warning(f"⚠️ TBD Professors detected: {', '.join(tbd_courses)}")
        
        # Table
        df = pd.DataFrame(st.session_state['courses'])
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        course_options = [f"{c['code']} | {c['professor']}" for c in st.session_state['courses']]
        selected = st.multiselect("Select Courses (可多选):", course_options)
        
        # Fetch Requirements Logic
        if 'req_context' not in st.session_state:
            if st.session_state['user_profile'].get('school') != "Unknown":
                with st.spinner("📜 Fetching degree requirements..."):
                    st.session_state['req_context'] = fetch_degree_requirements(
                        st.session_state['user_profile']['school'], 
                        st.session_state['user_profile']['major'], 
                        tavily_api_key
                    )
            else:
                st.session_state['req_context'] = "No requirements fetched (School Unknown)."

        if selected:
            user_req = st.text_input("Specific Questions (Optional):", value="Workload? Grading?")
            if st.button("🚀 Launch Analysis"):
                if not tavily_api_key:
                    st.error("Tavily API Key required!")
                else:
                    st.markdown("---")
                    for item in selected:
                        idx = course_options.index(item)
                        course_obj = st.session_state['courses'][idx]
                        
                        with st.status(f"🕵️ Analyzing {course_obj['code']}...", expanded=True) as status:
                            result = analyze_course_with_tavily(course_obj, user_req, st.session_state['user_profile'], st.session_state['req_context'], tavily_api_key)
                            status.update(label=f"✅ {course_obj['code']} Ready", state="complete", expanded=False)
                        
                        st.markdown(f"""<div class="glass-card"><h3 class="highlight-text">📘 {course_obj['code']}</h3>{result}</div>""", unsafe_allow_html=True)

        # Step 3: Recommend
        st.markdown("### 3️⃣ Strategic Planning (排课推荐)")
        if st.button("🧠 Generate Optimal Schedule"):
            if not tavily_api_key:
                st.error("Tavily API Key required!")
            else:
                with st.spinner("🧠 Computing optimal paths..."):
                    rec_result = generate_schedule_recommendations(st.session_state['courses'], st.session_state['user_profile'], st.session_state['req_context'], google_api_key)
                    st.markdown(f"""<div class="glass-card" style="border-left: 5px solid #48bb78;"><h3>🧠 AI Schedule Recommendation</h3>{rec_result}</div>""", unsafe_allow_html=True)
