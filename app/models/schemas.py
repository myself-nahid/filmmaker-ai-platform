from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .models import TaskStatus 

class TaskBase(BaseModel):
    prompt: str

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: str
    status: TaskStatus
    result_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 

class VideoGenerationRequest(BaseModel):
    prompt: str = Field(..., example="A cinematic shot of a futuristic city at sunset.")
    user_id: str
class VideoGenerationResponse(BaseModel):
    task_id: str
    message: str

class ImageGenerationRequest(BaseModel):
    prompt: str = Field(..., example="A hyper-realistic portrait of a golden retriever wearing a crown.")
    user_id: str
class ImageGenerationResponse(BaseModel):
    image_url: str

class ScriptAnalysisRequest(BaseModel):
    script_text: str = Field(..., example="[SCENE START]\nINT. COFFEE SHOP - DAY\n...")

class ScriptAnalysisResponse(BaseModel):
    analysis: str

class KieCallbackData(BaseModel):
    taskId: str
    status: str
    output_url: Optional[str] = None
    error: Optional[str] = None