# ✈️ Course Pilot (v3.2)
**Your Intelligent Academic Copilot for NYU Tandon**

Course Pilot is an AI-powered course planning assistant that goes beyond simple catalog searches. It aggregates data from **Rate My Professors**, **Reddit**, and **Official Syllabi** to provide personalized, goal-driven advice (Job Seeking, Research, or GPA Booster).

![Course Pilot UI](https://img.shields.io/badge/Status-Active-success) ![Python](https://img.shields.io/badge/Python-3.9+-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B) ![Gemini](https://img.shields.io/badge/AI-Gemini%202.0-8E75B2)

## ✨ Key Features

*   **🧠 Intelligent Parsing**: Paste messy text from any course catalog, and our AI extracts structured data instantly.
*   **🎯 Goal-Driven Analysis**:
    *   **Job Seekers**: Focuses on interview skills, resume projects, and industry relevance.
    *   **PhD Hopefuls**: Highlights theoretical depth, lab opportunities, and professor reputation.
    *   **GPA Boosters**: Scrutinizes workload, grading distributions, and "easy A" potential.
*   **🛡️ Tiered Data Verification**:
    *   **Level 1**: Verified RMP Ratings (Difficulty, Would Take Again).
    *   **Level 2**: Reddit Consensus (Sentiment analysis from student discussions).
    *   **Level 3**: AI Estimation (Fallback for new/unknown courses).
*   **💎 Premium UI**: A modern, glassmorphism-inspired interface built with Streamlit.
*   **🔧 Robust & Resilient**: Auto-corrects typos (e.g., "Linda Selie" -> "Linda Sellie") and handles missing data gracefully.

## 🛠️ Tech Stack

*   **Core**: Python 3.9+
*   **Frontend**: Streamlit
*   **AI Engine**: Google Gemini 2.0 Flash Lite (via `google-generativeai`)
*   **Search**: Tavily API (for real-time RMP/Reddit data)
*   **Data Processing**: Pandas, TheFuzz (optional)

## 🚀 Quick Start

### Prerequisites
*   Python 3.9 or higher
*   A Google Cloud API Key (Gemini)
*   A Tavily API Key

### Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/GU2THOUSAND/course-pilot.git
    cd course-pilot
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up environment variables**
    Create a `.env` file in the root directory:
    ```env
    GOOGLE_API_KEY=your_google_api_key
    TAVILY_API_KEY=your_tavily_api_key
    ```

4.  **Run the application**
    ```bash
    streamlit run src/ui/app.py
    ```

## 📖 How It Works

1.  **Paste**: Copy course text from the NYU Albert/Catalog.
2.  **Parse**: The **Universal Parser** extracts course codes, names, and professors.
3.  **Configure**: Set your **Mission Goal** (e.g., Job Seeking) and **No-Fly Zone** (e.g., No 8am classes).
4.  **Analyze**: The **Judge Agent** verifies data, and the **Advisor Engine** generates a comprehensive report with "Quick Stats", "Verdict", and "Deep Dive".

## 🤝 Contributing

Contributions are welcome! Please check `WORKFLOW.md` for development guidelines.

## 📄 License

MIT License.
