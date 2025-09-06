import google.generativeai as genai
from app.core.config import settings
import time
import os
from google.oauth2 import service_account

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_DRIVE_CREDENTIALS_FILE

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

def generate_video_from_prompt(prompt: str):
    """
    Generates a video based on a text prompt using the Veo model.
    (Conceptual - Final API may differ)
    """
    model = genai.GenerativeModel('models/veo')
    operation = model.generate_content_async(prompt)
    time.sleep(60) 
    print("Simulated video generation complete.")
    return "placeholder_video_url_from_veo"

def generate_image_from_prompt(prompt: str):
    """
    Generates an image based on a text prompt using the Imagen model via Vertex AI.
    """
    try:
        model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")  
        response = model.generate_images(
            prompt=prompt,
            number_of_images=1, 
        )

        if response.images:
            image = response.images[0]
            # return f"generated_image_{hash(prompt)}.png"
            output_dir = "generated_images"
            os.makedirs(output_dir, exist_ok=True)
            
            # 2. Create a unique filename and the full path
            file_name = f"image_{hash(prompt)}.png"
            file_path = os.path.join(output_dir, file_name)
            
            # 3. Save the image data to the file path
            image.save(location=file_path)
            print(f"Image successfully saved to: {file_path}")
            
            # 4. Return the path so you know where it is
            return file_path
        
        return None
    except Exception as e:
        print(f"Error generating image: {e}")
        return None


def analyze_script(script_text: str):
    """
    Analyzes a screenplay using the Gemini model.
    """
    model = genai.GenerativeModel('gemini-2.5-flash')  
    prompt = f"Analyze the following screenplay for plot structure, character development, and dialogue quality:\n\n{script_text}"
    response = model.generate_content(prompt)
    return response.text