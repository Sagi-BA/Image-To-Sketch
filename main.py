import asyncio
import os
import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io
from utils.BatchSketchApp import ImageToSketchProcessor

# Initialize components
from utils.init import initialize
from utils.counter import initialize_user_count, increment_user_count, get_user_count
from utils.TelegramSender import TelegramSender

# Initialize session state
if 'state' not in st.session_state:
    st.session_state.state = {
        'telegram_sender': TelegramSender(),
        'counted': False,
    }

# Set page config for better mobile responsiveness
# Set page config at the very beginning
st.set_page_config(layout="wide", initial_sidebar_state="collapsed", page_title="מחולל תמונות AI", page_icon="📷")

async def send_telegram_message_and_file(message, file_content: io.BytesIO):
    sender = TelegramSender()
    try:
        # Verify bot token
        if await sender.verify_bot_token():
            # Reset the file pointer to the beginning
            # file_content.seek(0)
            
            # Modify the send_document method to accept BytesIO
            await sender.send_document(file_content, caption=message)
        else:
            raise Exception("Bot token verification failed")
    except Exception as e:
        raise Exception(f"Failed to send Telegram message: {str(e)}")
    finally:
        await sender.close_session()

def load_html_file(file_name):
    with open(file_name, 'r', encoding='utf-8') as f:
        return f.read()
    
def load_footer():
    footer_path = os.path.join('utils', 'footer.md')
    if os.path.exists(footer_path):
        with open(footer_path, 'r', encoding='utf-8') as footer_file:
            return footer_file.read()
    return None  # Return None if the file doesn't exist

async def send_telegram_message_and_file(message, original_image, sketch_image):
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

def resize_image(image, max_width=800):
    """Resize image to fit within max_width while maintaining aspect ratio"""
    w_percent = max_width / float(image.size[0])
    h_size = int(float(image.size[1]) * float(w_percent))
    return image.resize((max_width, h_size), Image.LANCZOS)

async def main():
    title, image_path, footer_content = initialize()
    st.title("המרה של תמונות לסקיצות אמנותיות")

    # Load and display the custom expander HTML
    expander_html = load_html_file('expander.html')
    st.markdown(expander_html, unsafe_allow_html=True)  
    
    uploaded_file = st.file_uploader("בחרו תמונה...", type=["jpg", "jpeg", "png"])    
    
    if uploaded_file is not None:
        try:
            # Read file as bytes
            file_bytes = uploaded_file.read()
            
            if len(file_bytes) == 0:
                st.error("הקובץ שהועלה ריק. אנא נסה קובץ אחר.")
                return
            
            # Open image with PIL
            image = Image.open(io.BytesIO(file_bytes))
            
            # Convert to OpenCV format
            np_array = np.frombuffer(file_bytes, np.uint8)
            opencv_image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
            
            if opencv_image is None:
                st.error("נכשל בפענוח התמונה עם OpenCV. ייתכן שהקובץ פגום או בפורמט שאינו נתמך.")
                return
            
            # Convert to sketch
            sketch = ImageToSketchProcessor.convert_to_sketch(opencv_image)
            
            # Convert sketch back to PIL Image
            sketch_image = Image.fromarray(sketch)
            
            # Resize images
            image_resized = resize_image(image)
            sketch_resized = resize_image(sketch_image)
            
            # Display images side by side
            col1, col2 = st.columns(2)
            with col1:
                st.image(image_resized, caption="התמונה המקורית", use_column_width=True)
            with col2:
                st.image(sketch_resized, caption="הסקיצה", use_column_width=True)
            
            # Add download button for sketch
            buffered = io.BytesIO()
            sketch_image.save(buffered, format="PNG")
            st.download_button(
                label="הורד סקיצה",
                data=buffered.getvalue(),
                file_name="sketch.png",
                mime="image/png"
            )
            
            # Send message to Telegram            
            await send_telegram_message_and_file("סקיצה של תמונה", image, sketch_image)
            
        except Exception as e:
            st.error(f"אירעה שגיאה בעיבוד התמונה: {str(e)}")
            st.error("אנא נסה להעלות תמונה אחרת או בדוק אם הקובץ פגום.")
        
    # Display footer content
    st.markdown(footer_content, unsafe_allow_html=True)    

    # Display user count after the chatbot
    user_count = get_user_count(formatted=True)
    st.markdown(f"<p class='user-count' style='color: #4B0082;'>סה\"כ משתמשים: {user_count}</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    if 'counted' not in st.session_state:
        st.session_state.counted = True
        increment_user_count()
    initialize_user_count()
    asyncio.run(main())