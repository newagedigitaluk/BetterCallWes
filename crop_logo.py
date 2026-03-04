from PIL import Image, ImageChops
import os

def crop_bg(image_path, output_path, padding=0):
    img = Image.open(image_path).convert("RGB") # convert to RGB to ignore alpha differences
    
    # Get the top-left pixel color and create a background image of that color
    bg_color = img.getpixel((0, 0))
    bg = Image.new("RGB", img.size, bg_color)
    
    # Find the difference between the image and the background
    diff = ImageChops.difference(img, bg)
    
    # Convert diff to grayscale
    diff = diff.convert("L")
    
    # Threshold to remove slight noise (tolerance)
    diff = diff.point(lambda p: p > 10 and 255)
    
    bbox = diff.getbbox()
    
    if bbox:
        # Use the original RGBA image to crop so we keep alpha if any
        orig_img = Image.open(image_path).convert("RGBA")
        left = max(0, bbox[0] - padding)
        upper = max(0, bbox[1] - padding)
        right = min(img.width, bbox[2] + padding)
        lower = min(img.height, bbox[3] + padding)
        
        cropped = orig_img.crop((left, upper, right, lower))
        
        if cropped.width > 800:
            ratio = 800 / cropped.width
            new_h = int(cropped.height * ratio)
            cropped = cropped.resize((800, new_h), Image.Resampling.LANCZOS)
            
        cropped.save(output_path, "PNG")
        print(f"Cropped and resized image saved to {output_path} with size {cropped.size}")
    else:
        print("Could not find a bounding box.")

source = "/home/antigravity/Projects/Better Call Wes/Brand Images/hf_20260116_204855_b6a6e69a-83da-4f1e-982c-a5b85eb34817.png"
output_png = "/home/antigravity/Projects/Better Call Wes/Website/assets/logo.png"

crop_bg(source, output_png)
