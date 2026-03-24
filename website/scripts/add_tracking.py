import os
import glob
import re

website_dir = '/home/antigravity/Projects/Better Call Wes/Website'
html_files = glob.glob(os.path.join(website_dir, '**/*.html'), recursive=True)

tracking_script = '''<script
  src="https://i.bettercallwes.co.uk/js/external-tracking.js"
  data-tracking-id="tk_7328a539b1e343b8a44f6f9bf8537fd6"
></script>
</body>'''

updated_count = 0

for file_path in html_files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'external-tracking.js' not in content:
        new_content = re.sub(r'</body>', tracking_script, content, flags=re.IGNORECASE)
        
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            updated_count += 1

print(f'Successfully added tracking script to {updated_count} HTML files.')
