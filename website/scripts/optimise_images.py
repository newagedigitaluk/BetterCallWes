#!/usr/bin/env python3
"""
Image optimisation script for Better Call Wes website.
- Converts PNG/JPG images to WebP format
- Resizes over-sized images to sensible display dimensions
- Updates all HTML files to reference the new .webp files
- Keeps originals as backup with .bak extension
"""
import os
import glob
import re
import shutil
from PIL import Image

ASSETS_DIR = '/home/antigravity/Projects/Better Call Wes/Website/assets'
WEBSITE_DIR = '/home/antigravity/Projects/Better Call Wes/Website'

# Max dimensions for each image (width, height) — resize if larger
# Hero/fullscreen images: up to 1600px wide
# Logo: already well-sized, just compress
# Card/section images: 800px wide is plenty
IMAGE_SETTINGS = {
    'logo.png':                 {'max_w': 800,  'quality': 85, 'keep_original': True},
    'logo.jpg':                 {'max_w': 800,  'quality': 85, 'keep_original': True},
    'images/hero-wes.png':      {'max_w': 1600, 'quality': 82, 'keep_original': False},
    'images/van-work.png':      {'max_w': 1600, 'quality': 82, 'keep_original': False},
    'images/copper-pipework.png': {'max_w': 1600, 'quality': 82, 'keep_original': False},
    'images/southampton-cityscape.png': {'max_w': 1600, 'quality': 82, 'keep_original': False},
    'images/wes-profile.png':   {'max_w': 900,  'quality': 85, 'keep_original': False},
    'images/boiler-repair.png': {'max_w': 900,  'quality': 85, 'keep_original': False},
    'images/gas-safety.png':    {'max_w': 900,  'quality': 85, 'keep_original': False},
    'images/plumbing-repairs.png': {'max_w': 900, 'quality': 85, 'keep_original': False},
    'images/heating-radiator.png': {'max_w': 900, 'quality': 85, 'keep_original': False},
    'images/bathroom-shower.png': {'max_w': 900, 'quality': 85, 'keep_original': False},
    'images/plumber-tools.png': {'max_w': 900,  'quality': 85, 'keep_original': False},
}

converted = []
skipped = []

for rel_path, settings in IMAGE_SETTINGS.items():
    src = os.path.join(ASSETS_DIR, rel_path)
    if not os.path.exists(src):
        print(f'  SKIP (not found): {rel_path}')
        skipped.append(rel_path)
        continue

    base, ext = os.path.splitext(src)
    dest = base + '.webp'
    orig_size = os.path.getsize(src)

    try:
        img = Image.open(src)

        # Convert RGBA to RGB if saving as lossy WebP (optional, preserves transparency)
        # We keep RGBA for logo (transparency needed), convert others to RGB
        if img.mode == 'RGBA' and 'logo' not in rel_path:
            img = img.convert('RGB')
        elif img.mode not in ('RGB', 'RGBA', 'L'):
            img = img.convert('RGB')

        # Resize if over max width
        max_w = settings['max_w']
        if img.width > max_w:
            ratio = max_w / img.width
            new_h = int(img.height * ratio)
            img = img.resize((max_w, new_h), Image.LANCZOS)
            print(f'  Resized: {rel_path} → {max_w}x{new_h}')

        img.save(dest, 'WEBP', quality=settings['quality'], method=6)
        new_size = os.path.getsize(dest)
        saving = (1 - new_size / orig_size) * 100

        print(f'  ✓ {rel_path}')
        print(f'    {orig_size//1024}KB → {new_size//1024}KB  ({saving:.0f}% smaller)')
        converted.append((rel_path, dest, ext))

    except Exception as e:
        print(f'  ERROR: {rel_path}: {e}')
        skipped.append(rel_path)

print(f'\n--- Converted {len(converted)} images ---')

# Update all HTML files to reference .webp instead of .png/.jpg
print('\nUpdating HTML references...')
html_files = glob.glob(os.path.join(WEBSITE_DIR, '**/*.html'), recursive=True)
update_count = 0

for html_path in html_files:
    with open(html_path, 'r') as f:
        content = f.read()

    original = content

    # Replace image references: both direct and with query strings like ?v=3
    for rel_path, dest, old_ext in converted:
        # Get just the filename without extension
        basename = os.path.basename(rel_path)
        stem = os.path.splitext(basename)[0]

        # Replace .ext" with .webp" and .ext? with .webp?
        old_ext_esc = re.escape(old_ext)
        # Replace the file extension in src attributes
        content = re.sub(
            rf'({re.escape(stem)}){old_ext_esc}(\?[^"\'>\s]*)?(")',
            rf'\1.webp\2\3',
            content
        )
        # Also handle without query string
        content = re.sub(
            rf'({re.escape(stem)}){old_ext_esc}(")',
            rf'\1.webp\2',
            content
        )

    if content != original:
        with open(html_path, 'w') as f:
            f.write(content)
        update_count += 1
        print(f'  Updated: {os.path.relpath(html_path, WEBSITE_DIR)}')

print(f'\nUpdated {update_count} HTML files.')
print('\nDone! Check results above.')
