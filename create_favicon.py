from PIL import Image

def create_favicon(input_path, output_dir):
    try:
        img = Image.open(input_path).convert("RGBA")
        
        # The cropped logo is 800w x 414h. The emblem is on the left.
        # So we crop a square from the left: (0, 0, height, height)
        size = img.height
        emblem = img.crop((0, 0, size, size))
        
        # Save as PNG
        png_path = f"{output_dir}/favicon.png"
        emblem.resize((512, 512), Image.Resampling.LANCZOS).save(png_path, "PNG")
        
        # Save as ICO (requires multiple sizes usually, but PIL can do it)
        ico_path = f"{output_dir}/favicon.ico"
        emblem.resize((256, 256), Image.Resampling.LANCZOS).save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64,64), (128,128), (256,256)])
        
        print(f"Favicon created successfully at {png_path} and {ico_path}")
        
    except Exception as e:
        print(f"Error: {e}")

source_img = "/home/antigravity/Projects/Better Call Wes/Website/assets/logo.png"
output_directory = "/home/antigravity/Projects/Better Call Wes/Website/assets"

create_favicon(source_img, output_directory)
