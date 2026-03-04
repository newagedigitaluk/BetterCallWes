from PIL import Image

def crop_transparent(input_path, output_path):
    try:
        img = Image.open(input_path).convert("RGBA")
        bbox = img.getbbox()
        if bbox:
            cropped = img.crop(bbox)
            cropped.save(output_path, "PNG")
            print(f"Successfully cropped and saved to {output_path}")
        else:
            print("Image is entirely empty/transparent.")
    except Exception as e:
        print(f"Error: {e}")

input_img = "/home/antigravity/Projects/Better Call Wes/Brand Images/logo-trans.png"
output_img = "/home/antigravity/Projects/Better Call Wes/Website/assets/logo.png"

crop_transparent(input_img, output_img)
