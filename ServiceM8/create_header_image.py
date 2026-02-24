
from PIL import Image, ImageDraw, ImageFont
import os

def create_header_image(logo_path, output_path):
    # Dimensions for a high-res header (width of A4 at 300dpi is ~2480px)
    # Let's make it 2400px wide x 600px tall
    W, H = 2400, 500
    
    # Colors
    NAVY = (15, 23, 42)    # #0F172A
    ORANGE = (255, 125, 0) # #FF7D00
    WHITE = (255, 255, 255)
    
    # 1. Create Base Image (Navy Background)
    img = Image.new('RGB', (W, H), color=NAVY)
    draw = ImageDraw.Draw(img)
    
    # 2. Add Logo (Left Side)
    if os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert("RGBA")
            # Resize logo to fit nicely (e.g. max height 350px)
            logo.thumbnail((800, 350), Image.Resampling.LANCZOS)
            
            # Position: Vertically centered, Left padding 100px
            logo_x = 100
            logo_y = (H - logo.size[1]) // 2
            
            # Paste logo using its alpha channel as mask
            img.paste(logo, (logo_x, logo_y), logo)
        except Exception as e:
            print(f"Error loading logo: {e}")
    else:
        print("Logo file not found!")
        
    # 3. Add Title Text (Right Side)
    # Since we can't easily rely on system fonts being perfect, we'll try a default or simple path
    # But for a script running on Mac, we can often find Arial or similar.
    
    try:
        # Try to load a bold font
        font_path = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
        if not os.path.exists(font_path):
            font_path = "/Library/Fonts/Arial Black.ttf"
        
        font = ImageFont.truetype(font_path, 100)
        
        text = "TAX INVOICE"
        
        # Calculate text size (bbox)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        
        # Position: Right padding 100px, top aligned relative to logo
        text_x = W - text_w - 100
        text_y = 150
        
        draw.text((text_x, text_y), text, font=font, fill=ORANGE)
        
        # Add "Job Ref" placeholder text below
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
        ref_text = "Ref No:"
        
        bbox_ref = draw.textbbox((0, 0), ref_text, font=font_small)
        ref_w = bbox_ref[2] - bbox_ref[0]
        
        draw.text((W - ref_w - 100, text_y + text_h + 20), ref_text, font=font_small, fill=WHITE)
        
    except Exception as e:
        print(f"Font error: {e}")
        # Fallback to simple rectangle if text fails?
        pass

    # Save
    img.save(output_path)
    print(f"Created header image: {output_path}")

if __name__ == "__main__":
    LOGO_PATH = "/Users/akweteybortier/Coding/Better Call Wes/Brand Images/a1781cea-8d5b-423d-bd16-14e4f373f63c.png"
    OUTPUT_PATH = "header_bg.png"
    create_header_image(LOGO_PATH, OUTPUT_PATH)
