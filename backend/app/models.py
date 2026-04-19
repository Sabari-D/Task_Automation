from pydantic import BaseModel, Field

class AutoTaskRequest(BaseModel):
    user_prompt: str = Field(..., description="The task the user wants the AI agents to accomplish.")

class AutoTaskResponse(BaseModel):
    task_id: str
    status: str
    message: str
