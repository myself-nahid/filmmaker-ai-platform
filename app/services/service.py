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
import docx
from pypdf import PdfReader
import io
# --- END OF NEW IMPORTS ---

# ... (keep your existing setup and submit_kie_job function)

# --- SCRIPT ANALYSIS (NOW SEPARATED AND SIMPLIFIED) ---

def read_uploaded_file(file: UploadFile) -> str:
    """
    Reads an UploadFile object, verifies its type using magic numbers, 
    and returns its text content. Supports .txt, .pdf, and .docx.
    """
    filename = file.filename.lower()
    content = ""
    try:
        # Read the entire file into memory once.
        file_bytes = file.file.read()
        if not file_bytes:
            raise ValueError("The uploaded file is empty.")

        # --- NEW: FILE TYPE VERIFICATION (MAGIC NUMBER CHECK) ---
        is_pdf = file_bytes.startswith(b'%PDF-')
        is_docx = file_bytes.startswith(b'PK\x03\x04') # DOCX files are zip archives
        # --- END OF VERIFICATION ---

        if filename.endswith('.pdf') and is_pdf:
            print(f"Reading verified PDF file: {file.filename}")
            reader = PdfReader(io.BytesIO(file_bytes))
            for page in reader.pages:
                content += page.extract_text() or ""
        
        elif filename.endswith('.docx') and is_docx:
            print(f"Reading verified DOCX file: {file.filename}")
            doc = docx.Document(io.BytesIO(file_bytes))
            for para in doc.paragraphs:
                content += para.text + "\n"
        
        else: # Default to assuming it's a text file
            print(f"Reading file as plain text: {file.filename}")
            try:
                content = file_bytes.decode('utf-8')
            except UnicodeDecodeError:
                raise ValueError(f"File '{file.filename}' is not a valid PDF, DOCX, or UTF-8 text file.")

        if not content.strip():
            raise ValueError("Extracted text from the file is empty.")
            
        return content
        
    except ValueError as e:
        # Re-raise our own validation errors to be caught by the endpoint
        raise e
    except Exception as e:
        # Catch other parsing errors (e.g., from a corrupted but valid-looking file)
        print(f"ERROR: Could not read file {file.filename}. Reason: {e}")
        raise ValueError(f"Failed to process the file: {file.filename}. It may be corrupted or an unsupported format.")



async def analyze_script(script_text: str):
    """
    Analyzes a given string of screenplay text using the Gemini API.
    """
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    if not script_text or not script_text.strip():
        raise ValueError("No script text provided for analysis.")

    full_prompt = f"""You are an expert screenplay analyst. Please provide a comprehensive professional analysis of the following screenplay content, focusing on structure, character, dialogue, pacing, and overall potential.

--- SCREENPLAY CONTENT ---
{script_text}
--- END OF SCREENPLAY ---

Your analysis:"""
    
    try:
        response = model.generate_content(full_prompt)
        return {"analysis": response.text}
    except Exception as e:
        print(f"ERROR: Gemini API call failed. Reason: {e}")
        raise ValueError(f"Failed to get analysis from AI API: {e}")