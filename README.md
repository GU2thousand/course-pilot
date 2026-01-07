# ✈️ Course Pilot (v3.2)
**Your Intelligent Academic Copilot for NYU Tandon**

Course Pilot is an AI-powered course planning assistant that goes beyond simple catalog searches. It aggregates data from **Rate My Professors**, **Reddit**, and **Official Syllabi** to provide personalized, goal-driven advice.

![Status-Active](https://img.shields.io/badge/Status-Active-success) ![Python](https://img.shields.io/badge/Python-3.9+-blue) ![Gemini](https://img.shields.io/badge/AI-Gemini%202.0-8E75B2)

## ✨ Key Features

* **🧠 Intelligent Parsing**: AI-driven extraction of Course IDs and Professor names from messy Albert/Catalog text.
* **🎯 Mission-Goal Alignment**: 
    * **Job Seekers**: Prioritizes interview-relevant skills and resume-worthy projects.
    * **PhD Hopefuls**: Highlights theoretical depth and lab opportunities.
    * **GPA Boosters**: Scrutinizes workload and "Easy A" potential.
* **🛡️ Tiered Data Verification**: 
    * **Level 1**: Real-time RMP scraping & sentiment extraction.
    * **Level 2**: Reddit consensus analysis via Tavily Search.
    * **Level 3**: AI Fallback reasoning for new/unknown courses.
* **🔧 Fault-Tolerant Engine**: Integrated `thefuzz` for professor name auto-correction (e.g., "Linda Selie" -> "Linda Sellie").

## 📂 Project Structure
```text
├── src/
│   ├── ui/app.py          # Streamlit Interface
│   ├── logic/             # Core AI & Search logic
│   ├── data/              # Database & Ingestion scripts
│   └── utils/logger.py    # Standardized logging utility
├── docs/                  # Design documents & ADRs
├── .env.example           # Environment template
└── requirements.txt       # Dependencies
