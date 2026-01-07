import streamlit as st
import google.generativeai as genai
from tavily import TavilyClient
import json
import pandas as pd
import os
import sys
import re
from dotenv import load_dotenv

# Fix path to allow importing from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

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
    # User suggested gemini-flash-latest as the safest option
    # We try 'gemini-flash-latest' first, then 'gemini-2.0-flash-lite', then 'gemini-1.5-flash'
    models_to_try = ['gemini-flash-latest', 'gemini-2.0-flash-lite', 'gemini-1.5-flash']
    
    for model_name in models_to_try:
        try:
            # print(f"Trying model: {model_name}")
            m = genai.GenerativeModel(model_name)
            return m
        except: continue
            
    return genai.GenerativeModel('gemini-flash-latest')

def parse_raw_text_with_gemini(text, api_key):
    if not api_key:
        st.error("❌ Missing Google API Key")
        return []
    try:
        model = get_generative_model(api_key)
        # st.toast(f"Using Model: {model.model_name}", icon="🤖")
        
        prompt = """
        Extract course info from this text.
        Output JSON list: [{"code": "...", "name": "...", "professor": "...", "time": "..."}]
        Rules:
        1. If professor is missing/Staff, use "TBD".
        2. Extract Time if available (e.g., "Mon 2:00PM", "TBD").
        3. Merge sections.
        4. **Auto-correct typos**: Fix professor names (e.g. "Linda Selie" -> "Linda Sellie") and course names.
        5. **Standardize Codes**: Use full format (e.g. "CS6033" -> "CS-GY 6033").
        Text:
        """ + text[:50000] # Reduced limit to be safe
        
        response = model.generate_content(prompt)
        return extract_json_from_text(response.text)
    except Exception as e:
        st.error(f"Parse Error ({type(e).__name__}): {e}")
        return []

def fetch_degree_requirements(school, major, api_key):
    try:
        tavily = TavilyClient(api_key=api_key)
        query = f"{school} {major} degree requirements core courses electives pdf"
        result = tavily.search(query=query, search_depth="advanced", max_results=3)
        return "\n".join([f"- {r['content']} (Source: {r['url']})" for r in result['results']])
    except:
        return "Could not fetch requirements."

from src.engine.judge import JudgeAgent

def analyze_course_with_tavily(course_info, user_query, user_profile, req_context, tavily_api_key, google_api_key):
    try:
        tavily = TavilyClient(api_key=tavily_api_key)
        prof_name = clean_professor_name(course_info['professor'])
        
        # --- 1. Data Gathering (Agent A) ---
        results = []
        
        # RMP Search
        if prof_name != "TBD":
            rmp_query = f"{prof_name} {user_profile.get('school', '')} Rate My Professors"
            rmp_result = tavily.search(query=rmp_query, search_depth="advanced", max_results=2)
            results.extend(rmp_result['results'])
        
        # Review Search
        if prof_name == "TBD":
            review_query = f"{course_info['code']} {user_profile.get('school', '')} difficulty workload review reddit 1point3acres"
        else:
            review_query = f"{course_info['code']} {prof_name} {user_profile.get('school', '')} rating review difficulty workload reddit 1point3acres"
            
        review_result = tavily.search(query=review_query, search_depth="advanced", max_results=4)
        results.extend(review_result['results'])
        
        # Deduplicate
        seen_urls = set()
        unique_results = []
        for r in results:
            if r['url'] not in seen_urls:
                unique_results.append(r)
                seen_urls.add(r['url'])
        
        # --- 2. The Judge (Agent B) ---
        # Filter content for the Judge (focus on RMP-like content)
        rmp_content = "\n".join([r['content'] for r in unique_results if "Rate My Professors" in r.get('title', '') or "ratemyprofessors" in r.get('url', '')])
        
        judge = JudgeAgent(google_api_key)
        verified_data = judge.extract_rmp_data(rmp_content)
        
        # --- 3. Final Analysis (Tiered Fallback) ---
        context = "\n".join([f"- Content: {r['content']}\n  Source: {r['url']}" for r in unique_results])
        
        # Configure model for JSON output
        model = genai.GenerativeModel('gemini-2.0-flash-lite', generation_config={"response_mime_type": "application/json"})
        
        # --- Goal-Driven Logic ---
        user_goal = user_profile.get('goal', 'General')
        goal_instruction = ""
        
        if "Job" in user_goal or "Career" in user_goal:
            goal_instruction = """
            [Analysis Focus: JOB SEEKING]
            - Highlight skills relevant to industry interviews (e.g. System Design, LeetCode patterns).
            - Does this course have projects suitable for a resume?
            - If the course is too theoretical with no practical application, warn the user.
            """
        elif "Research" in user_goal or "PhD" in user_goal:
            goal_instruction = """
            [Analysis Focus: RESEARCH/PhD]
            - Focus on the professor's lab and publication reputation.
            - Is the content rigorous enough for research prep?
            - Ignore "workload is heavy" complaints if the depth is worth it.
            """
        elif "Easy" in user_goal or "Booster" in user_goal:
            goal_instruction = """
            [Analysis Focus: GPA BOOSTER]
            - CRITICAL: Check grading distribution and workload hours.
            - If the course is "useful but hard", mark it as CAUTION for this user.
            - Highlight "easy A" aspects.
            """
        else:
            goal_instruction = """
            [Analysis Focus: GENERAL]
            - Balance practical skills with academic depth.
            - Highlight any red flags regarding organization or teaching quality.
            """

        summary_prompt = f"""
        You are an expert academic advisor.
        
        Task: Analyze the course and provide a structured JSON report.
        
        {goal_instruction}
        
        [Real Data from Judge (RMP)]
        Has Data: {verified_data['has_data']}
        RMP Rating: {verified_data['rmp_rating']}
        Difficulty: {verified_data['difficulty']}
        Summary: {verified_data['summary']}
        
        [Context & Reviews]
        Course: {course_info['code']} - {prof_name}
        Profile: {user_profile.get('school')}, {user_profile.get('major')}, Goal: {user_profile.get('goal')}
        Requirements: {req_context}
        Reviews: {context}
        
        [Fallback Logic]
        1. **Level 1 (RMP)**: If 'Has Data' is True, use Judge data. Set 'data_source' = "RMP Verified".
        2. **Level 2 (Reddit)**: If 'Has Data' is False, look for Reddit/Forum reviews in [Context]. If found, extract sentiment. Set 'data_source' = "Reddit Consensus".
        3. **Level 3 (AI)**: If no data found, estimate based on your knowledge of the course/professor. Set 'data_source' = "AI Estimate".
        
        Output JSON Schema:
        {{
            "data_source": "RMP Verified" | "Reddit Consensus" | "AI Estimate",
            "quick_stats": {{
                "rating": float | null,
                "difficulty": float | null,
                "workload": "High" | "Medium" | "Low",
                "grading": "Tough" | "Fair" | "Easy"
            }},
            "verdict": {{
                "status": "Recommended" | "Caution" | "Avoid",
                "reason": "string (Mix En/Ch)",
                "badge_color": "green" | "yellow" | "red"
            }},
            "deep_dive": {{
                "workload_details": "string (with inline citations)",
                "professor_vibe": "string (with inline citations)",
                "forum_chatter": "string (with inline citations)"
            }},
            "heads_up": ["string (actionable advice)"]
        }}
        """
        response = model.generate_content(summary_prompt)
        return response.text
    except Exception as e:
        return json.dumps({"error": str(e)})

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
            # --- Smart Input Reset ---
            if 'last_selected' not in st.session_state:
                st.session_state['last_selected'] = []
            
            # Check if selection changed
            if st.session_state['last_selected'] != selected:
                st.session_state['user_req_input'] = "Workload? Grading?" # Reset to default
                st.session_state['last_selected'] = selected
            
            user_req = st.text_input("Specific Questions (Optional):", value="Workload? Grading?", key="user_req_input")
            if st.button("🚀 Launch Analysis"):
                if not tavily_api_key:
                    st.error("Tavily API Key required!")
                else:
                    st.markdown("---")
                    for item in selected:
                        idx = course_options.index(item)
                        course_obj = st.session_state['courses'][idx]
                        
                        with st.status(f"🕵️ Analyzing {course_obj['code']}...", expanded=True) as status:
                            result_json = analyze_course_with_tavily(course_obj, user_req, st.session_state['user_profile'], st.session_state['req_context'], tavily_api_key, google_api_key)
                            status.update(label=f"✅ {course_obj['code']} Ready", state="complete", expanded=False)
                        
                        try:
                            data = json.loads(result_json)
                            if "error" in data:
                                st.error(f"Analysis Error: {data['error']}")
                            else:
                                # --- Render Structured UI ---
                                source_badge = data.get('data_source', 'Unknown')
                                source_color = "#48bb78" if "RMP" in source_badge else "#ecc94b" if "Reddit" in source_badge else "#a0aec0"
                                
                                st.markdown(f"""
                                <div class="glass-card">
                                    <div style="display:flex; justify-content:space-between; align_items:center;">
                                        <h3 class="highlight-text" style="margin:0;">📘 {course_obj['code']}</h3>
                                        <span style="background-color:{source_color}; color:white; padding:4px 8px; border-radius:12px; font-size:0.8em;">{source_badge}</span>
                                    </div>
                                """, unsafe_allow_html=True)
                                
                                # 1. Quick Stats Row
                                qs = data.get("quick_stats", {})
                                c1, c2, c3, c4 = st.columns(4)
                                with c1: st.metric("RMP Rating", f"{qs.get('rating') or 'N/A'}/5")
                                with c2: st.metric("Difficulty", f"{qs.get('difficulty') or 'N/A'}/5")
                                with c3: st.metric("Workload", qs.get('workload', 'N/A'))
                                with c4: st.metric("Grading", qs.get('grading', 'N/A'))
                                
                                # 2. Verdict Badge
                                v = data.get("verdict", {})
                                color_map = {"green": "#48bb78", "yellow": "#ecc94b", "red": "#f56565"}
                                badge_color = color_map.get(v.get("badge_color"), "#a0aec0")
                                st.markdown(f"""
                                <div style="background-color: {badge_color}; padding: 15px; border-radius: 10px; color: white; margin: 15px 0;">
                                    <h4 style="margin:0;">💡 Verdict: {v.get('status')}</h4>
                                    <p style="margin:5px 0 0 0;">{v.get('reason')}</p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # 3. Deep Dive
                                dd = data.get("deep_dive", {})
                                with st.expander("📝 Deep Dive (Workload & Vibe)", expanded=True):
                                    st.markdown(f"**Workload & Grading**:\n{dd.get('workload_details')}")
                                    st.markdown(f"**Professor Vibe**:\n{dd.get('professor_vibe')}")
                                    st.markdown(f"**Forum Chatter**:\n{dd.get('forum_chatter')}")
                                
                                # 4. Heads Up
                                if data.get("heads_up"):
                                    st.warning("⚠️ **Heads Up:**\n" + "\n".join([f"- {h}" for h in data['heads_up']]))
                                
                                st.markdown("</div>", unsafe_allow_html=True)

                        except json.JSONDecodeError:
                            # Fallback for raw text (if model failed JSON mode)
                            st.markdown(f"""<div class="glass-card"><h3 class="highlight-text">📘 {course_obj['code']}</h3>{result_json}</div>""", unsafe_allow_html=True)

        # Step 3: Recommend
        st.markdown("### 3️⃣ Strategic Planning (排课推荐)")
        if st.button("🧠 Generate Optimal Schedule"):
            if not tavily_api_key:
                st.error("Tavily API Key required!")
            else:
                with st.spinner("🧠 Computing optimal paths..."):
                    rec_result = generate_schedule_recommendations(st.session_state['courses'], st.session_state['user_profile'], st.session_state['req_context'], google_api_key)
                    st.markdown(f"""<div class="glass-card" style="border-left: 5px solid #48bb78;"><h3>🧠 AI Schedule Recommendation</h3>{rec_result}</div>""", unsafe_allow_html=True)
