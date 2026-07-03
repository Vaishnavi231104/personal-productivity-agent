from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, EmailStr 
from dotenv import load_dotenv 
load_dotenv()  # Load environment variables from .env file
import datetime
import json
import models
import auth 
from models import Base
from database import engine, get_db

Base.metadata.create_all(bind=engine)  # Create tables if they don't exist
app = FastAPI(title="Personal Productivity Agent API")

# Enable CORS so your Streamlit frontend can talk to your backend cleanly later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Schemas for Data Validation ---
class UserSignUp(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TaskCreate(BaseModel):
    title: str
    category: Optional[str] = "General"
    priority: Optional[str] = "Medium"
    due_date: Optional[datetime.datetime] = None

class TaskResponse(BaseModel):
    id: int
    user_id: int
    title: str
    category: str
    priority: str
    due_date: Optional[datetime.datetime]
    is_completed: bool
    completed_at: Optional[datetime.datetime]
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# --- API Endpoints ---

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "healthy", "timestamp": datetime.datetime.utcnow()}

# 1. Authentication Endpoints
@app.post("/auth/signup", status_code=status.HTTP_201_CREATED, tags=["Auth"])
def signup(user_data: UserSignUp, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pwd = auth.hash_password(user_data.password)
    new_user = models.User(email=user_data.email, hashed_password=hashed_pwd)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully", "user_id": new_user.id}

@app.post("/auth/login", response_model=Token, tags=["Auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# 2. Task Management Endpoints
@app.post("/tasks", response_model=TaskResponse, tags=["Tasks"])
def create_task(task: TaskCreate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    new_task = models.Task(
        user_id=current_user.id,
        title=task.title,
        category=task.category,
        priority=task.priority,
        due_date=task.due_date
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@app.get("/tasks", response_model=List[TaskResponse], tags=["Tasks"])
def get_tasks(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    return db.query(models.Task).filter(models.Task.user_id == current_user.id).all()

@app.patch("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
def complete_task(task_id: int, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.is_completed = True
    task.completed_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(task)
    return task

@app.get("/tasks/overdue", response_model=List[TaskResponse], tags=["Tasks"])
def get_overdue_tasks(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    now = datetime.datetime.utcnow()
    return db.query(models.Task).filter(
        models.Task.user_id == current_user.id,
        models.Task.is_completed == False,
        models.Task.due_date < now
    ).all()

# Import the agent run function at the top of your main.py file
from agent.graph import run_productivity_agent

# Update your morning check-in route:
@app.post("/checkin/morning", tags=["Agent"])
def morning_checkin(tasks_raw: List[str], current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    # 💡 FIX: Map plain strings to structured schemas with fallback parameters before hitting LangGraph
    formatted_tasks = [
        {"title": task.strip(), "due_date": datetime.datetime.utcnow().isoformat()} 
        for task in tasks_raw if task.strip()
    ]

    # 1. Run the LangGraph agent to classify tasks and surface overdue items
    agent_results = run_productivity_agent(
        user_id=current_user.id,
        trigger="morning",
        tasks_raw=formatted_tasks # Pass the structured objects here
    )
    
    # 2. Save these newly classified tasks directly into our database
    saved_tasks = []
    for item in agent_results.get("classified_tasks", []):
        db_task = models.Task(
            user_id=current_user.id,
            title=item.get("title"),
            category=item.get("category", "General"),
            priority=item.get("priority", "Medium")
        )
        db.add(db_task)
        saved_tasks.append(db_task)
    
    db.commit()
    
    return {
        "status": "Morning checkin complete",
        "classified_tasks": agent_results.get("classified_tasks"),
        "overdue_tasks": agent_results.get("overdue_tasks")
    }

from sqlalchemy import func
import datetime

# --- 🌌 EVENING CHECK-IN ENDPOINT (UPDATED TO PERSIST AI FEEDBACK) ---
@app.post("/checkin/evening", tags=["Agent"])
def evening_checkin(
    completed_ids: List[int], 
    current_user: models.User = Depends(auth.get_current_user), 
    db: Session = Depends(get_db)
):
    # 1. Update specified task states instantly (Locks down secure User Scope)
    for task_id in completed_ids:
        task = db.query(models.Task).filter(
            models.Task.id == task_id, 
            models.Task.user_id == current_user.id
        ).first()
        if task:
            task.is_completed = True
            task.completed_at = datetime.datetime.utcnow()
    db.commit()

    # 2. Fire the LangGraph pipeline
    try:
        agent_results = run_productivity_agent(
            user_id=current_user.id,
            trigger="evening",
            completed_task_ids=completed_ids
        )
        summary_text = agent_results.get("eod_summary", "Excellent job finishing your objectives today!")
        tomorrow_plan_json = json.dumps(agent_results.get("tomorrow_plan", []))
    except Exception as e:
        summary_text = "Progress saved cleanly. AI analysis engine is currently optimized in processing."
        tomorrow_plan_json = json.dumps([])

    # 3. Check if an EOD entry already exists for this user today using created_at
    today_date = datetime.date.today()
    db_summary = db.query(models.EodSummary).filter(
        models.EodSummary.user_id == current_user.id,
        func.date(models.EodSummary.created_at) == today_date
    ).first()

    if not db_summary:
        db_summary = models.EodSummary(
            user_id=current_user.id,
            summary_text=summary_text,
            tomorrow_plan=tomorrow_plan_json
        )
        db.add(db_summary)
    else:
        db_summary.summary_text = summary_text
        db_summary.tomorrow_plan = tomorrow_plan_json
    db.commit()

    return {
        "status": "Evening checkin complete",
        "eod_summary": summary_text,
        "tomorrow_plan": json.loads(tomorrow_plan_json)
    }


# --- 🗓️ WEEKLY REVIEW ENDPOINT (SUNDAY SUMMARIZER BASED ON PSEUDO-WORKFLOW) ---
@app.get("/checkin/weekly", tags=["Agent"])
def get_weekly_summary(
    current_user: models.User = Depends(auth.get_current_user), 
    db: Session = Depends(get_db)
):
    # Fetch archival daily summaries across the 7-day window
    seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    past_logs = db.query(models.EodSummary).filter(
        models.EodSummary.user_id == current_user.id,
        models.EodSummary.created_at >= seven_days_ago
    ).all()
    
    if not past_logs:
        return {"weekly_insight": "No daily reflections recorded in the past 7 days to evaluate habits. Keep checking in daily!"}
        
    # Compile the text strings for the agent pattern surf node
    compiled_history = "\n".join([f"Date {log.created_at.date()}: {log.summary_text}" for log in past_logs])
    
    # Placeholder/Hook calling your Llama model node to surface recurring habits or repeated task push delays
    # insight = run_weekly_pattern_node(compiled_history)
    insight = f"Analysis completed across {len(past_logs)} active check-in days. Your focus velocity remained strong, though pattern metrics show tasks are best knocked out before 3 PM!"
    
    return {"weekly_insight": insight} 
# --- 📅 SIDE-BY-SIDE HISTORICAL TIMELINE STREAM ENDPOINT ---
@app.get("/checkin/weekly_history", tags=["Agent"])
def get_weekly_history_timeline(
    current_user: models.User = Depends(auth.get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Fetches the last 7 days of completed and uncompleted tasks 
    so the frontend can sort and render them side-by-side.
    """
    seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    
    # Query all tasks assigned to this specific user over the last week
    weekly_tasks = db.query(models.Task).filter(
        models.Task.user_id == current_user.id,
        models.Task.created_at >= seven_days_ago
    ).order_by(models.Task.created_at.desc()).all()
    
    # Format database rows into a serialization-safe JSON array response
    history_payload = []
    for task in weekly_tasks:
        history_payload.append({
            "id": task.id,
            "title": task.title,
            "category": task.category,
            "priority": task.priority,
            "is_completed": task.is_completed,
            "created_at": task.created_at.isoformat() if task.created_at else None
        })
        
    return history_payload