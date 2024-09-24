import cv2
import numpy as np
import os

class ImageToSketchProcessor:
    @staticmethod
    def convert_to_sketch(image):
        """
        Convert an image to a sketch-like representation.
        
        :param image: str or numpy.ndarray, path to the input image file or OpenCV image
        :return: numpy array, the sketch image
        """
        try:
            if isinstance(image, str):
                # Read the image if a file path is provided
                img = cv2.imread(image)
                if img is None:
                    raise ValueError(f"Unable to read image at {image}")
            elif isinstance(image, np.ndarray):
                # Use the provided OpenCV image
                img = image.copy()  # Create a copy to avoid modifying the original
            else:
                raise ValueError("Input must be either a file path or an OpenCV image")
            
            # Check if the image is empty
            if img.size == 0:
                raise ValueError("The input image is empty")
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Invert the grayscale image
            inverted = 255 - gray
            
            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(inverted, (21, 21), 0)
            
            # Invert the blurred image
            inverted_blurred = 255 - blurred
            
            # Create the pencil sketch image
            sketch = cv2.divide(gray, inverted_blurred, scale=256.0)
            
            return sketch
        except Exception as e:
            raise ValueError(f"Error processing image: {str(e)}")

    @staticmethod
    def process_folder(input_folder, output_folder=None):
        """
        Process all images in a folder and save the sketch versions.
        
        :param input_folder: str, path to the folder containing input images
        :param output_folder: str, path to save the sketch images (default is a 'sketches' subfolder)
        :return: list of paths to the created sketch images
        """
        if output_folder is None:
            output_folder = os.path.join(input_folder, "sketches")
        
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        image_files = [f for f in os.listdir(input_folder) 
                       if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
        
        output_paths = []
        
        for image_file in image_files:
            input_path = os.path.join(input_folder, image_file)
            output_path = os.path.join(output_folder, f"sketch_{image_file}")
            
            sketch = ImageToSketchProcessor.convert_to_sketch(input_path)
            cv2.imwrite(output_path, sketch)
            
            output_paths.append(output_path)
        
        return output_paths

# Example usage
if __name__ == "__main__":
    # This section is for testing purposes and won't be used by the Streamlit app
    input_image = "uploads/pool_gallery4.jpeg"
    sketch = ImageToSketchProcessor.convert_to_sketch(input_image)
    cv2.imwrite("sketch_output.jpg", sketch)
    print(f"Sketch saved as sketch_output.jpg")