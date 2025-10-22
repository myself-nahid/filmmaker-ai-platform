import os
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
def analyze_script(script_text: str):
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"Analyze the following screenplay for plot structure, character development, and dialogue quality:\n\n{script_text}"
    response = model.generate_content(prompt)
    return {"analysis": response.text}