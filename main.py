import time
import streamlit as st
from PIL import Image
import io
import numpy as np
import cv2
import asyncio
import base64
import os
import uuid

# Initialize components
from utils.BatchSketchApp import ImageToSketchProcessor
from utils.ImageTransitionAnimator import ImageTransitionAnimator
from utils.image_captioning import ImageCaptioning
from deep_translator import GoogleTranslator
from utils.imgur_uploader import ImgurUploader
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
st.set_page_config(layout="wide", initial_sidebar_state="collapsed", page_title="המרה של תמונות לסקיצות אמנותיות", page_icon="🖼️")

def image_to_bytes(image: Image.Image) -> io.BytesIO:
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

async def send_telegram_message_and_file(message, original_image, sketch_image, video_base64):
    sender = TelegramSender()
    try:
        # Convert the base64 video into BytesIO
        video_bytes = base64.b64decode(video_base64)
        video_buffer = io.BytesIO(video_bytes)
        
        # Verify the bot token
        if await sender.verify_bot_token():
            # First send the original and sketch images
            await sender.sketch_image(original_image, sketch_image, caption=message)
            
            # Then send the video as a file
            await sender.send_video(video_buffer, caption=message)
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

def resize_image(image, max_width=800):
    """Resize image to fit within max_width while maintaining aspect ratio"""
    w_percent = max_width / float(image.size[0])
    h_size = int(float(image.size[1]) * float(w_percent))
    return image.resize((max_width, h_size), Image.LANCZOS)

@st.cache_resource
def translate_to_hebrew(text):
    try:        
        translator = GoogleTranslator(source='auto', target='iw')
        return translator.translate(text)
    except Exception as e:
        st.error(f"שגיאה בתרגום: {str(e)}")
        return text

# Force a refresh by clearing and reassigning the video URL
def load_video(video_url, placeholder):
    placeholder.empty()  # Clear the placeholder
    time.sleep(2)  # Small delay to ensure the placeholder is cleared
    placeholder.video(video_url, autoplay=True, loop=True)

async def main():
    title, image_path, footer_content = initialize()
    st.title("המרת תמונות לסקיצות אמנותיות")

    # Load and display the custom expander HTML
    expander_html = load_html_file('expander.html')
    st.markdown(expander_html, unsafe_allow_html=True)  
    
    uploaded_file = st.file_uploader("בחרו תמונה...", type=["jpg", "jpeg", "png", "webp"])    
    
    if uploaded_file is not None:
        try:
            # Read file as bytes
            file_bytes = uploaded_file.read()
            
            if len(file_bytes) == 0:
                st.error("הקובץ שהועלה ריק. אנא נסה קובץ אחר.")
                return
            
             # Open the image            
            image = Image.open(io.BytesIO(file_bytes))
            
            # Convert to OpenCV format
            np_array = np.frombuffer(file_bytes, np.uint8)
            opencv_image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
            
            if opencv_image is None:
                st.error("נכשל בפענוח התמונה עם OpenCV. ייתכן שהקובץ פגום או בפורמט שאינו נתמך.")
                return
            
            # Placeholder for caption
            caption_placeholder = st.empty()

            with st.spinner('מתאר את תוכן התמונה...'):
                captioning = ImageCaptioning()
                english_captioning = captioning.get_image_captioning(image)
                hebrew_captioning = translate_to_hebrew(english_captioning)
                caption_placeholder.success(hebrew_captioning)

            # Placeholder for images
            col1, col2 = st.columns(2)
            with col1:
                original_image_placeholder = st.empty()
            with col2:
                sketch_image_placeholder = st.empty()
            
            # Resize and display original image            
            image_resized = resize_image(image)
            original_image_placeholder.image(image_resized, caption="התמונה המקורית", use_column_width=True)
            
            # Convert to sketch
            sketch = ImageToSketchProcessor.convert_to_sketch(opencv_image)
            sketch_image = Image.fromarray(sketch)
            sketch_resized = resize_image(sketch_image)
            sketch_image_placeholder.image(sketch_resized, caption="הסקיצה", use_column_width=True)
            
            # Placeholder for VIDEO
            video_placeholder = st.empty()
            
            # Create the transition animation mp4 file
            with st.spinner('מייצר אנימציה...'):
                animator = ImageTransitionAnimator(sketch_image=sketch_resized, color_image=image_resized)
                frames = animator.create_transition_frames()
                video_base64 = animator.create_video_in_memory(frames)
        
            with st.spinner('מחבר את הכיתוב לתמונה...'):
                uploader = ImgurUploader()                
                video_url = uploader.upload_media_to_imgur(video_base64, "video", english_captioning, hebrew_captioning)                
            
            with st.spinner('יוצר את הוידאו זה ייקח כ 2 שניות...'):
                print(video_url)

                load_video(video_url, video_placeholder)
        
            # Add download button for sketch
            buffered = io.BytesIO()
            sketch_image.save(buffered, format="PNG")
            # Generate a unique image name
            unique_filename = f"sketch_{uuid.uuid4().hex}.png"

            # Convert image to base64 string
            buffered.seek(0)
            image_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            # Update the st.markdown with the corrected href
            # Update the st.markdown with custom CSS to center the download link on the image
            st.markdown(f"""
             <div class="gallery-container">
                <div class="image-container">
                    <a href="data:image/png;base64,{image_base64}" download="{unique_filename}" class="centered-link">
                        הורדת סקיצה
                    </a>&nbsp;
                    <a href="data:video/mp4;base64,{video_base64}" download="{video_url}" class="centered-link">
                        הורדת וידאו
                    </a>
                </div>                
            </div>
        """, unsafe_allow_html=True)
            
            # Send message to Telegram       
            await send_telegram_message_and_file(hebrew_captioning, image, sketch_image, video_base64)
                  
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