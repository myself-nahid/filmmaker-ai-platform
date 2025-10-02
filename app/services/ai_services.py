import google.generativeai as genai
from app.core.config import settings
import time
import os
from google.oauth2 import service_account
import requests  
import time

genai.configure(api_key=settings.GOOGLE_API_KEY)
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

credentials = service_account.Credentials.from_service_account_file(
    settings.GOOGLE_DRIVE_CREDENTIALS_FILE
)
vertexai.init(
    project=settings.GOOGLE_CLOUD_PROJECT_ID,
    location=settings.GOOGLE_CLOUD_LOCATION,
    credentials=credentials
)

KIE_API_KEY = settings.KIE_API_KEY
KIE_API_BASE_URL = "https://api.kie.ai/api/v1/runway/generate" 

def generate_video_from_prompt(prompt: str):
    """
    Generates a video by submitting a job to the Kie.ai API and providing a
    callback URL for the result.
    """
    print(f"AI SERVICE: Submitting 'veo3' job to Kie.ai for prompt: '{prompt}'")
    
    headers = {
        "Authorization": f"Bearer {KIE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    submit_url = "https://api.kie.ai/api/v1/veo/generate"
    
    callback_url = f"{settings.PUBLIC_SERVER_URL}/api/v1/kie-callback"
    print(f"AI SERVICE: Providing this callback URL to Kie.ai: {callback_url}")

    submit_payload = {
        "prompt": prompt,
        "model": "veo3",
        "aspectRatio": "16:9",
        "callBackUrl": callback_url 
    }
    
    try:
        print(f"AI SERVICE: SENDING THIS EXACT VEO3 PAYLOAD: {submit_payload}")
        submit_response = requests.post(submit_url, headers=headers, json=submit_payload)
        
        if submit_response.status_code != 200:
            print(f"AI SERVICE: ERROR - Kie.ai returned status {submit_response.status_code}")
            print(f"AI SERVICE: Response Body: {submit_response.text}")
            submit_response.raise_for_status()

        response_data = submit_response.json()
        print(f"AI SERVICE: RECEIVED RAW RESPONSE FROM KIE.AI: {response_data}")
        
        data_dict = response_data.get("data") or {}
        job_id = data_dict.get("taskId")
        
        if not job_id:
            raise Exception("API reported success but did not return a recognizable job ID.")
            
        print(f"AI SERVICE: Job submitted successfully. Task ID: {job_id}")
        
        return job_id

    except requests.exceptions.HTTPError as http_err:
        print(f"AI SERVICE: HTTP ERROR: {http_err}")
        print(f"AI SERVICE: Response Body: {http_err.response.text}")
        raise http_err
    except Exception as e:
        print(f"AI SERVICE: CRITICAL FAILURE during video generation with Kie.ai: {e}")
        raise e

def generate_image_from_prompt_async(prompt: str):
    """
    Submits an asynchronous image generation job to the Kie.ai GPT-4o endpoint
    and returns the Kie.ai task ID.
    """
    print(f"AI SERVICE: Submitting 'gpt4o-image' job to Kie.ai for prompt: '{prompt}'")
    
    headers = {
        "Authorization": f"Bearer {KIE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    submit_url = "https://api.kie.ai/api/v1/gpt4o-image/generate"
    
    callback_url = f"{settings.PUBLIC_SERVER_URL}/api/v1/kie-callback"
    print(f"AI SERVICE: Providing this callback URL to Kie.ai: {callback_url}")
    submit_payload = {
        "prompt": prompt,
        "filesUrl": [], 
        "size": "1:1",
        "callBackUrl": callback_url,
        "isEnhance": False,
        "nVariants": 1
    }
    
    try:
        print(f"AI SERVICE: SENDING THIS EXACT GPT4O-IMAGE PAYLOAD: {submit_payload}")
        submit_response = requests.post(submit_url, headers=headers, json=submit_payload)
        
        if submit_response.status_code != 200:
            print(f"AI SERVICE: ERROR - Kie.ai returned status {submit_response.status_code}")
            print(f"AI SERVICE: Response Body: {submit_response.text}")
            submit_response.raise_for_status()

        response_data = submit_response.json()
        print(f"AI SERVICE: RECEIVED RAW RESPONSE FROM KIE.AI: {response_data}")
        
        data_dict = response_data.get("data") or {}
        job_id = data_dict.get("taskId")
        
        if not job_id:
            raise Exception("API reported success but did not return a recognizable job ID.")
            
        print(f"AI SERVICE: Image job submitted successfully. Task ID: {job_id}")
        return job_id

    except Exception as e:
        print(f"AI SERVICE: CRITICAL FAILURE during image submission with Kie.ai: {e}")
        raise e

def analyze_script(script_text: str):
    """
    Analyzes a screenplay using the Gemini model.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"Analyze the following screenplay for plot structure, character development, and dialogue quality:\n\n{script_text}"
    response = model.generate_content(prompt)
    return response.text