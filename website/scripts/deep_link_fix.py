import os
import glob
import re

website_dir = '/home/antigravity/Projects/Better Call Wes/Website'
html_files = glob.glob(os.path.join(website_dir, '**/*.html'), recursive=True)

fixed_count = 0

for file_path in html_files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        # Determine depth to know how many ../ we need
        rel_path = os.path.relpath(file_path, website_dir)
        depth = rel_path.count(os.sep)
        
        prefix = '../' * depth if depth > 0 else ''
        
        if depth > 0:
            # Fix links that are missing the relative prefix or pointing back to the same folder incorrectly
            content = content.replace('href="index.html"', f'href="{prefix}index.html"')
            content = content.replace('href="about.html"', f'href="{prefix}about.html"')
            content = content.replace('href="pricing.html"', f'href="{prefix}pricing.html"')
            content = content.replace('href="reviews.html"', f'href="{prefix}reviews.html"')
            content = content.replace('href="contact.html"', f'href="{prefix}contact.html"')
            content = content.replace('href="services.html"', f'href="{prefix}services.html"')
            
            # Fix absolute paths that should be relative
            content = content.replace('href="/services/', f'href="{prefix}services/')
            
            # The dropdown "View All Services" link was broken as href="../.html"
            content = content.replace('href="../.html"', f'href="{prefix}services.html"')

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            fixed_count += 1
            
    except Exception as e:
        print(f'Error reading/writing {file_path}: {e}')

print(f'Aggressively fixed links in {fixed_count} files.')
