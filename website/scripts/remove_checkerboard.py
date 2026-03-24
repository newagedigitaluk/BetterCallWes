from PIL import Image

def remove_checkerboard(img_path, output_path):
    print("Loading image...")
    # Load image and ensure it's in RGBA mode
    img = Image.open(img_path).convert("RGBA")
    pixels = img.load()
    width, height = img.size

    # Define the exact colors of the checkerboard pattern (light grey and white)
    color1 = (204, 204, 204)  # rgb(204, 204, 204)
    color2 = (255, 255, 255)  # rgb(255, 255, 255)
    
    tolerance = 15  # Tolerance for slight anti-aliasing artifacts

    def color_match(p, target):
        return abs(p[0] - target[0]) < tolerance and abs(p[1] - target[1]) < tolerance and abs(p[2] - target[2]) < tolerance

    print("Processing pixels...")
    # Iterate through every pixel
    for y in range(height):
        for x in range(width):
            current_pixel = pixels[x, y]
            
            # If the pixel has some transparency already, skip it
            if current_pixel[3] < 255:
                continue

            # Check if it matches either of the checkerboard colors
            if color_match(current_pixel, color1) or color_match(current_pixel, color2):
                pixels[x, y] = (0, 0, 0, 0) # Make completely transparent

    print(f"Saving cleaned image to {output_path}...")
    img.save(output_path, "PNG")
    print("Done!")

import sys
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <input.png> <output.png>")
    else:
        remove_checkerboard(sys.argv[1], sys.argv[2])
