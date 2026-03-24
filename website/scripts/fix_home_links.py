import os
import glob
import re

def fix_links(directory, is_root):
    html_files = glob.glob(os.path.join(directory, "*.html"))
    for file in html_files:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()

        if is_root:
            new_content = re.sub(r'href="/"', r'href="index.html"', content)
        else:
            new_content = re.sub(r'href="/"', r'href="../index.html"', content)
            # Also fix href="../" just to be safe
            new_content = re.sub(r'href="\.\./"', r'href="../index.html"', new_content)

        if new_content != content:
            with open(file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Fixed {file}")

website_dir = "/home/antigravity/Projects/Better Call Wes/Website"
services_dir = os.path.join(website_dir, "services")

fix_links(website_dir, is_root=True)
fix_links(services_dir, is_root=False)
