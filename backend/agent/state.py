from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    user_id: int
    tasks_raw: List[str]               # Raw input strings from morning check-in
    classified_tasks: List[Dict[str, Any]] # Tasks parsed into category, priority, etc.
    overdue_tasks: List[Dict[str, Any]]    # Pulled from DB by the agent
    completed_task_ids: List[int]       # IDs completed during evening review
    eod_summary: str                   # AI generated performance review paragraph
    tomorrow_plan: List[str]           # AI suggested task list for the next day
    trigger: str                       # Tells graph whether it's "morning" or "evening"