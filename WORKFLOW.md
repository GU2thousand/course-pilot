# ✈️ Course Pilot Project Workflow

这份文档旨在帮助你快速上手、开发和维护 Course Pilot 项目。

## 1. 🚀 Quick Start (快速启动)

### 环境准备
确保你已经安装了 Python 3.10+ 和 Git。

```bash
# 1. 克隆项目 (如果你还没克隆)
git clone https://github.com/GU2THOUSAND/course-pilot.git
cd course-pilot

# 2. 创建并激活虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Mac/Linux
# .venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install -r requirements.txt
```

### 配置密钥
在项目根目录创建一个 `.env` 文件 (不要上传到 GitHub!)：

```ini
GOOGLE_API_KEY=your_gemini_key_here
TAVILY_API_KEY=your_tavily_key_here
```

### 启动应用
```bash
streamlit run src/ui/app.py
```
访问: http://localhost:8501

---

## 2. 📂 Project Structure (项目结构)

*   **`src/ui/app.py`**: 主程序入口。包含 Streamlit 界面逻辑、Prompt 定义和核心流程控制。
*   **`src/data/`**: 数据处理模块。
    *   `rmp.py`: 处理 Rate My Professors 搜索和数据提取。
    *   `processor.py`: 数据清洗和格式化。
    *   `fetcher.py`: (旧) 数据获取逻辑。
*   **`src/vector_store/`**: 向量数据库逻辑 (ChromaDB)。
*   **`requirements.txt`**: 项目依赖列表。
*   **`.gitignore`**: 指定不上传到 Git 的文件 (如 .env, .venv)。

---

## 3. 🧠 How it Works (核心原理)

Course Pilot 的工作流程分为四个主要阶段：

### 1. 智能解析 (Intelligent Parsing)
*   **输入**: 用户将教务系统 (如 Albert) 的杂乱文本粘贴到输入框。
*   **处理**: `parse_raw_text_with_gemini` 函数调用 Gemini API。
*   **输出**: AI 自动识别并提取 Course Code, Name, Professor, Time 等关键信息，转换为标准的 JSON 格式。

### 2. 数据增强 (Data Enrichment)
*   **RMP 搜索**: 系统自动调用 Tavily API 搜索 `Professor Name + School + Rate My Professors`。
*   **数据提取**: 使用正则表达式和 AI 从搜索结果中精准提取 **Rating (评分)** 和 **Summary (评价摘要)**。
*   **论坛侦察**: 同时搜索 Reddit 和 1point3acres，获取关于 Workload (工作量) 和 Difficulty (难度) 的真实讨论。

### 3. 深度分析 (Deep Analysis)
*   **Prompt 构建**: 系统将以下信息打包成一个超级 Prompt：
    *   用户画像 (Profile): 专业、年级、目标 (找工/读博)。
    *   毕业要求 (Requirements): 自动抓取的学位要求。
    *   真实数据 (Real Data): 上一步获取的 RMP 评分和论坛评价。
*   **AI 生成**: Gemini 扮演 "CourseMate" 角色，生成一份包含 "Quick Stats", "Verdict" (建议), "Deep Dive" (深度挖掘) 的 Markdown 报告。

### 4. 智能排课 (Strategic Recommendation)
*   **逻辑**: 根据用户的 Goal (如 "Job Seeking" 偏向实用课) 和 Anti-Preferences (如 "No 8am")。
*   **输出**: AI 从可选课程中计算出最佳的 3-4 门课组合，并给出具体的选课策略理由。

---

## 4. 🛠 Development Workflow (开发流程)

### 修改代码
1.  **修改 UI**: 编辑 `src/ui/app.py`。Streamlit 通常会自动检测更改，点击浏览器右上角的 "Rerun" 即可看到效果。
2.  **修改逻辑**: 如果修改了 `rmp.py` 等后端逻辑，建议重启 Streamlit 服务以确保生效。

### 调试 (Debugging)
*   **查看日志**: Streamlit 的报错信息会直接显示在网页上，或者终端控制台中。
*   **API 问题**: 如果遇到 API 报错 (404, 429)，请检查 `.env` 中的 Key 是否有效，或尝试切换模型 (如 `gemini-1.5-flash` -> `gemini-2.0-flash-lite`)。

---

## 5. 🐙 Git Workflow (Git 工作流)

你之前遇到了推送冲突，这是因为远程仓库 (GitHub) 有你本地没有的更新。请遵循以下标准流程：

### 提交代码 (Standard Push)
```bash
# 1. 查看修改状态
git status

# 2. 添加修改
git add .

# 3. 提交 (写清楚你做了什么)
git commit -m "描述你的修改，例如: 修复 RMP 数据提取 bug"

# 4. 拉取远程更新 (关键步骤! 防止冲突)
git pull origin main

# 5. 推送
git push origin main
```

### 解决冲突 (Fixing Conflicts)
如果在 `git pull` 时提示冲突 (Conflict)：
1.  打开冲突的文件，你会看到 `<<<<<<< HEAD` 和 `>>>>>>>` 标记。
2.  手动修改文件，保留你想要的代码，删除标记。
3.  保存文件。
4.  重新执行：
    ```bash
    git add .
    git commit -m "解决合并冲突"
    git push origin main
    ```

---

## 6. ⚠️ Common Issues (常见问题)

**Q: 报错 `404 models/gemini-1.5-flash not found`?**
A: 你的 Google 账号可能不支持该模型。请在 `src/ui/app.py` 中搜索 `get_generative_model` 函数，将模型名称改为 `gemini-2.0-flash-lite` 或 `gemini-flash-latest`。

**Q: 报错 `429 Resource Exhausted`?**
A: API 配额用完了。
1. 等待几分钟。
2. 切换到更便宜/免费配额更多的模型 (Flash 系列)。
3. 检查代码中是否有死循环调用 API。

**Q: Git 提示 `refusing to merge unrelated histories`?**
A: 首次拉取时可能发生。使用: `git pull origin main --allow-unrelated-histories`
