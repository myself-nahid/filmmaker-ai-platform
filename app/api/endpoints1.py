from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Form, UploadFile, File
from typing import Optional, List
from app.services import service
from pydantic import BaseModel
from app.core.config import settings
import httpx 
from app.models import schemas

router = APIRouter()

# --- PAYLOADS ---
class GenerationRequest(BaseModel):
    internal_task_id: str
    prompt: str

# class ScriptRequest(BaseModel):
#     prompt: str = Form(...),
#     files: list[UploadFile] = File(...)

# --- ENDPOINTS ---
@router.post("/generate-video")
async def generate_video(request: GenerationRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(service.submit_kie_job, request.prompt, request.internal_task_id, "video")
    return {"status": "video generation job accepted"}

@router.post("/generate-image")
async def generate_image(request: GenerationRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(service.submit_kie_job, request.prompt, request.internal_task_id, "image")
    return {"status": "image generation job accepted"}

class TextAnalysisRequest(BaseModel):
    script_text: str

@router.post("/analyze-script-text", response_model=schemas.AnalysisResponse) # <-- THE FIX
async def analyze_script_from_text(request: TextAnalysisRequest):
    """
    Analyzes a screenplay from a raw text string.
    """
    if not request.script_text or not request.script_text.strip():
        raise HTTPException(status_code=400, detail="script_text field cannot be empty.")
    
    try:
        return await service.analyze_script(script_text=request.script_text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")


@router.post("/analyze-script-file", response_model=schemas.AnalysisResponse) # <-- THE FIX
async def analyze_script_from_file(file: UploadFile = File(...)):
    """
    Analyzes a screenplay from an uploaded file (.txt, .pdf, .docx).
    """
    try:
        script_content = service.read_uploaded_file(file)
        return await service.analyze_script(script_text=script_content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")
@router.post("/kie-callback")
async def kie_callback(request: Request, internal_task_id: str):
    callback_body = await request.json()
    print(f"Callback received for internal task: {internal_task_id}")

    final_status = "failed"
    result_url = "Error: " + callback_body.get("msg", "Unknown error from callback")
    
    if callback_body.get("code") == 200:
        data = callback_body.get("data", {})
        info = data.get("info", {})
        urls = info.get("resultUrls") or info.get("result_urls")
        if urls:
            final_status = "completed"
            result_url = urls[0]

    # --- Handoff to Main Backend ---
    result_payload = {
        "task_id": internal_task_id,
        "status": final_status,
        "result_url": result_url
    }
    
    async with httpx.AsyncClient() as client:
        print(f"Sending final result to main backend: {result_payload}")
        await client.post(settings.MAIN_BACKEND_SAVE_URL, json=result_payload)

    return {"status": "callback processed and result forwarded"}