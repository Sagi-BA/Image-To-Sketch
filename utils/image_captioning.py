import os
import requests
from io import BytesIO
from PIL import Image
from tenacity import retry, stop_after_attempt, wait_fixed
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class ImageCaptioning:
    def __init__(self):
        self.HF_TOKEN = os.getenv("HF_TOKEN")
        self.API_URL = os.getenv("HF_IMAGF_CAPTIONING_URL")

        if not self.HF_TOKEN:
            raise ValueError("Hugging Face token must be set in environment variables")
        if not self.API_URL:
            raise ValueError("Hugging Face URL must be set in environment variables")
        
        self.headers = {"Authorization": f"Bearer {self.HF_TOKEN}"}
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
    def get_image_captioning(self, image: Image.Image):
        # Convert the PIL Image to bytes
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        # Send the image data (as bytes) to the API
        response = requests.post(self.API_URL, headers=self.headers, data=img_byte_arr)
        response_json = response.json()

        # Check if the response is a list and extract the first item's 'generated_text'
        if isinstance(response_json, list) and 'generated_text' in response_json[0]:
            generated_text = response_json[0]['generated_text']
        else:
            generated_text = 'No caption found'

        return generated_text

def main():
    # Create an instance of the ImageCaptioning class
    captioning = ImageCaptioning()

    # Load the image from the local folder
    image_path = "shawarma.png"
    image = Image.open(image_path)

    try:
        # Get the generated caption
        generated_text = captioning.get_image_captioning(image)

        # Print the extracted text
        print("Image Caption:", generated_text)
    except Exception as e:
        print(f"An error occurred: {e}")

# To run the main function asynchronously
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
