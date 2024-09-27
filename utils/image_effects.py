import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw
import imageio
from io import BytesIO
import base64
import random

class ImageEffects:
    def __init__(self, sketch_image, color_image):
        self.sketch = sketch_image.convert('RGB')
        self.color = color_image.convert('RGB')
        self.size = (500, 500)  # Default size
        self.sketch = self.sketch.resize(self.size)
        self.color = self.color.resize(self.size)

    def _create_gif(self, frames, fps=30):
        output = BytesIO()
        imageio.mimsave(output, frames, format='GIF', fps=fps, loop=0)
        return base64.b64encode(output.getvalue()).decode('utf-8')

    def smooth_transition(self, num_frames=150):
        frames = []
        for i in range(num_frames):
            alpha = i / (num_frames - 1)
            blend = Image.blend(self.sketch, self.color, alpha)
            frames.append(np.array(blend))
        return self._create_gif(frames)

    def picture_in_picture(self, num_frames=150):
        frames = []
        for i in range(num_frames):
            base = self.color.copy()
            size = int(50 + i / num_frames * 400)
            small_sketch = self.sketch.resize((size, size))
            position = (self.size[0] - size - 10, self.size[1] - size - 10)
            base.paste(small_sketch, position)
            frames.append(np.array(base))
        return self._create_gif(frames)

    def ken_burns_effect(self, num_frames=150):
        frames = []
        for i in range(num_frames):
            scale = 1 + 0.3 * i / num_frames
            crop_size = int(self.size[0] / scale)
            offset_x = int((self.size[0] - crop_size) * (i / num_frames))
            offset_y = int((self.size[1] - crop_size) * (i / num_frames))
            zoomed = self.color.crop((offset_x, offset_y, offset_x + crop_size, offset_y + crop_size)).resize(self.size)
            frames.append(np.array(zoomed))
        return self._create_gif(frames)

    def parallax_effect(self, num_frames=150):
        # Simplified parallax effect
        background = self.color.copy()
        foreground = self.sketch.copy()
        frames = []
        for i in range(num_frames):
            offset = int(20 * np.sin(2 * np.pi * i / num_frames))
            frame = background.copy()
            frame.paste(foreground, (offset, 0), foreground.convert('RGBA'))
            frames.append(np.array(frame))
        return self._create_gif(frames)

    def glitch_effect(self, num_frames=150):
        frames = []
        for _ in range(num_frames):
            glitched = self.color.copy()
            if random.random() > 0.7:
                split = random.randint(0, self.size[0])
                left = glitched.crop((0, 0, split, self.size[1]))
                right = glitched.crop((split, 0, self.size[0], self.size[1]))
                glitched.paste(right, (0, 0))
                glitched.paste(left, (self.size[0] - split, 0))
            frames.append(np.array(glitched))
        return self._create_gif(frames)

    def rotation_3d(self, num_frames=150):
        # Simplified 3D rotation effect
        frames = []
        for i in range(num_frames):
            angle = 360 * i / num_frames
            if angle < 90 or angle >= 270:
                image = self.sketch
            else:
                image = self.color
            rotated = image.rotate(angle)
            size = int(self.size[0] * abs(np.cos(np.radians(angle))))
            rotated = rotated.resize((size, self.size[1]))
            frame = Image.new('RGB', self.size, (0, 0, 0))
            frame.paste(rotated, ((self.size[0] - size) // 2, 0))
            frames.append(np.array(frame))
        return self._create_gif(frames)

    def particles_transition(self, num_frames=150, num_particles=1000):
        particles = []
        for _ in range(num_particles):
            x = random.randint(0, self.size[0] - 1)
            y = random.randint(0, self.size[1] - 1)
            target_x = random.randint(0, self.size[0] - 1)
            target_y = random.randint(0, self.size[1] - 1)
            particles.append((x, y, target_x, target_y))

        frames = []
        for i in range(num_frames):
            frame = Image.new('RGB', self.size, (0, 0, 0))
            draw = ImageDraw.Draw(frame)
            for x, y, target_x, target_y in particles:
                current_x = int(x + (target_x - x) * i / num_frames)
                current_y = int(y + (target_y - y) * i / num_frames)
                color = self.color.getpixel((target_x, target_y))
                draw.point([current_x, current_y], fill=color)
            frames.append(np.array(frame))
        return self._create_gif(frames)