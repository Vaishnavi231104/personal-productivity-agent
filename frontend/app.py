import streamlit as st
import datetime
import requests
import json

# Backend API Configuration URL
BASE_URL = "https://personal-productivity-agent-0qvn.onrender.com"

# Set global page configurations
st.set_page_config(
    page_title="AuraFlow AI Workspace",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 🔒 PART 1: PERSISTENT STATE TRACKING ---
# Keeping these declared globally stops the page from kicking you back to login on state change
if "token" not in st.session_state:
    st.session_state.token = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "last_eod_summary" not in st.session_state:
    st.session_state.last_eod_summary = None
if "last_tomorrow_plan" not in st.session_state:
    st.session_state.last_tomorrow_plan = None


if st.session_state.token is None:
    st.title("⚡ Welcome to AuraFlow AI")
    st.markdown("*Your Intelligent Personal Productivity Core Agent Framework*")
    st.divider()

    # 👇 Clean, native HTML/CSS injection with no extra parameters to break Python 3.14 👇
    st.html('<style>.stApp { background-color: #FFF0F2 !important; }</style>')

    # 🔑 The standard gateway elements continue right below:
    auth_mode = st.radio("Choose Access Route", ["Log In", "Sign Up"], horizontal=True)
    email = st.text_input("Email Address")
    password = st.text_input("Password", type="password")
    if auth_mode == "Log In":
        if st.button("Log In", use_container_width=True):
            if email and password:
                with st.spinner("Validating JWT credentials tokens..."):
                    # 💡 FIX: Explicitly send credentials as a form dictionary using data=
                    login_payload = {
                        "username": email, 
                        "password": password
                    }
                    res = requests.post(f"{BASE_URL}/auth/login", data=login_payload)
                    
                    if res.status_code == 200:
                        st.session_state.token = res.json()["access_token"]
                        st.session_state.user_email = email
                        st.success("Session verified successfully!")
                        st.rerun()
                    else:
                        st.error("Access denied. Invalid credentials mapped.")
            else:
                st.warning("Please input complete login details.")
                
    else: # Sign Up Pipeline
        if st.button("Provision New Account Profile", use_container_width=True):
            if email and password:
                with st.spinner("Registering database account profile records..."):
                    res = requests.post(f"{BASE_URL}/auth/signup", json={"email": email, "password": password})
                    if res.status_code == 200:
                        st.success("Profile generated! Switch to Log In mode to authorize.")
                    else:
                        st.error("Registration rejected. User profile might already exist.")
            else:
                st.warning("Please fill out registration text parameters.")


# --- 🎨 PART 3: DYNAMIC WORKSPACE INTERFACE ---
else:
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    
    # 🕒 Dynamic Time-Aware Background Themes
    current_hour = datetime.datetime.now().hour
    
    # Check if morning vs evening to change backdrop aesthetics
    if 5 <= current_hour < 16:
        # Morning Mood: Fresh sunrise colors, dark readable text
        bg_gradient = "linear-gradient(135deg, #FFDEE9 0%, #B5FFFC 100%)"
        text_color = "#2C3E50"
        card_bg = "rgba(255, 255, 255, 0.85)"
        mood_banner = "🌅 Good Morning! Flowers blooming, focus pulsing. Time to chase down today's milestones."
    else:
        # Evening Cozy Mood: Warm dark ambient workspace, soft text
        bg_gradient = "linear-gradient(135deg, #1A1C29 0%, #322543 100%)"
        text_color = "#F5F6FA"
        card_bg = "rgba(255, 255, 255, 0.08)"
        mood_banner = "🌌 Evening Reflection. Warm ambient lights, clear mind. Time to evaluate and wind down peacefully."

    # Injecting Custom Dynamic CSS Layers
    st.markdown(f"""
        <style>
            [data-testid="stAppViewContainer"] {{
                background: {bg_gradient} !important;
                transition: background 1s ease-in-out;
            }}
            .stMarkdown, p, h1, h2, h3, label, div[data-testid="stMetricValue"] {{
                color: {text_color} !important;
            }}
            .metric-box {{
                background: {card_bg};
                border-radius: 12px;
                padding: 20px;
                border: 1px solid rgba(255, 255, 255, 0.15);
                text-align: center;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
            }}
            .stButton>button {{
                background: linear-gradient(135deg, #36d1dc 0%, #5b86e5 100%);
                color: white !important;
                border: none !important;
                border-radius: 8px;
                font-weight: 600;
                transition: all 0.2s ease;
            }}
            .stButton>button:hover {{
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(91, 134, 229, 0.3);
            }}
        </style>
    """, unsafe_allow_html=True)

    # Sidebar Structural Layout Component Panel
    st.sidebar.markdown("## 👤 AuraFlow Profile")
    st.sidebar.markdown(f"User Active:<br>**{st.session_state.user_email}**", unsafe_allow_html=True)
    st.sidebar.divider()
    if st.sidebar.button("To Log Out / Terminate", use_container_width=True):
        st.session_state.token = None
        st.session_state.user_email = None
        st.session_state.last_eod_summary = None
        st.session_state.last_tomorrow_plan = None
        st.rerun()

    # App Branding Main Layout Header
    st.title("⚡ AuraFlow AI Workspace")
    st.markdown(f"*{mood_banner}*")
    st.divider()

    # Fetch active tasks early to generate real-time metrics trackers
    response = requests.get(f"{BASE_URL}/tasks", headers=headers)
    active_tasks = []
    completed_count = 0
    
    if response.status_code == 200:
        all_tasks = response.json()
        active_tasks = [t for t in all_tasks if not t.get("is_completed", False)]
        completed_count = len(all_tasks) - len(active_tasks)

    # --- MAIN STRUCTURAL VIEW SPLIT TABS ---
    main_tab, weekly_tab = st.tabs(["🎯 Daily Core Sync", "📊 Sunday Pattern Surf"])

    with main_tab:
        # 📊 PROGRESS LOADERS & THRESHOLD METRICS ENGINE
        total_tasks = len(active_tasks) + completed_count
        velocity_ratio = (completed_count / total_tasks) if total_tasks > 0 else 0.0

        # Determine structural rating context classes (Red -> Yellow -> Green)
        if velocity_ratio < 0.4:
            status_label = "🔴 Hustle Mode Required (Focus Velocity Poor)"
        elif velocity_ratio < 0.8:
            status_label = "🟡 Steady Progress (Focus Velocity Mid)"
        else:
            status_label = "🟢 Crushing Objectives! (Focus Velocity Awesome)"

        st.markdown(f"**Current Status Matrix:** {status_label}")
        st.progress(velocity_ratio, text=f"Daily Completion Performance: {int(velocity_ratio * 100)}%")
        st.markdown("<br>", unsafe_allow_html=True)

        # High level numeric summary metrics grid
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.markdown('<div class="metric-box">', unsafe_allow_html=True)
            st.metric(label="⏳ Remaining Backlog Objectives", value=len(active_tasks))
            st.markdown('</div>', unsafe_allow_html=True)
        with m_col2:
            st.markdown('<div class="metric-box">', unsafe_allow_html=True)
            st.metric(label="✅ Finalized Milestones Today", value=completed_count)
            st.markdown('</div>', unsafe_allow_html=True)

        st.divider()

        # --- TWO COLUMN TASK ACTION PIPELINES ---
        col1, col2 = st.columns([1, 1], gap="large")
        
        with col1:
            st.subheader("🌅 Morning AI Pipeline Sync")
            with st.container(border=True):
                raw_input = st.text_area(
                    "What major intentions are we tracking today?", 
                    placeholder="e.g., video lectures, final report, read chapter...",
                    height=120
                )
                
                if st.button("🚀 Execute Morning Agent Scan", use_container_width=True):
                    if raw_input:
                        tasks_list = [line.strip() for line in raw_input.split(",") if line.strip()]
                        with st.spinner("LangGraph Engine mapping workflows..."):
                            res = requests.post(f"{BASE_URL}/checkin/morning", json=tasks_list, headers=headers)
                            if res.status_code == 200:
                                st.success("Checklist parsed and committed successfully!")
                                st.rerun()
                            else:
                                st.error("Could not run agent parsing node pipeline connectivity.")
                    else:
                        st.warning("Please enter at least one intention item string!")

        with col2:
            st.subheader("🌌 Evening AI Feedback Summary")
            with st.container(border=True):
                if response.status_code == 200:
                    if not active_tasks:
                        st.info("🎉 All clear! No outstanding tasks for today. Run your morning engine to add more goals.")
                    else:
                        st.markdown("### Update Daily Checklist Progress:")
                        completed_ids = []
                        
                        # Iterate active rows rendering sliding toggles
                        for task in active_tasks:
                            priority = task.get('priority', 'Normal')
                            p_badge = "🔴" if priority == "High" else "🟡" if priority == "Medium" else "🟢"
                            
                            is_checked = st.toggle(
                                label=f"{p_badge} **{task['title']}** | `{task.get('category', 'Task')}`", 
                                key=f"task_{task['id']}"
                            )
                            if is_checked:
                                completed_ids.append(task['id'])
                        
                        st.divider()
                        
                        if st.button("📊 Finalize Evening Review Sync", use_container_width=True):
                            if not completed_ids:
                                st.warning("Please select at least one completed task before checking in!")
                            else:
                                with st.spinner("Analyzing productivity layout flows with LangGraph..."):
                                    res = requests.post(f"{BASE_URL}/checkin/evening", json=completed_ids, headers=headers)
                                    if res.status_code == 200:
                                        st.success("Evening evaluation finalized cleanly!")
                                        data = res.json()
                                        
                                        # Save text results to session cache so they persist across metric reruns
                                        st.session_state.last_eod_summary = data.get("eod_summary")
                                        st.session_state.last_tomorrow_plan = data.get("tomorrow_plan")
                                        st.rerun()
                                    else:
                                        st.error("Failed to process evening feedback pipeline connection.")
                else:
                    st.error("Could not fetch active workspace tasks from database layer server.")
            
            # Print text results dynamically if they exist in state cache cache
            if st.session_state.last_eod_summary:
                st.markdown("### 📝 End of Day Reflection")
                st.info(st.session_state.last_eod_summary)
            if st.session_state.last_tomorrow_plan:
                st.markdown("### 📅 Tomorrow's Strategy Roadmap")
                st.json(st.session_state.last_tomorrow_plan)

    with weekly_tab:
        st.subheader("🗓️ This Week View & Habit Analytics")
        st.markdown("Monitor your rolling 7-day timeline logs side-by-side and extract agent insights.")
        
        # --- 📈 REQUIREMENT 1: "THIS WEEK" SIDE-BY-SIDE TIMELINE GRID ---
        st.markdown("### 📅 Weekly Archive Roadmap")
        
        # Pull your task data to display statuses across the running 7-day window
        history_response = requests.get(f"{BASE_URL}/tasks", headers=headers)
        if history_response.status_code == 200:
            all_history_tasks = history_response.json()
            
            if not all_history_tasks:
                st.info("No recorded milestones found in your profile history this week.")
            else:
                # Group tasks by their creation date dynamically (up to the last 4 unique days for clear side-by-side view)
                grouped_days = {}
                for t in all_history_tasks:
                    # Safely parse date strings
                    date_str = t.get("created_at", "Today")[:10] if t.get("created_at") else "Today"
                    if date_str not in grouped_days:
                        grouped_days[date_str] = []
                    grouped_days[date_str].append(t)
                
                sorted_days = sorted(list(grouped_days.keys()), reverse=True)[:4]
                
                if sorted_days:
                    # Initialize Streamlit side-by-side column objects dynamically!
                    cols = st.columns(len(sorted_days))
                    for idx, day_key in enumerate(sorted_days):
                        with cols[idx]:
                            st.markdown(f"#### 📅 {day_key}")
                            for task_item in grouped_days[day_key]:
                                status_icon = "✅" if task_item.get("is_completed") else "⏳"
                                st.caption(f"{status_icon} {task_item['title']} (`{task_item.get('category', 'Focus')}`)")
        else:
            st.error("Could not fetch side-by-side structural history timeline records.")
            
        st.divider()

        # --- 🤖 REQUIREMENT 2: WEEKLY REVIEW PATTERN SURFACER ---
        st.markdown("### 🧠 Pattern Surfacer Insight Engine")
        with st.container(border=True):
            if st.button("🔍 Pull Weekly Pattern Analysis", use_container_width=True):
                with st.spinner("Analyzing past historical daily reflection log strings..."):
                    res = requests.get(f"{BASE_URL}/checkin/weekly", headers=headers)
                    if res.status_code == 200:
                        review_data = res.json()
                        st.markdown("#### 📝 Surfaced Agent Behavioral Patterns")
                        st.info(review_data.get("weekly_insight", "No recurring patterns recorded this cycle."))
                    else:
                        st.error("Could not complete weekly reflection aggregation request.")