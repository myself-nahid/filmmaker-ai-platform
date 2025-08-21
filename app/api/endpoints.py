from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from app.models import schemas
from app.services import ai_services, google_drive
import os

router = APIRouter()

def process_video_generation(prompt: str):
    """A wrapper function for the background task."""
    video_url = ai_services.generate_video_from_prompt(prompt)
    print(f"Video generated: {video_url}")

@router.post("/generate-video", response_model=schemas.VideoGenerationResponse)
async def generate_video(request: schemas.VideoGenerationRequest, background_tasks: BackgroundTasks):
    """
    Generate a video from a text prompt. This is a long-running task and will be processed in the background. [2, 12]
    """
    background_tasks.add_task(process_video_generation, request.prompt)
    return {"task_id": "some_unique_task_id", "message": "Video generation started in the background."}

@router.post("/generate-image", response_model=schemas.ImageGenerationResponse)
async def generate_image(request: schemas.ImageGenerationRequest):
    """
    Generate an image from a text prompt.
    """
    image_url = ai_services.generate_image_from_prompt(request.prompt)
    return {"image_url": image_url}

@router.post("/analyze-script-text", response_model=schemas.ScriptAnalysisResponse)
async def analyze_script_from_text(request: schemas.ScriptAnalysisRequest):
    """
    Analyze a screenplay provided as text.
    """
    analysis = ai_services.analyze_script(request.script_text)
    return {"analysis": analysis}

@router.post("/analyze-script-file", response_model=schemas.ScriptAnalysisResponse)
async def analyze_script_from_file(file: UploadFile = File(...)):
    """
    Analyze a screenplay from an uploaded file.
    """
    contents = await file.read()
    script_text = contents.decode("utf-8")
    analysis = ai_services.analyze_script(script_text)
    return {"analysis": analysis}

@router.post("/upload-to-drive")
async def upload_to_drive(file: UploadFile = File(...)):
    """
    Upload a file to Google Drive.
    """
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    file_id = google_drive.upload_file_to_drive(temp_file_path, file.filename)
    os.remove(temp_file_path)
    
    return {"file_id": file_id, "file_name": file.filename}