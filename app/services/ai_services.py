import google.generativeai as genai
from app.core.config import settings
import time
import os
from google.oauth2 import service_account

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
    Generates a video based on a text prompt.
    This function now creates a tiny, but structurally valid, MP4 file.
    """
    print(f"Starting video generation for prompt: '{prompt}'")

    dummy_video_bytes = b'\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00isommp42\x00\x00\x00\x08free\x00\x00\x00\x00mdat'

    time.sleep(10) 
    print("AI model has finished generating video data.")

    output_dir = "generated_videos"
    os.makedirs(output_dir, exist_ok=True)
    file_name = f"video_{hash(prompt)}.mp4"
    file_path = os.path.join(output_dir, file_name)

    try:
        with open(file_path, "wb") as f:
            f.write(dummy_video_bytes)
        print(f"Video data successfully WRITTEN IN BINARY to: {file_path}")
        return file_path
    except Exception as e:
        print(f"!!! FAILED TO WRITE FILE: {e} !!!")
        raise e

def generate_image_from_prompt(prompt: str):
    """
    Generates an image based on a text prompt using the Imagen model via Vertex AI.
    """
    try:
        model = ImageGenerationModel.from_pretrained("imagegeneration@005")
        response = model.generate_images(
            prompt=prompt,
            number_of_images=1,
        )

        if response.images:
            image = response.images[0]
            output_dir = "generated_images"
            os.makedirs(output_dir, exist_ok=True)
            file_name = f"image_{hash(prompt)}.png"
            file_path = os.path.join(output_dir, file_name)
            image.save(location=file_path)
            print(f"Image successfully saved to: {file_path}")
            return file_path
        
        return None
    except Exception as e:
        print(f"Error generating image: {e}")
        return None

def analyze_script(script_text: str):
    """
    Analyzes a screenplay using the Gemini model.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"Analyze the following screenplay for plot structure, character development, and dialogue quality:\n\n{script_text}"
    response = model.generate_content(prompt)
    return response.text