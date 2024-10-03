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
from utils.image_effects import ImageEffects
from utils.html5_slideshow_component import display_image_slideshow  # Updated import

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

async def send_telegram_message_and_file(message, original_image, sketch_image, video_base64=None):
    sender = TelegramSender()
    try:
        # Verify the bot token
        if await sender.verify_bot_token():
            # Send the original and sketch images
            await sender.sketch_image(original_image, sketch_image, caption=message)
            
            # If video_base64 is provided, send the video as well
            if video_base64:
                video_bytes = base64.b64decode(video_base64)
                video_buffer = io.BytesIO(video_bytes)
                await sender.send_video(video_buffer, caption=message)
        else:
            raise Exception("Bot token verification failed")
    except Exception as e:
        st.error(f"Failed to send Telegram message: {str(e)}")
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
    
    # Initialize session state for tracking Telegram message sent
    if 'telegram_message_sent' not in st.session_state:
        st.session_state.telegram_message_sent = False
    
    if 'last_uploaded_file' not in st.session_state:
        st.session_state.last_uploaded_file = None

    uploaded_file = st.file_uploader("בחרו תמונה...", type=["jpg", "jpeg", "png", "webp", ".jfif"])    
    
    # Add the Image Carousel component
    st.subheader("גלריית דוגמאות")
    display_image_slideshow()  # Display the image slideshow

    # Reset telegram_message_sent if a new file is uploaded
    if uploaded_file is not None and uploaded_file != st.session_state.last_uploaded_file:
        st.session_state.telegram_message_sent = False
        st.session_state.last_uploaded_file = uploaded_file

    if uploaded_file is not None:
        try:
            # שלב 1: הצגת התמונה המקורית והסקיצה
            file_bytes = uploaded_file.read()
            
            if len(file_bytes) == 0:
                st.error("הקובץ שהועלה ריק. אנא נסה קובץ אחר.")
                return
            
            image = Image.open(io.BytesIO(file_bytes))
            np_array = np.frombuffer(file_bytes, np.uint8)
            opencv_image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
            
            if opencv_image is None:
                st.error("נכשל בפענוח התמונה עם OpenCV. ייתכן שהקובץ פגום או בפורמט שאינו נתמך.")
                return
            
            caption_placeholder = st.empty()

            with st.spinner('מתאר את תוכן התמונה...'):
                captioning = ImageCaptioning()
                english_captioning = captioning.get_image_captioning(image)
                hebrew_captioning = translate_to_hebrew(english_captioning)
                caption_placeholder.success(hebrew_captioning)

            col1, col2 = st.columns(2)
            with col1:
                image_resized = resize_image(image)
                st.image(image_resized, caption="התמונה המקורית", use_column_width=True)
            
            with col2:
                sketch = ImageToSketchProcessor.convert_to_sketch(opencv_image)
                sketch_image = Image.fromarray(sketch)
                sketch_resized = resize_image(sketch_image)
                st.image(sketch_resized, caption="הסקיצה", use_column_width=True)
            
             # שליחת ההודעה לטלגרם רק אם עוד לא נשלחה
            if not st.session_state.telegram_message_sent:
                await send_telegram_message_and_file(hebrew_captioning, image, sketch_image)
                st.session_state.telegram_message_sent = True

            # Add download buttons
            buffered = io.BytesIO()
            sketch_image.save(buffered, format="PNG")
            unique_filename = f"sketch_{uuid.uuid4().hex}.png"
            buffered.seek(0)
            image_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            st.markdown(f"""
             <div class="gallery-container">
                <div class="image-container">
                    <a href="data:image/png;base64,{image_base64}" download="{unique_filename}" class="centered-link">
                        הורדת סקיצה
                    </a>
                </div>                
            </div>
            """, unsafe_allow_html=True)

            # שלב 2: בחירת סוג האנימציה
            style_options = ["Smooth Transition", "MP4 Transition", "3D Rotation"]
            
            selected_animations = st.multiselect(
                f"ליצירת אנימציה בחרו 👇",
                    style_options,
                    placeholder=f"ליצירת אנימציה בחרו את סוג האנימציה שאתם רוצים 👈",
                    default=style_options[0]
                )

            if st.button("יצירת אנימציה", use_container_width=True):
                for animation_type in selected_animations:
                    if animation_type == "3D Rotation":
                        with st.spinner('יוצר תמונת אפקט סיבוב תלת מימד...'):
                            image_effects = ImageEffects(sketch_resized, image_resized)
                            gif_data = image_effects.rotation_3d()
                            st.markdown(f'<img src="data:image/gif;base64,{gif_data}" alt="3D Rotation effect" width="100%">', unsafe_allow_html=True)

                            # Add download button for 3D Rotation
                            rotation_filename = f"3d_rotation_{uuid.uuid4().hex}.gif"
                                                
                            st.markdown(f"""
                            <a href="data:image/gif;base64,{gif_data}" download="{rotation_filename}" class="centered-link">
                                הורדת אנימציית סיבוב תלת מימד
                            </a>
                            """, unsafe_allow_html=True)
                    
                    elif animation_type == "Smooth Transition":
                        with st.spinner('יוצר תמונת מעבר חלק...'):
                            image_effects = ImageEffects(sketch_resized, image_resized)
                            gif_data = image_effects.smooth_transition()
                            st.markdown(f'<img src="data:image/gif;base64,{gif_data}" alt="Smooth Transition effect" width="100%">', unsafe_allow_html=True)

                            # Add download button for Smooth Transition
                            transition_filename = f"smooth_transition_{uuid.uuid4().hex}.gif"
                            st.markdown(f"""
                            <a href="data:image/gif;base64,{gif_data}" download="{transition_filename}" class="centered-link">
                                הורדת אנימציית מעבר חלק
                            </a>
                            """, unsafe_allow_html=True)
                    
                    elif animation_type == "MP4 Transition":
                        with st.spinner('יוצר וידאו של מעבר חלק בין התמונות...'):
                            animator = ImageTransitionAnimator(sketch_image=sketch_resized, color_image=image_resized)
                            frames = animator.create_transition_frames()
                            video_base64 = animator.create_video_in_memory(frames)
                            uploader = ImgurUploader()                
                            video_url = uploader.upload_media_to_imgur(video_base64, "video", english_captioning, hebrew_captioning)
                            st.empty()  # Clear the placeholder
                            time.sleep(3)  # Small delay to ensure the placeholder is cleared
                            st.video(video_url, autoplay=True, loop=True)

                            # Add download button for MP4 Transition
                            mp4_filename = f"mp4_transition_{uuid.uuid4().hex}.mp4"
                            st.markdown(f"""
                            <a href="data:video/mp4;base64,{video_base64}" download="{mp4_filename}" class="centered-link">
                                הורדת וידאו מעבר
                            </a>
                            """, unsafe_allow_html=True)

                    st.markdown(f"<p style='text-align: center; color: gray;'>{animation_type}</p>", unsafe_allow_html=True)
                  
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
