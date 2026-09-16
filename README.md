[English](#english) | [简体中文](#简体中文)

<a id="english"></a>

# English

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

---

<a id="简体中文"></a>

# 简体中文

# ✈️ Course Pilot (v3.2)

**面向 NYU Tandon 的智能选课助手**

Course Pilot 是 AI 驱动的课程规划助手，不局限于课程目录搜索。它汇总 **Rate My Professors**、**Reddit** 和**官方教学大纲**的数据，根据求职、科研或提高 GPA 等目标提供个性化建议。

![Course Pilot UI](https://img.shields.io/badge/Status-Active-success) ![Python](https://img.shields.io/badge/Python-3.9+-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B) ![Gemini](https://img.shields.io/badge/AI-Gemini%202.0-8E75B2)

## ✨ 核心功能

- **🧠 智能解析**：粘贴课程目录中的杂乱文本，由 AI 提取结构化数据。
- **🎯 目标导向分析**：求职侧重面试技能、简历项目和行业相关性；博士申请侧重理论深度、实验室机会和教授声誉；提高 GPA 侧重工作量、成绩分布和获得高分的可能性。
- **🛡️ 分级数据验证**：第一级为已核实的 RMP 评分（难度、是否愿意再次选课）；第二级为 Reddit 共识（学生讨论的情感分析）；第三级为 AI 估算，用于新课程或未知课程。
- **💎 界面设计**：使用 Streamlit 构建现代玻璃拟态界面。
- **🔧 容错能力**：自动纠正拼写错误（例如 `Linda Selie` → `Linda Sellie`），并处理缺失数据。

## 🛠️ 技术栈

- **核心**：Python 3.9+
- **前端**：Streamlit
- **AI 引擎**：Google Gemini 2.0 Flash Lite（通过 `google-generativeai`）
- **搜索**：Tavily API，用于实时获取 RMP/Reddit 数据
- **数据处理**：Pandas、TheFuzz（可选）

## 🚀 快速开始

### 前置条件

- Python 3.9 或更高版本
- Google Cloud API Key（Gemini）
- Tavily API Key

### 安装

1. **克隆仓库**

    ```bash
    git clone https://github.com/GU2THOUSAND/course-pilot.git
    cd course-pilot
    ```

2. **安装依赖**

    ```bash
    pip install -r requirements.txt
    ```

3. **配置环境变量**：在根目录创建 `.env` 文件：

    ```env
    GOOGLE_API_KEY=your_google_api_key
    TAVILY_API_KEY=your_tavily_api_key
    ```

4. **启动应用**

    ```bash
    streamlit run src/ui/app.py
    ```

## 📖 工作流程

1. **粘贴**：从 NYU Albert 或课程目录复制课程文本。
2. **解析**：**Universal Parser** 提取课程代码、名称和教授。
3. **配置**：设置 **Mission Goal**（例如求职）和 **No-Fly Zone**（例如不选早上 8 点的课）。
4. **分析**：**Judge Agent** 核验数据，**Advisor Engine** 生成包含 `Quick Stats`、`Verdict` 和 `Deep Dive` 的完整报告。

## 🤝 参与贡献

欢迎贡献！开发规范见 `WORKFLOW.md`。

## 📄 许可证

MIT License。
