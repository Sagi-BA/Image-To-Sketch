import os
import streamlit as st
import base64

def load_images_from_folder(folder_path):
    images = []
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            img_path = os.path.join(folder_path, filename)
            with open(img_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
            caption = os.path.splitext(filename)[0]  # Get filename without extension
            images.append({"src": f"data:image/png;base64,{encoded_string}", "alt": caption})
    return images

def display_image_slideshow(folder_path="examples"):
    images = load_images_from_folder(folder_path)
    if not images:
        st.warning("No images found in the specified folder.")
        return

    # HTML for the TikTok-style slideshow
    slideshow_html = f"""
    <link rel="stylesheet" href="https://unpkg.com/swiper/swiper-bundle.min.css">
    <script src="https://unpkg.com/swiper/swiper-bundle.min.js"></script>
    <style>
    .swiper-container {{
        width: 100%;
        height: 80vh;
        background-color: #000;
    }}
    .swiper-slide {{
        overflow: hidden;
        position: relative;
    }}
    .swiper-slide img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
    }}
    .image-caption {{
        position: absolute;
        bottom: 20px;
        left: 20px;
        color: white;
        font-size: 18px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }}
    .swiper-pagination-bullet {{
        width: 10px;
        height: 10px;
        background-color: #fff;
        opacity: 0.5;
    }}
    .swiper-pagination-bullet-active {{
        opacity: 1;
    }}
    .swiper-button-next, .swiper-button-prev {{
        color: #fff;
        opacity: 0.7;
        transition: opacity 0.3s;
    }}
    .swiper-button-next:hover, .swiper-button-prev:hover {{
        opacity: 1;
    }}
    </style>
    <div class="swiper-container">
        <div class="swiper-wrapper">
            {"".join(f'<div class="swiper-slide"><img src="{img["src"]}" alt="{img["alt"]}"><div class="image-caption">{img["alt"]}</div></div>' for img in images)}
        </div>
        <div class="swiper-pagination"></div>
        <div class="swiper-button-next"></div>
        <div class="swiper-button-prev"></div>
    </div>
    <script>
    var swiper = new Swiper('.swiper-container', {{
        direction: 'vertical',
        loop: true,
        autoplay: {{
            delay: 3000,
            disableOnInteraction: false,
        }},
        pagination: {{
            el: '.swiper-pagination',
            clickable: true,
        }},
        navigation: {{
            nextEl: '.swiper-button-next',
            prevEl: '.swiper-button-prev',
        }},
        effect: 'fade',
        fadeEffect: {{
            crossFade: true
        }},
    }});
    </script>
    """
    
    st.components.v1.html(slideshow_html, height=600)