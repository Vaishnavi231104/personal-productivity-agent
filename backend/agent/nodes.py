import os
import json
import datetime
from groq import Groq
from sqlalchemy.orm import Session

from agent.state import AgentState
from database import SessionLocal
import models

# Initialize Groq Client
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
groq_client = Groq(api_key=GROQ_API_KEY)

def classifier_node(state: AgentState) -> dict:
    """Uses LLM to take raw task strings and format them into structured JSON objects."""
    print("--- RUNNING CLASSIFIER NODE ---")
    tasks_raw = state.get("tasks_raw", [])
    
    if not tasks_raw:
        return {"classified_tasks": []}

    prompt = f"""
    You are an expert personal productivity assistant. Take the following list of raw tasks and categorize them.
    For each task, determine:
    1. Category (e.g., Work, Personal, Study, Health, Urgent)
    2. Priority (High, Medium, Low)
    
    Tasks to process: {tasks_raw}
    
    You MUST respond with a valid JSON array of objects, and NOTHING ELSE. Do not include markdown code block formatting (like ```json).
    Format example:
    [
        {{"title": "task description", "category": "Work", "priority": "High"}}
    ]
    """

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        
        content = response.choices[0].message.content.strip()
        # Clean up accidental markdown formatting if the model still outputs it
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("\n", 1)[0].strip()
            if content.startswith("json"):
                content = content.split("\n", 1)[1].strip()

        classified = json.loads(content)
        return {"classified_tasks": classified}
    except Exception as e:
        print(f"Error in classifier_node parsing: {e}")
        # Fallback if parsing fails completely
        fallback = [{"title": t, "category": "General", "priority": "Medium"} for t in tasks_raw]
        return {"classified_tasks": fallback}


def overdue_surfacer_node(state: AgentState) -> dict:
    """Queries the SQLite database to see if this user has any uncompleted, overdue tasks."""
    print("--- RUNNING OVERDUE SURFACER NODE ---")
    user_id = state.get("user_id")
    now = datetime.datetime.utcnow()
    
    db: Session = SessionLocal()
    try:
        overdue_db_tasks = db.query(models.Task).filter(
            models.Task.user_id == user_id,
            models.Task.is_completed == False,
            models.Task.due_date < now
        ).all()
        
        overdue_list = [
            {"id": t.id, "title": t.title, "category": t.category, "priority": t.priority} 
            for t in overdue_db_tasks
        ]
        return {"overdue_tasks": overdue_list}
    finally:
        db.close()


def eod_summarizer_node(state: AgentState) -> dict:
    """Generates a motivating 2-sentence feedback wrap-up of the day's achievements."""
    print("--- RUNNING EOD SUMMARIZER NODE ---")
    user_id = state.get("user_id")
    
    db: Session = SessionLocal()
    try:
        # Pull today's tasks for context
        today_start = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        tasks = db.query(models.Task).filter(
            models.Task.user_id == user_id,
            models.Task.created_at >= today_start
        ).all()
        
        completed = [t.title for t in tasks if t.is_completed]
        pending = [t.title for t in tasks if not t.is_completed]
        
        prompt = f"""
        Review this user's completion record for today:
        Completed Tasks: {completed}
        Remaining Tasks: {pending}
        
        Write a concise, high-impact, encouraging 2-sentence performance summary review. Direct it directly to them.
        """
        
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        
        summary = response.choices[0].message.content.strip()
        return {"eod_summary": summary}
    finally:
        db.close()


def next_day_planner_node(state: AgentState) -> dict:
    """Generates an optimized JSON suggestion roadmap for tomorrow's checklist."""
    print("--- RUNNING NEXT DAY PLANNER NODE ---")
    user_id = state.get("user_id")
    
    db: Session = SessionLocal()
    try:
        # Pull pending tasks to carry over
        pending_tasks = db.query(models.Task).filter(
            models.Task.user_id == user_id,
            models.Task.is_completed == False
        ).all()
        pending_titles = [t.title for t in pending_tasks]
        
        prompt = f"""
        Based on these carried-over pending tasks: {pending_titles}, propose an actionable plan for tomorrow.
        Suggest 2-3 specific, broken-down next actionable items.
        
        Return ONLY a raw JSON list of strings representing the task titles. Do not include markdown blocks.
        Example: ["Finish project documentation draft", "Review feedback on PR"]
        """
        
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("\n", 1)[0].strip()
            if content.startswith("json"):
                content = content.split("\n", 1)[1].strip()
                
        plan = json.loads(content)
        return {"tomorrow_plan": plan}
    except Exception as e:
        print(f"Error in next_day_planner parsing: {e}")
        return {"tomorrow_plan": ["Review incomplete tasks from yesterday"]}
    finally:
        db.close()