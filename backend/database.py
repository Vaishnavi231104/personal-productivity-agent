import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 🔌 1. LOAD ENVIRONMENT VARIABLES
# Reads variables out of your local .env file. Passes silently in production.
load_dotenv()

# 🚀 2. DYNAMIC DATABASE URL SELECTION
# Captures production cloud connection strings or defaults to your local SQLite file
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# Safety handler for Render's default "postgres://" syntax scheme
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


# 🛠️ 3. CONDITIONAL ARGUMENT ALLOCATION
# SQLite requires 'check_same_thread', but passing an empty dictionary prevents Postgres from crashing.
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}


# 🏗️ 4. ENGINE & TRANSACTION SESSION BUILD
engine = create_engine(
    DATABASE_URL, 
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# 🛡️ 5. DATABASE SESSION DEPENDENCY PROVIDER
# Yields transaction boundaries context-mapped to your incoming FastAPI requests
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()