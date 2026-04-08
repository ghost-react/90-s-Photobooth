import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
import datetime
import os
import base64
import io

def add_noise(image_np, amount=0.04):
    """Add slight poisson/gaussian noise to simulate film grain."""
    row, col, ch = image_np.shape
    noise = np.random.randn(row, col, ch) * 255 * amount
    noisy = image_np + noise
    noisy = np.clip(noisy, 0, 255).astype(np.uint8)
    return noisy

def apply_vintage_filter(image_np):
    """Apply a 90s vintage film filter (high contrast, chemical fade)."""
    img = Image.fromarray(image_np)
    
    # Increase contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.3)
    
    # Increase color saturation
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.2)
    
    img_np = np.array(img, dtype=np.float32)
    # Golden Hour Vintage wash matrix (strong gold/yellow warmth, reduced blues)
    transform = np.array([
        [1.15, 0.15, 0.0 ],  # Push red channel heavily with green bleed (yellow/gold)
        [0.05, 1.10, 0.0 ],  # Push green channel up slightly
        [0.0 , 0.0 , 0.85]   # Drop blue to remove cold tones
    ])
    
    tinted = cv2.transform(img_np, transform)
    tinted = np.clip(tinted, 0, 255).astype(np.uint8)
    
    # Add heavy grain
    tinted = add_noise(tinted, amount=0.15)
    return Image.fromarray(tinted)

def crop_to_portrait(image_np):
    """Crops a horizontal frame to a wider 1:1 Square portrait."""
    h, w, c = image_np.shape
    target_width = h # Change aspect from 3:4 to 1:1 to widen strip
    if w > target_width:
        start_x = (w - target_width) // 2
        return image_np[:, start_x:start_x+target_width]
    return image_np

def decode_base64_image(b64_string):
    """Decodes a data URL base64 string to a cv2/numpy RGB array."""
    # Split "data:image/png;base64,iVBORw0..."
    header, encoded = b64_string.split(",", 1)
    # Decode
    data = base64.b64decode(encoded)
    # Convert string data to numpy array for cv2
    nparr = np.frombuffer(data, np.uint8)
    # Decode image to RGB (OpenCV normally loads BGR, so we force RGB here)
    img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    return img_rgb

def process_base64_frames(b64_frames, layout="vertical", mode="standard", prev_strip_b64=None):
    """
    Takes 3 base64 encoded frames from the frontend, processes them,
    and returns a base64 encoded finished strip.
    """
    frames_rgb = [decode_base64_image(f) for f in b64_frames]
    
    processed_images = []
    for frame in frames_rgb:
        cropped = crop_to_portrait(frame)
        vintage = apply_vintage_filter(cropped)
        processed_images.append(vintage)
    
    if not processed_images:
        return None

    # Determine sizes
    img_w, img_h = processed_images[0].size
    gap = 20
    border_side = 80
    border_top = 50
    border_bottom = 150
    
    # Calculate strip dimensions
    if layout == "horizontal":
        strip_w = (img_w * 3) + (gap * 2) + (border_side * 2)
        strip_h = img_h + border_top + border_bottom
    else:
        strip_w = img_w + (border_side * 2)
        strip_h = (img_h * 3) + (gap * 2) + border_top + border_bottom
    
    # Create white canvas
    strip = Image.new('RGB', (strip_w, strip_h), color='#E8E8E1')
    
    # Paste images
    current_x = border_side
    current_y = border_top
    for img in processed_images:
        strip.paste(img, (current_x, current_y))
        if layout == "horizontal":
            current_x += img_w + gap
        else:
            current_y += img_h + gap
        
    # Add digital orange date (without time)
    draw = ImageDraw.Draw(strip)
    timestamp = datetime.datetime.now().strftime("%Y %b %d")
    
    font_path = os.path.join("assets", "Digital-7.ttf")
    try:
        font = ImageFont.truetype(font_path, 40)
    except IOError:
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except IOError:
            font = ImageFont.load_default()
            
    text_bbox = draw.textbbox((0, 0), timestamp, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]
    
    x = strip_w - border_side - text_w
    y = strip_h - border_bottom + 50
    
    draw.text((x+2, y+2), timestamp, font=font, fill=(50, 20, 0)) # Shadow
    draw.text((x, y), timestamp, font=font, fill='#FF6600') # Orange Target
    
    # Advanced Modes handling
    if mode == "twin":
        twin_w = (strip.width * 2) + 20
        twin_strip = Image.new('RGB', (twin_w, strip.height), color='#E8E8E1')
        twin_strip.paste(strip, (0, 0))
        twin_strip.paste(strip, (strip.width + 20, 0))
        
        # Add a faint cut line
        draw_twin = ImageDraw.Draw(twin_strip)
        draw_twin.line([(strip.width + 10, 0), (strip.width + 10, strip.height)], fill="#AAA", width=2)
        strip = twin_strip
        
    elif mode == "combine" and prev_strip_b64:
        prev_np = decode_base64_image(prev_strip_b64)
        prev_img = Image.fromarray(prev_np)
        
        comb_w = prev_img.width + strip.width + 40
        comb_h = max(prev_img.height, strip.height)
        comb_strip = Image.new('RGB', (comb_w, comb_h), color='#E8E8E1')
        comb_strip.paste(prev_img, (0, 0))
        comb_strip.paste(strip, (prev_img.width + 40, 0))
        strip = comb_strip
        
    elif mode == "ghost" and prev_strip_b64:
        prev_np = decode_base64_image(prev_strip_b64)
        prev_img = Image.fromarray(prev_np)
        
        # Resize previous to match new perfectly
        prev_img = prev_img.resize(strip.size, Image.LANCZOS)
        strip = Image.blend(prev_img, strip, alpha=0.55) # Blend them!
    
    # Encode final strip back to base64
    buffered = io.BytesIO()
    strip.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    return f"data:image/png;base64,{img_str}"
