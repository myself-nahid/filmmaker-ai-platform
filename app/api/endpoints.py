from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models import schemas
from app.services import ai_services, google_drive
from app import crud
from app.database import SessionLocal, get_db
from app.models.models import TaskStatus
import os

router = APIRouter()

def process_video_generation(task_id: str, prompt: str):
    db = SessionLocal()
    try:
        crud.update_task(db, task_id=task_id, status=TaskStatus.PROCESSING)
        print(f"Task {task_id}: Started processing.")
        
        video_url = ai_services.generate_video_from_prompt(prompt)
        
        crud.update_task(db, task_id=task_id, status=TaskStatus.COMPLETED, result_url=video_url)
        print(f"Task {task_id}: Completed successfully.")

    except Exception as e:
        crud.update_task(db, task_id=task_id, status=TaskStatus.FAILED, result_url=str(e))
        print(f"Task {task_id}: Failed. Error: {e}")
    finally:
        db.close()

@router.post("/generate-video", response_model=schemas.VideoGenerationResponse)
async def generate_video(
    request: schemas.VideoGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    task = crud.create_task(db=db, prompt=request.prompt)
    
    background_tasks.add_task(process_video_generation, task.id, task.prompt)
    
    return {"task_id": task.id, "message": "Video generation task has been submitted."}

@router.get("/tasks/{task_id}", response_model=schemas.Task)
async def get_task_status(task_id: str, db: Session = Depends(get_db)):
    db_task = crud.get_task(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@router.post("/generate-image", response_model=schemas.ImageGenerationResponse)
async def generate_image(request: schemas.ImageGenerationRequest):
    """
    Generate an image from a text prompt.
    """
    image_url = ai_services.generate_image_from_prompt(request.prompt)
    
    if image_url is None:
        raise HTTPException(
            status_code=500, 
            detail="Failed to generate image. Check server logs for more details."
        )
        
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