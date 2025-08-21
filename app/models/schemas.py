from pydantic import BaseModel, Field
from typing import Optional

class VideoGenerationRequest(BaseModel):
    prompt: str = Field(..., example="A cinematic shot of a futuristic city at sunset.")

class VideoGenerationResponse(BaseModel):
    task_id: str
    message: str

class ImageGenerationRequest(BaseModel):
    prompt: str = Field(..., example="A hyper-realistic portrait of a golden retriever wearing a crown.")

class ImageGenerationResponse(BaseModel):
    image_url: str

class ScriptAnalysisRequest(BaseModel):
    script_text: str = Field(..., example="[SCENE START]\nINT. COFFEE SHOP - DAY\n...")

class ScriptAnalysisResponse(BaseModel):
    analysis: str