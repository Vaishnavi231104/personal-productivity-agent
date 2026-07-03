# ⚡ AuraFlow AI — Intelligent Personal Productivity Framework

AuraFlow AI is a stateful, full-stack multi-agent orchestration ecosystem designed to handle personal goal mapping and task classification. Driven by a **FastAPI** backend and an intelligent **LangGraph state machine**, the application splits chaotic morning raw text streams into highly structured, prioritized database entries while generating side-by-side behavioral timelines and scheduled automated habit reflection logs.

---

## 👥 Contributor Details
* **Developer Name:** Vaishnavi Dwivedi   
* **Capstone Submission Module:** Module 6 (IITR-SE-2509-Cohort-B)  

---

## 🗂️ Project Deliverables & Media Links
* **🎬 Project Walkthrough Video Demo:** [[Google Drive Link for Project Walkthrough Video Here](https://drive.google.com/file/d/16WqF74UBBVtV87r4Q3x5OXfMxRlQV4HV/view?usp=drive_link)]  
* **📊 Architectural Strategy Slide Deck (PPT):** [[Google Drive Link for PPT Here](https://docs.google.com/presentation/d/1EM6PUzk704w8jHmql2hgORZD8adXkZ7dvYCxNLB6Jp8/edit?usp=drive_link)]  
* **💻 GitHub Repository:** [[GitHub Repo URL Here](https://github.com/Vaishnavi231104/personal-productivity-agent)]
  
--- 

## 🚀 Live Deployments
* **Live Frontend Dashboard (Streamlit):** [[AuraFlow AI app URL](https://personal-appuctivity-agent-rphjvq47lh8ld6ghkqmowx.streamlit.app/)]
* **Live Production API (FastAPI/Render):** [https://personal-productivity-agent.onrender.com/docs](https://personal-productivity-agent-0qvn.onrender.com/docs)
---

## 🤖 Core Agentic System Workflow

The architecture utilizes an intelligent, asynchronous pipeline that monitors, manages, and structures goals over a rolling 7-day operational window:

1. **Morning AI Pipeline Sync:** Captures unstructured focus text strings via a Streamlit interface and passes them securely through a FastAPI layer to a **LangGraph stateful classifier agent** (powered by `llama-3.1-8b`).
2. **Overdue Surfacing Engine:** Automatically triggers localized database queries to identify incomplete actions from previous cycles, pulling them into active viewport states.
3. **State Management:** Preserves user history and active node flows continuously using transactional thread parameters (`thread_id = {user_id}`) managed via an integrated state-saver layer.
4. **Automated Pattern Surfacer:** A background worker scheduled via **APScheduler** that evaluates historical data streams on a rolling 7-day matrix to isolate repeating behavioral trend dynamics (e.g., category dominance or repeating item drops).

---

## 🗄️ Database Architecture & ORM Schema Mappings

The database layer handles Object Relational Mapping (ORM) natively through definitions configured inside [`backend/models.py`](./backend/models.py). 

### 📋 Schema Configuration Summary
* **User Entity (`users` table):** Tracks unique authenticated user profiles, credential security strings, and handles an explicit one-to-many cascading model relationship pointing directly down to individual tasks.
* **Task Entity (`tasks` table):** Records explicit item parameters including unique task identifiers, foreign keys, strings for `title`, `category`, and `priority`, completion state booleans, and datetime properties for creation and completion tracking. 
* **Overdue State Tracking:** Utilizes a dedicated `due_date` column property within the table rows, enabling the LangGraph overdue query node to surface uncompleted items dynamically across sessions.

---

## ⚙️ Local Installation & Launch Setup Playbook

Ensure you have Python 3.10+ installed locally before executing the initialization routines.

### 🔧 1. Backend API Execution (FastAPI & LangGraph)
Open your terminal window, navigate into your backend subdirectory, spin up your python virtual environment, and initialize dependencies:
```bash
# Move into the backend layer
cd backend

# Initialize and launch the local environment
source venv/Scripts/activate   # On Windows Git Bash
# venv\Scripts\activate        # On Windows Command Prompt
# source venv/bin/activate     # On macOS/Linux

# Install the structural dependencies
pip install -r requirements.txt

# Run the database migration column creation statement
python -c "import database, models; models.Base.metadata.create_all(bind=database.engine)"

# Start the local development server
python -m uvicorn main:app --reload


### 🎨 2. Frontend User Interface Execution (Streamlit Workspace)
To run the client workspace dashboard locally, open a separate terminal window or vertical terminal split in VS Code and execute the following steps:
```bash
# 1. Navigate into the frontend layout directory from the root folder
cd frontend

# 2. Verify dependencies are configured (Streamlit, Requests)
pip install streamlit requests

# 3. Launch the local Streamlit application server node
streamlit run app.py


