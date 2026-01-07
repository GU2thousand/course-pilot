# Changelog & Decision Records

## 2026.1.7
### 💡 Product Logic Update
- **Goal-Driven Prompting**: Refactored the 'Judge Agent' to weigh analysis based on the `Mission Goal` (Job/Research/GPA).
- **Session Persistence**: Implemented `st.session_state` to clear specific questions only when the course target changes.

### 🔧 Technical Improvements
- **Fuzzy Matching**: Integrated `thefuzz` library to handle user typos in professor names.
- **Structured JSON Output**: Forced Gemini to output JSON to eliminate "Extract [N/A]" hallucinations in the UI.

### 🛡️ Decision Log: Why TheFuzz?
- **Problem**: Many RMP searches failed due to Albert's "Lastname, Firstname" format or user typos.
- **Alternative**: Manual mapping (too high maintenance).
- **Decision**: Use Levenshtein distance (Fuzzy matching) with a 85% similarity threshold.
- **Result**: Reduced 404 Professor errors by ~35%.

---

## 
- **Initial Migration**: Moved from local scripts to Streamlit Cloud.
- **Logging**: Added `FileHandler` to capture production errors for remote debugging.
