"""Utility functions for CAPTCHA"""
from PIL import Image, ImageDraw, ImageFont
import random
import string
import io

from flask import send_file


def generate_captcha_image(text=None, width=200, height=70):
    """Generate CAPTCHA image"""
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a font, fallback to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    # Add random background lines
    for _ in range(3):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill='gray', width=2)
    
    # Add text with random positioning
    if not text:
        text = ''.join(random.choices(string.ascii_lowercase + string.ascii_uppercase + string.digits, k=6))
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    draw.text((x, y), text, fill='black', font=font)
    
    # Add noise dots
    for _ in range(30):
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), fill='gray')
    
    # return as png image
    img_io = io.BytesIO()
    img.save(img_io, format='PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png')


def verify_captcha(captcha_text, user_input):
    """Verify CAPTCHA"""
    return captcha_text.upper() == user_input.upper()
