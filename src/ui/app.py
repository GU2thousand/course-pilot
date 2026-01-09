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
        You are a strict data extraction assistant.
        Extract course info from this text.
        
        Output JSON list: [{"code": "...", "name": "...", "professor": "..."}]
        
        Rules:
        1. **Professor Name**: Look for "Instructor:", "Prof.", or names after the course title. 
           - IGNORE locations (e.g. "Jacobs Building", "Room 101").
           - IGNORE times (e.g. "Mon 2:00PM").
           - If not found, use "TBD".
        2. **Course Code**: Standardize to full format (e.g. "CS-GY 6033").
        3. **Course Name**: Full title.
        4. **Auto-correct**: Fix obvious typos in names (e.g. "Linda Selie" -> "Linda Sellie").
        
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

def analyze_course_with_tavily(course_info, user_query, user_profile, req_context, tavily_api_key, google_api_key, status_container=None):
    try:
        tavily = TavilyClient(api_key=tavily_api_key)
        prof_name = clean_professor_name(course_info['professor'])
        
        # --- 1. Data Gathering (Agent A) ---
        if status_container: status_container.write(f"🌐 Searching RMP & Reddit for **{prof_name}**...")
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
        
        if status_container: status_container.write("⚖️ Judge Agent verifying data...")
        judge = JudgeAgent(google_api_key)
        verified_data = judge.extract_rmp_data(rmp_content)
        
        # --- 3. Final Analysis (Tiered Fallback) ---
        if status_container: status_container.write(f"🧠 Generating advice for **{user_profile.get('goal')}**...")
        context = "\n".join([f"- Content: {r['content']}\n  Source: {r['url']}" for r in unique_results])
        
        # --- System Instruction (Strategic Advisor Persona) ---
        system_instruction = """
        # ROLE
        You are a sharp, pragmatic, and critically-minded academic advising agent for NYU Tandon students.
        Your job is NOT to praise courses; your job is to help students make informed trade-offs and optimize outcomes.

        # CORE MISSION
        You must help students navigate:
        1. course content alignment
        2. workload and GPA risks
        3. internship/job-seeking constraints
        4. opportunity cost (e.g., LeetCode vs side projects vs coursework)
        5. credit and graduation planning

        # CORE PRINCIPLES
        1. **No Generic Advice**: Reject "study hard". Give specific strategy.
        2. **Evidence-Based**: All claims must be backed by data (RMP, Reddit).
        3. **Contradiction Audit**: Surface contradictions (e.g. Rating < 3.0 but "Easy A").
        4. **Opportunity Cost**: Explicitly model trade-offs (Job Search vs Coursework).
        5. **Transparency**: Reveal sources.
        6. **No Hallucination**: If data is sparse, say "Data Sparse".

        # DECISION STYLE
        Do NOT output "good course" / "bad course".
        Output must reflect: "good for whom + under what conditions + why".
        """

        # Configure model with System Instruction
        model = genai.GenerativeModel(
            'gemini-2.0-flash-lite', 
            generation_config={"response_mime_type": "application/json"},
            system_instruction=system_instruction
        )
        
        # --- Goal-Driven Logic ---
        user_goal = user_profile.get('goal', 'General')
        
        summary_prompt = f"""
        # User Context
        - Mission Goal: {user_goal}
        - Course: {course_info['code']} - {prof_name}
        - RMP Data: Rating {verified_data['rmp_rating']}, Difficulty {verified_data['difficulty']}
        - Reviews: {context}
        - Requirements: {req_context}

        # Task
        Perform a strategic analysis based on the user's goal.
        
        1. **Classify Persona**: Based on Mission Goal ({user_goal}), classify user as:
           - "Job Seeking" (prioritize interview prep, resume)
           - "Research Oriented" (prioritize theory, lab)
           - "GPA Farming" (minimize workload)
           - "Undecided" (exploratory)
        
        2. **Deep Dive**: Extract specific details (Workload hours, Exam type, Languages).
        
        3. **Contradiction Audit**: Check if Rating matches Reviews.
        
        4. **Opportunity Cost**: Analyze trade-offs. Does this course kill interview prep time?
        
        5. **Strategic Planning**: Where does this fit in a 4-semester plan?
        
        Output JSON Schema:
        {{
            "data_source": "RMP Verified" | "Reddit Consensus" | "AI Estimate",
            "persona_classification": "Job Seeking" | "Research Oriented" | "GPA Farming" | "Undecided",
            "deep_dive": {{
                "workload": "string (Hours/week, intensity)",
                "grading": "string (Curve, strictness, distribution)",
                "teaching": "string (Style, clarity, engagement)",
                "exams": "string (Format, difficulty, open/closed book)",
                "projects": "string (Individual/Group, Languages, Resume value)",
                "industry_relevance": "string (Skills, Real-world alignment)"
            }},
            "contradiction_audit": {{
                "flag": boolean,
                "details": "string (Explain any mismatch found)"
            }},
            "suitability": {{
                "best_for": ["string", "string"],
                "not_for": ["string", "string"],
                "risk_factors": ["string", "string"]
            }},
            "strategic_planning": {{
                "roadmap_context": "string (e.g. 'Take in Sem 2 after Python')",
                "credit_advice": "string (e.g. 'Pair with a light elective')",
                "alternatives": ["string (Similar courses)"]
            }},
            "opportunity_cost": {{
                "trade_offs": "string (e.g. 'High workload reduces LeetCode time')",
                "warning": "string (Critical warning if applicable)"
            }}
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
                
                # --- Web-Augmented Parsing (Self-Correction) ---
                if parsed and tavily_api_key:
                    try:
                        tavily = TavilyClient(api_key=tavily_api_key)
                        for course in parsed:
                            # If info is missing, search the web
                            if course['professor'] == "TBD" or course['professor'] == "Staff" or len(course['name']) < 5:
                                st.toast(f"🌍 Searching web for {course['code']}...", icon="🔍")
                                q = f"NYU Tandon {course['code']} official course catalog syllabus instructor"
                                res = tavily.search(q, max_results=2)
                                context = "\n".join([r['content'] for r in res['results']])
                                
                                # Quick Re-Parse using Gemini
                                fix_model = get_generative_model(google_api_key)
                                fix_prompt = f"""
                                Based on this search result, find the Professor and Course Name for {course['code']}.
                                If multiple professors, pick the most recent one.
                                Output JSON: {{ "name": "...", "professor": "..." }}
                                Context: {context}
                                """
                                fix_resp = fix_model.generate_content(fix_prompt)
                                fixed_data = extract_json_from_text(fix_resp.text)
                                
                                if fixed_data:
                                    if isinstance(fixed_data, list) and len(fixed_data) > 0: fixed_data = fixed_data[0]
                                    if isinstance(fixed_data, dict):
                                        course['name'] = fixed_data.get('name', course['name'])
                                        prof = fixed_data.get('professor', 'TBD')
                                        if prof and prof != "TBD":
                                            course['professor'] = prof
                                            st.toast(f"✅ Fixed: {prof}", icon="✨")
                    except Exception as e:
                        print(f"Web Augmentation Failed: {e}")

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
        st.dataframe(
            df[['code', 'name', 'professor']].rename(columns={"code": "Course", "name": "Name", "professor": "Professor"}), 
            use_container_width=True, 
            hide_index=True
        )
        
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
                            result_json = analyze_course_with_tavily(course_obj, user_req, st.session_state['user_profile'], st.session_state['req_context'], tavily_api_key, google_api_key, status_container=status)
                            status.update(label=f"✅ {course_obj['code']} Ready", state="complete", expanded=False)
                        
                        try:
                            data = json.loads(result_json)
                            if "error" in data:
                                st.error(f"Analysis Error: {data['error']}")
                            else:
                                # --- Render Structured UI ---
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
                                
                                # 1. Suitability & Risks
                                suit = data.get("suitability", {})
                                if suit:
                                    c1, c2, c3 = st.columns(3)
                                    with c1:
                                        st.markdown("**✅ Best For**")
                                        for i in suit.get('best_for', []): st.markdown(f"- {i}")
                                    with c2:
                                        st.markdown("**❌ Not For**")
                                        for i in suit.get('not_for', []): st.markdown(f"- {i}")
                                    with c3:
                                        st.markdown("**⚠️ Risks**")
                                        for i in suit.get('risk_factors', []): st.markdown(f"- {i}")
                                    st.divider()

                                # 2. Strategic Context & Opportunity Cost
                                strat = data.get("strategic_planning", {})
                                opp = data.get("opportunity_cost", {})
                                
                                if strat or opp:
                                    st.markdown("#### 🧭 Strategic Context")
                                    sc1, sc2 = st.columns(2)
                                    with sc1:
                                        st.info(f"**Roadmap**: {strat.get('roadmap_context', 'N/A')}")
                                        st.caption(f"💡 {strat.get('credit_advice', '')}")
                                    with sc2:
                                        st.warning(f"**📉 Opportunity Cost**: {opp.get('trade_offs', 'N/A')}")
                                        if opp.get('warning'):
                                            st.error(f"🚨 {opp.get('warning')}")

                                # 3. Deep Dive
                                with st.expander("🧐 Deep Dive (深度测评)", expanded=True):
                                    dd = data.get("deep_dive", {})
                                    
                                    # Details Grid
                                    c1, c2 = st.columns(2)
                                    with c1:
                                        st.markdown(f"**📚 Workload**: {dd.get('workload', 'N/A')}")
                                        st.markdown(f"**⚖️ Grading**: {dd.get('grading', 'N/A')}")
                                        st.markdown(f"**🎓 Teaching**: {dd.get('teaching', 'N/A')}")
                                    with c2:
                                        st.markdown(f"**📝 Exams**: {dd.get('exams', 'N/A')}")
                                        st.markdown(f"**💻 Projects**: {dd.get('projects', 'N/A')}")
                                        st.markdown(f"**💼 Industry**: {dd.get('industry_relevance', 'N/A')}")

                                # 4. Contradiction Audit
                                audit = data.get("contradiction_audit", {})
                                if audit.get("flag"):
                                    st.error(f"🕵️ **Logic Audit**: {audit.get('details')}")
                                
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
