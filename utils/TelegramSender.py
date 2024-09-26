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

    async def send_images(self, original_image: BytesIO, sketch_image: BytesIO, caption_original: Optional[str] = None, caption_sketch: Optional[str] = None) -> None:
        data_original = aiohttp.FormData()
        data_sketch = aiohttp.FormData()
        
        # Prepare original image
        data_original.add_field("chat_id", self.chat_id)
        data_original.add_field("photo", original_image, filename="original_image.png", content_type="image/png")
        if caption_original:
            data_original.add_field("caption", caption_original)

        # Send original image
        result_original = await self._make_request('post', 'sendPhoto', data=data_original)
        if result_original:
            print("Original image sent successfully")

        # Prepare sketch image
        data_sketch.add_field("chat_id", self.chat_id)
        data_sketch.add_field("photo", sketch_image, filename="sketch_image.png", content_type="image/png")
        if caption_sketch:
            data_sketch.add_field("caption", caption_sketch)

        # Send sketch image
        result_sketch = await self._make_request('post', 'sendPhoto', data=data_sketch)
        if result_sketch:
            print("Sketch image sent successfully")

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

        result = await self._make_request('post', 'sendPhoto', data=data)
        if result:
            print("Combined image sent successfully")


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
