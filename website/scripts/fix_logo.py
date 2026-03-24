from PIL import Image
import os

src = '/home/antigravity/Projects/Better Call Wes/Brand Images/logo-trans.png'
dest = '/home/antigravity/Projects/Better Call Wes/Website/assets/logo.webp'

img = Image.open(src)
print(f'Source size: {img.size}, mode: {img.mode}')

# Resize to 800px wide max, keep RGBA for transparency
if img.width > 800:
    ratio = 800 / img.width
    img = img.resize((800, int(img.height * ratio)), Image.LANCZOS)

img.save(dest, 'WEBP', quality=90, method=6)
orig = os.path.getsize(src) // 1024
new = os.path.getsize(dest) // 1024
print(f'Done: {orig}KB → {new}KB')
