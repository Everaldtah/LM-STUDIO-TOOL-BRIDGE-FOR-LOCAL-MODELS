"""
Convert image to ASCII art - clean output for HTML embedding.
"""
from PIL import Image
import numpy as np
import sys

# Extended ASCII character set (dark to light)
ASCII_CHARS = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "

def resize_image(image, new_width=200):
    """Resize image maintaining aspect ratio."""
    original_width, original_height = image.size
    aspect_ratio = original_height / original_width
    new_height = int(new_width * aspect_ratio * 0.55)
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

def image_to_ascii_html(image_path, width=200):
    """Convert image to ASCII art with HTML span colors."""
    try:
        image = Image.open(image_path)
        image = resize_image(image, width)
        image_rgb = image.convert('RGB')
        pixels = np.array(image_rgb)

        # Calculate grayscale for character selection
        gray = np.dot(pixels[...,:3], [0.2989, 0.5870, 0.1140])

        # Build HTML output
        lines = []
        for y in range(gray.shape[0]):
            line_chars = []
            for x in range(gray.shape[1]):
                pixel_val = gray[y, x]
                r, g, b = pixels[y, x]

                # Map to character index
                index = int((pixel_val / 255) * (len(ASCII_CHARS) - 1))
                index = (len(ASCII_CHARS) - 1) - index
                char = ASCII_CHARS[index]

                # Create colored span
                if char != " ":
                    line_chars.append(f'<span style="color: rgb({r},{g},{b})">{char}</span>')
                else:
                    line_chars.append(' ')
            lines.append(''.join(line_chars))

        return '\n'.join(lines)
    except Exception as e:
        return f"Error: {e}"

def image_to_ascii_text(image_path, width=200):
    """Convert image to plain text ASCII art."""
    try:
        image = Image.open(image_path)
        image = resize_image(image, width)
        image = image.convert('L')
        pixels = np.array(image)

        lines = []
        for row in pixels:
            line = ""
            for pixel in row:
                index = int((pixel / 255) * (len(ASCII_CHARS) - 1))
                index = (len(ASCII_CHARS) - 1) - index
                line += ASCII_CHARS[index]
            lines.append(line)

        return '\n'.join(lines)
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    image_path = r"C:\Users\evera\Downloads\ChatGPT Image Mar 5, 2026, 09_13_26 PM.png"
    width = int(sys.argv[1]) if len(sys.argv) > 1 else 180
    output_type = sys.argv[2] if len(sys.argv) > 2 else "html"

    if output_type == "html":
        print(image_to_ascii_html(image_path, width))
    else:
        print(image_to_ascii_text(image_path, width))
