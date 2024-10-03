# https://molmo.org/dashboard
# $ pip install gradio_client
import os
from dotenv import load_dotenv

from gradio_client import Client, handle_file
from huggingface_hub import HfApi


# Load environment variables from .env file
load_dotenv()

# Initialize the Hugging Face API client
hf_api = HfApi(token=os.getenv("HF_TOKEN"))

# Create the Gradio client with your token
client = Client("akhaliq/Molmo-7B-D-0924", hf_token=hf_api.token)

try:
    # image=handle_file('testing/color_image1.jpg')

    # Use a local file path instead of a URL
    result = client.predict(
     	image=handle_file('https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/bus.png'),
        text="what do you see ?",
        api_name="/chatbot"
    )
    print(result)
except Exception as e:
    if "exceeded your GPU quota" in str(e):
        print("GPU quota exceeded. Please wait and try again later, or consider creating a Hugging Face account for increased quota.")
    else:
        print(f"An error occurred: {str(e)}")

# from gradio_client import Client, handle_file

# client = Client("akhaliq/Molmo-7B-D-0924")
# result = client.predict(
# 		# image=handle_file('https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/bus.png'),
#         image=handle_file('https://i.imgur.com/TQWu7c5.jpeg'),
# 		# text="Hello!!",
#         text="what do you see ?",
# 		api_name="/chatbot"
# )
# print(result)

# from gradio_client import Client, handle_file
# import requests

# client = Client("akhaliq/Molmo-7B-D-0924")

# def get_image_content(url):
#     response = requests.get(url)
#     response.raise_for_status()  # This will raise an exception for 4xx and 5xx status codes
#     return response.content

# try:
#     image_content = get_image_content('https://i.imgur.com/TQWu7c5.jpeg')
#     result = client.predict(
#         image=handle_file(image_content),
#         text="what do you see ?",
#         api_name="/chatbot"
#     )
#     print(result)
# except Exception as e:
#     print(f"An error occurred: {str(e)}")
