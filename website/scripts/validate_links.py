import os
import re
from urllib.parse import urlparse

website_dir = "/home/antigravity/Projects/Better Call Wes/Website"

html_files = []
for root, dirs, files in os.walk(website_dir):
    for file in files:
        if file.endswith(".html"):
            html_files.append(os.path.join(root, file))

valid_paths = set()
for file_path in html_files:
    rel_path = os.path.relpath(file_path, website_dir)
    valid_paths.add(rel_path.replace("\\", "/"))
    # Also add the directory if the file is index.html
    if file_path.endswith("index.html"):
        valid_paths.add(os.path.dirname(rel_path).replace("\\", "/"))

errors = []

for file_path in html_files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Simple regex to find hrefs
    links = re.findall(r'href=["\'](.*?)["\']', content)
    
    for link in links:
        # Ignore external links, mailto, tel, anchors
        if link.startswith("http") or link.startswith("mailto:") or link.startswith("tel:") or link.startswith("#") or link.startswith("https://wa.me"):
            continue
            
        # Ignore CSS/JS/Image links
        if link.endswith(".css") or link.endswith(".png") or link.endswith(".jpg") or link.endswith(".svg"):
            continue

        # Clean the link
        clean_link = link.split('#')[0].strip()
        if not clean_link:
            continue

        # Resolve relative path using os.path.abspath logic manually
        # Since it's a simple flat-ish structure we can do it textually
        base_dir = os.path.dirname(file_path)
        resolved_path = os.path.normpath(os.path.join(base_dir, clean_link))
        
        # Convert to relpath from website_dir
        try:
            rel_resolved = os.path.relpath(resolved_path, website_dir).replace("\\", "/")
            if rel_resolved not in valid_paths and rel_resolved + "/index.html" not in valid_paths and clean_link != "/":
                # Special case: "/" link resolves to index.html
                if not (clean_link == "/" and "index.html" in valid_paths):
                    errors.append(f"Broken link: '{link}' found in {os.path.basename(file_path)}")
        except ValueError:
            pass

if errors:
    print("Found broken links:")
    for e in errors:
        print(" - " + e)
else:
    print("All internal links validated successfully. No broken links found.")
