import base64
import io
import os
import cv2
import tempfile

import numpy as np
from PIL import Image

class ImageTransitionAnimator:
    def __init__(self, sketch_image, color_image, duration=5, fps=30):
        self.sketch_image = self.prepare_image(sketch_image)
        self.color_image = self.prepare_image(color_image)
        self.duration = duration
        self.fps = fps
        self.num_frames = int(self.duration * self.fps)

    def prepare_image(self, image):
        if isinstance(image, np.ndarray):
            return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        elif isinstance(image, Image.Image):
            return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        else:
            raise ValueError("Unsupported image type")

    def create_transition_frames(self):
        frames = []
        for i in range(self.num_frames):
            alpha = i / self.num_frames
            blend = cv2.addWeighted(self.sketch_image, 1 - alpha, self.color_image, alpha, 0)
            frames.append(blend)
        return frames

    def create_video_in_memory(self, frames):
        height, width, _ = frames[0].shape
        
        # Create a temporary file in memory
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmpfile:
            video_path = tmpfile.name  # Save the temp file path to access later
        
        # Now create the video using OpenCV's VideoWriter and save it to the temporary file
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(video_path, fourcc, self.fps, (width, height))

        for frame in frames:
            out.write(frame)
        
        # Ensure the VideoWriter is released properly
        out.release()

        # Read the video file from the temporary file into memory
        with open(video_path, 'rb') as f:
            video_bytes = f.read()
        
        # Convert the video bytes to Base64
        video_base64 = base64.b64encode(video_bytes).decode('utf-8')

        # Clean up the temporary file
        os.remove(video_path)

        return video_base64

# Example usage
if __name__ == '__main__':
    # Example usage with some test images (replace these with actual PIL Image objects)
    sketch_image = Image.open("sketch_image.jpg")
    color_image = Image.open("color_image.jpg")

    animator = ImageTransitionAnimator(sketch_image=sketch_image, color_image=color_image)
    frames = animator.create_transition_video()
    video_buffer = animator.create_video_from_frames(frames)

    print("Video created and loaded into memory successfully!")
