import os
from fastapi import UploadFile
from typing import Optional, List
import requests
import google.generativeai as genai
from app.core.config import settings

# Configure Keys
os.environ["KIE_API_KEY"] = settings.KIE_API_KEY
genai.configure(api_key=settings.GOOGLE_API_KEY)

# --- Video & Image Generation ---
async def submit_kie_job(prompt: str, internal_task_id: str, service_type: str):
    headers = {"Authorization": f"Bearer {settings.KIE_API_KEY}", "Content-Type": "application/json"}
    callback_url = f"{settings.PUBLIC_SERVER_URL}/api/v1/kie-callback"
    
    # Store the internal task ID in the callback URL to get it back later
    # This is a robust way to track which job belongs to whom without a database
    callback_url_with_id = f"{callback_url}?internal_task_id={internal_task_id}"

    payload = {}
    if service_type == "video":
        url = "https://api.kie.ai/api/v1/veo/generate"
        payload = {"prompt": prompt, "model": "veo3", "aspectRatio": "16:9", "callBackUrl": callback_url_with_id}
    elif service_type == "image":
        url = "https://api.kie.ai/api/v1/gpt4o-image/generate"
        payload = {"prompt": prompt, "filesUrl": [], "size": "1:1", "callBackUrl": callback_url_with_id}
    else:
        raise ValueError("Invalid service type specified")

    print(f"Submitting {service_type} job to Kie.ai for internal task {internal_task_id}")
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    print("Kie.ai job submitted successfully.")
    return response.json()

# --- Script Analysis ---
async def analyze_script(prompt: Optional[str] = None, files: Optional[List[UploadFile]] = None):
    """
    Analyzes a screenplay by combining a text prompt and the content of uploaded files.
    """
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    script_content = ""
    # Read the content from each uploaded file
    if files:
        for file in files:
            contents = await file.read()
            try:
                # Append the decoded text to our script_content string
                script_content += contents.decode("utf-8") + "\n\n"
            except UnicodeDecodeError:
                # Handle cases where the file is not a valid text file
                print(f"Warning: Could not decode file {file.filename}. It might not be a text file.")
                continue

    # Combine the user's prompt (if any) with the file content
    full_prompt = f"Analyze the following screenplay content based on this user instruction: '{prompt or 'Provide a general analysis.'}'\n\n--- SCRIPT CONTENT START ---\n{script_content}\n--- SCRIPT CONTENT END ---"
    
    print("Sending combined prompt and script to Gemini for analysis...")
    response = model.generate_content(full_prompt)
    
    return {"analysis": response.text}