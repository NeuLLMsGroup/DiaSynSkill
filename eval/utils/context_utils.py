"""
Context Management Utilities

Handles conversation history management, token estimation, and
image-to-base64 conversion for multimodal API calls.

NOTE: Partial release. The complete implementation with dynamic context
truncation and adaptive image resizing is available upon acceptance.
"""

from PIL import Image
import math
import io
import base64
import re


def estimate_tokens(text):
    """
    Rough token count estimation for context window management.

    Uses a simple heuristic: token_count ≈ character_count / 4.
    This matches the approximate tokenization ratio for Chinese and
    English text in most subword tokenizers.
    """
    return len(text) // 4


def pil_to_base64_data_uri(pil_img, max_pixels=2000000, min_pixels=40000,
                           quality=85):
    """
    Convert a PIL Image to a base64 data URI for API transmission.

    Handles RGBA→RGB conversion (white background), resizes images
    exceeding max_pixels while preserving aspect ratio, and applies
    JPEG compression.

    Args:
        pil_img: PIL.Image object
        max_pixels: maximum pixel count before downscaling (default 2M)
        min_pixels: minimum pixel count threshold
        quality: JPEG compression quality 1-100 (default 85)

    Returns:
        str: "data:image/jpeg;base64,..."
    """
    # Handle RGBA images with white background compositing
    if pil_img.mode == 'RGBA':
        background = Image.new('RGBA', pil_img.size, (255, 255, 255, 255))
        pil_img = Image.alpha_composite(background, pil_img).convert('RGB')
    elif pil_img.mode != 'RGB':
        pil_img = pil_img.convert('RGB')

    # Resize if image exceeds max_pixels, preserving aspect ratio
    w, h = pil_img.size
    pixels = w * h
    if pixels > max_pixels:
        scale = math.sqrt(max_pixels / pixels)
        new_w, new_h = int(w * scale), int(h * scale)
        pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)

    # Encode as JPEG
    buffered = io.BytesIO()
    pil_img.save(buffered, format="JPEG", quality=quality)
    b64_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return f"data:image/jpeg;base64,{b64_str}"


def process_image(image_path, max_pixels=2000000, min_pixels=40000):
    """
    Load an image from disk and convert to base64 data URI.

    Wraps PIL.Image.open + pil_to_base64_data_uri with error handling.
    """
    try:
        img = Image.open(image_path)
        return pil_to_base64_data_uri(img, max_pixels, min_pixels)
    except Exception as e:
        print(f"Warning: Failed to process image {image_path}: {e}")
        return None
