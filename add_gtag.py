import os
import glob
import re

website_dir = '/home/antigravity/Projects/Better Call Wes/Website'
html_files = glob.glob(os.path.join(website_dir, '**/*.html'), recursive=True)

gtag_script = """<head>
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-GD5D6TC4DS"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());

      gtag('config', 'G-GD5D6TC4DS');
    </script>"""

updated_count = 0

for file_path in html_files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if script is already present
    if 'G-GD5D6TC4DS' not in content:
        # Replace the first <head> tag with <head> + gtag_script
        new_content = re.sub(r'<head>', gtag_script, content, count=1, flags=re.IGNORECASE)
        
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            updated_count += 1

print(f'Successfully added Google Tag (gtag.js) to {updated_count} HTML files.')
