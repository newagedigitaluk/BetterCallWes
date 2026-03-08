import os
import glob
from bs4 import BeautifulSoup

website_dir = '/home/antigravity/Projects/Better Call Wes/Website'
html_files = glob.glob(os.path.join(website_dir, '**/*.html'), recursive=True)

fixed_count = 0

for file_path in html_files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        # The dropdown Home link is currently href="index.html" on pages inside /services/
        # It should be href="../index.html"
        if '/services/' in file_path:
            content = content.replace('<a href="index.html" class="nav-link">Home</a>', '<a href="../index.html" class="nav-link">Home</a>')
            content = content.replace('<a href="index.html">Home</a>', '<a href="../index.html">Home</a>') # Mobile nav
            content = content.replace('<li><a href="index.html">Home</a></li>', '<li><a href="../index.html">Home</a></li>') # Footer nav
            
            # The dropdown "View All Services" link is currently href="../.html" on some pages
            content = content.replace('href="../.html"', 'href="../services.html"')
            
        elif '/locations/' in file_path:
             # Just in case locations have similar issues, though they were generated after child pages so might be OK
             content = content.replace('href="../.html"', 'href="../services.html"')

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            fixed_count += 1
            
    except Exception as e:
        print(f'Error reading/writing {file_path}: {e}')

print(f'Fixed broken navigation links in {fixed_count} files.')
