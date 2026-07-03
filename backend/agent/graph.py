import datetime 
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agent.state import AgentState
from agent.nodes import (
    classifier_node,
    overdue_surfacer_node,
    eod_summarizer_node,
    next_day_planner_node
)

# 1. Initialize our StateGraph with the custom AgentState structure
workflow = StateGraph(AgentState)

# 2. Add our execution nodes to the graph canvas
workflow.add_node("classifier", classifier_node)
workflow.add_node("overdue_surfacer", overdue_surfacer_node)
workflow.add_node("eod_summarizer", eod_summarizer_node)
workflow.add_node("next_day_planner", next_day_planner_node)

# 3. Create the Conditional Routing Logic
def route_by_trigger(state: AgentState) -> str:
    """Inspects the state trigger and determines which path the graph travels down."""
    if state.get("trigger") == "morning":
        return "morning_path"
    else:
        return "evening_path"

# 4. Wire up the entry point and connections
workflow.set_conditional_entry_point(
    route_by_trigger,
    {
        "morning_path": "classifier",
        "evening_path": "eod_summarizer"
    }
)

# Morning Flow Path
workflow.add_edge("classifier", "overdue_surfacer")
workflow.add_edge("overdue_surfacer", END)

# Evening Flow Path
workflow.add_edge("eod_summarizer", "next_day_planner")
workflow.add_edge("next_day_planner", END)

# 5. Compile the graph with an in-memory checkpointer for thread safety
memory = MemorySaver()
app_graph = workflow.compile(checkpointer=memory)


def run_productivity_agent(user_id: int, trigger: str, tasks_raw: list = None, completed_task_ids: list = None) -> dict:
    """
    Helper function called directly from FastAPI endpoints to execute 
    the state machine pipeline.
    """
    initial_state = {
        "user_id": user_id,
        "trigger": trigger,
        "tasks_raw": tasks_raw or [],
        "completed_task_ids": completed_task_ids or [],
        "classified_tasks": [],
        "overdue_tasks": [],
        "eod_summary": "",
        "tomorrow_plan": []
    }
    
    # Run the compiled graph (using a mock thread configuration id for checkpointing)
    config = {"configurable": {"thread_id": f"user_{user_id}_{datetime_stamp()}"}}
    final_output = app_graph.invoke(initial_state, config=config)
    return final_output

def datetime_stamp():
    import datetime
    return datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")