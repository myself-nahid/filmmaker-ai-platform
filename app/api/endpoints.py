from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Depends, Request, Form
from typing import Optional, Any
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
    task = crud.create_task(db=db, prompt=request.prompt, owner_id=request.user_id)
    
    background_tasks.add_task(process_video_generation, task.id, task.prompt)
    
    return {"task_id": task.id, "message": "Video generation task has been submitted."}

@router.get("/tasks/{task_id}", response_model=schemas.Task)
async def get_task_status(task_id: str, user_id: str, db: Session = Depends(get_db)): 
    db_task = crud.get_task_for_user(db, task_id=task_id, owner_id=user_id) 
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found or you do not have permission to view it")
    return db_task


@router.post("/generate-image", response_model=schemas.VideoGenerationResponse) 
async def generate_image(
    request: schemas.ImageGenerationRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Starts an asynchronous image generation task and returns a task ID for tracking.
    """
    task = crud.create_task(db=db, prompt=request.prompt, owner_id=request.user_id)
    
    background_tasks.add_task(process_image_generation, task.id, task.prompt)
    
    return {"task_id": task.id, "message": "Image generation task has been submitted."}

@router.post("/analyze-script", response_model=schemas.ScriptAnalysisResponse)
async def analyze_script(
    script_text: Optional[str] = Form(None),
    file: Any = File(None) 
):
    """
    Analyzes a screenplay from either an uploaded file or raw text.
    - If a file is provided, it will be prioritized and analyzed.
    - If no file is provided, the script_text will be analyzed.
    - If neither is provided, an error is returned.
    """
    
    final_script_text = ""

    if isinstance(file, UploadFile):
        print("Processing script from uploaded file.")
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="The uploaded file is empty.")
        
        try:
            final_script_text = contents.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Could not decode the file. Please ensure it is a valid text file.")

    elif script_text:
        print("Processing script from raw text input.")
        final_script_text = script_text

    else:
        raise HTTPException(status_code=400, detail="You must provide either a script file or script text to analyze.")

    if not final_script_text.strip():
        raise HTTPException(status_code=400, detail="The provided script content is empty or contains only whitespace.")

    print("Sending script to AI for analysis...")
    analysis = ai_services.analyze_script(final_script_text)
    
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


@router.post("/kie-callback")
async def kie_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    This endpoint receives the final result from the Kie.ai webhook
    and updates the correct task in the database using the external_id.
    """
    callback_body = await request.json()
    print(f"\n--- RAW CALLBACK BODY RECEIVED FROM KIE.AI ---\n{callback_body}\n---------------------------------------------\n")

    try:
        if callback_body.get("code") != 200:
            return {"status": "callback received with error"}

        data_dict = callback_body.get("data")
        if not data_dict:
            raise ValueError("Callback data does not contain a 'data' field.")

        external_task_id = data_dict.get("taskId")
        if not external_task_id:
            raise ValueError("Callback 'data' object does not contain a 'taskId'.")
            
        db_task = crud.get_task_by_external_id(db, external_id=external_task_id)
        if not db_task:
            raise ValueError(f"No task found in our database with external_id: {external_task_id}")

        info_dict = data_dict.get("info")
        if not info_dict:
            raise ValueError("Callback 'data' object does not contain an 'info' field.")
            
        result_urls = info_dict.get("resultUrls") or info_dict.get("result_urls")
        if not result_urls or not isinstance(result_urls, list) or len(result_urls) == 0:
            raise ValueError("Callback 'info' object does not contain a valid list of result URLs.")
            
        final_video_url = result_urls[0]
        
        print(f"CALLBACK SUCCESS: Found internal task '{db_task.id}'. Updating with Video URL '{final_video_url}'")
        
        crud.update_task(
            db,
            task_id=db_task.id, 
            status=TaskStatus.COMPLETED,
            result_url=final_video_url
        )
        
        return {"status": "callback received and processed successfully"}

    except (ValueError, KeyError) as e:
        print(f"CALLBACK PARSING ERROR: {e}")
        return {"status": "callback received but data was in an unexpected format"}


def process_video_generation(task_id: str, prompt: str):
    db = SessionLocal()
    try:
        crud.update_task(db, task_id=task_id, status=TaskStatus.PROCESSING)
        
        kie_task_id = ai_services.generate_video_from_prompt(prompt)
        
        crud.link_task_ids(db, internal_task_id=task_id, external_task_id=kie_task_id)

        print(f"Task {task_id}: Job successfully submitted to Kie.ai and linked with their Task ID: {kie_task_id}.")

    except Exception as e:
        crud.update_task(db, task_id=task_id, status=TaskStatus.FAILED, result_url=str(e))
        print(f"Task {task_id}: Failed during submission. Error: {e}")
    finally:
        db.close()


def process_image_generation(task_id: str, prompt: str):
    db = SessionLocal()
    try:
        crud.update_task(db, task_id=task_id, status=TaskStatus.PROCESSING)
        kie_task_id = ai_services.generate_image_from_prompt_async(prompt)
        crud.link_task_ids(db, internal_task_id=task_id, external_task_id=kie_task_id)
        print(f"Task {task_id}: Image job successfully submitted to Kie.ai and linked with their Task ID: {kie_task_id}.")

    except Exception as e:
        crud.update_task(db, task_id=task_id, status=TaskStatus.FAILED, result_url=str(e))
        print(f"Task {task_id}: Failed during image submission. Error: {e}")
    finally:
        db.close()