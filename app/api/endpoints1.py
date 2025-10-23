from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Form, UploadFile, File
from typing import Optional, List
from app.services import service
from pydantic import BaseModel
from app.core.config import settings
import httpx 

router = APIRouter()

# --- PAYLOADS ---
class GenerationRequest(BaseModel):
    internal_task_id: str
    prompt: str

class ScriptRequest(BaseModel):
    prompt: str = Form(...),
    files: list[UploadFile] = File(...)

# --- ENDPOINTS ---
@router.post("/generate-video")
async def generate_video(request: GenerationRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(service.submit_kie_job, request.prompt, request.internal_task_id, "video")
    return {"status": "video generation job accepted"}

@router.post("/generate-image")
async def generate_image(request: GenerationRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(service.submit_kie_job, request.prompt, request.internal_task_id, "image")
    return {"status": "image generation job accepted"}

@router.post("/analyze-script")
async def analyze_script(
    prompt: Optional[str] = Form(None), 
    files: Optional[List[UploadFile]] = File(None)
):
    """
    Analyzes a screenplay from an optional uploaded file and/or optional text prompt.
    """
    # We must have at least a prompt or a file
    if not prompt and not files:
        raise HTTPException(status_code=400, detail="You must provide either a script file or a text prompt.")

    # Pass the received data to the service layer for processing
    return await service.analyze_script(prompt=prompt, files=files)

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