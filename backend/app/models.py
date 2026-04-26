from pydantic import BaseModel, Field
from typing import List, Optional

class AutoTaskRequest(BaseModel):
    user_prompt: str = Field(..., description="The task the user wants the AI agents to accomplish.")
    custom_plan: Optional[List[str]] = Field(None, description="The human-approved execution plan array.")
    context: Optional[List[str]] = Field(None, description="Recent task history for stateful memory.")

class AutoTaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

class PlanRequest(BaseModel):
    user_prompt: str
    context: Optional[List[str]] = Field(None, description="Recent task history.")

class PlanResponse(BaseModel):
    steps: List[str]
