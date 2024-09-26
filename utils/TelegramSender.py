import os
from dotenv import load_dotenv
import asyncio
import aiohttp
from typing import Optional
from io import BytesIO
from PIL import Image

# Load environment variables from .env file
load_dotenv()

class TelegramSender:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not self.bot_token or not self.chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in environment variables")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.session = None

    async def ensure_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def close_session(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def _make_request(self, method: str, endpoint: str, **kwargs):
        await self.ensure_session()
        url = f"{self.base_url}/{endpoint}"
        async with getattr(self.session, method)(url, **kwargs) as response:
            if response.status != 200:
                print(f"Failed to {endpoint}. Status: {response.status}")
                print(f"Response: {await response.text()}")
                return None
            return await response.json()

    async def verify_bot_token(self):
        result = await self._make_request('get', 'getMe')
        if result:
            return True
        return False

    async def send_message(self, message: str) -> None:
        data = aiohttp.FormData()
        data.add_field("chat_id", self.chat_id)
        data.add_field("text", message)

        # Send the message
        result = await self._make_request('post', 'sendMessage', data=data)
        if result:
            print("Message sent successfully")

    async def send_video(self, video_buffer: BytesIO, caption: Optional[str] = None) -> None:
        data_video = aiohttp.FormData()

        # Add video file
        data_video.add_field("chat_id", self.chat_id)
        data_video.add_field("video", video_buffer, filename="animation.mp4", content_type="video/mp4")
        if caption:
            data_video.add_field("caption", caption)

        # Send video
        result_video = await self._make_request('post', 'sendVideo', data=data_video)
        if result_video:
            print("Video sent successfully")

    async def sketch_image(self, original_image: Image.Image, sketch_image: Image.Image, caption: Optional[str] = None) -> None:
        # Create a new image with both original and sketch side by side
        total_width = original_image.width + sketch_image.width
        max_height = max(original_image.height, sketch_image.height)
        combined_image = Image.new('RGB', (total_width, max_height))
        
        # Paste the original image on the left
        combined_image.paste(original_image, (0, 0))
        
        # Paste the sketch image on the right
        combined_image.paste(sketch_image, (original_image.width, 0))
        
        # Save the combined image to a BytesIO object
        img_byte_arr = BytesIO()
        combined_image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        # Send the combined image
        data = aiohttp.FormData()
        data.add_field("chat_id", self.chat_id)
        data.add_field("photo", img_byte_arr, filename="combined_image.png", content_type="image/png")
        if caption:
            data.add_field("caption", caption)

        data.add_field("link", "https://i.imgur.com/6vGORzZ.mp4")
        result = await self._make_request('post', 'sendPhoto', data=data)
        if result:
            print("Combined image sent successfully")

    async def send_video(self, video_buffer: BytesIO, caption: Optional[str] = None) -> None:
        data_video = aiohttp.FormData()

        # Add video file
        data_video.add_field("chat_id", self.chat_id)
        data_video.add_field("video", video_buffer, filename="animation.mp4", content_type="video/mp4")
        if caption:
            data_video.add_field("caption", caption)

        # Send video
        result_video = await self._make_request('post', 'sendVideo', data=data_video)
        if result_video:
            print("Video sent successfully")

# Example usage
async def main():
    sender = TelegramSender()
    try:
        if await sender.verify_bot_token():
            await sender.send_message("Test message", "LinguKid")
        else:
            print("Bot token verification failed")
    finally:
        await sender.close_session()

if __name__ == "__main__":
    asyncio.run(main())
