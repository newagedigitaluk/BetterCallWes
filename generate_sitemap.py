import os
import glob
from datetime import datetime

website_dir = '/home/antigravity/Projects/Better Call Wes/Website'
base_url = 'https://bettercallwes.co.uk'
sitemap_path = os.path.join(website_dir, 'sitemap.xml')
robots_path = os.path.join(website_dir, 'robots.txt')

# Find all HTML files
html_files = glob.glob(os.path.join(website_dir, '**/*.html'), recursive=True)

# Generate Sitemap content
sitemap_content = ['<?xml version="1.0" encoding="UTF-8"?>']
sitemap_content.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

today = datetime.now().strftime('%Y-%m-%d')

for file_path in sorted(html_files):
    # Get the relative path from the website root
    rel_path = os.path.relpath(file_path, website_dir)
    
    # Skip any 404 pages or similar
    if '404' in rel_path.lower():
        continue
        
    # Convert file paths to URLs
    url_path = rel_path.replace(os.sep, '/')
    if url_path == 'index.html':
        url_path = ''  # Root URL
        priority = '1.0'
    elif url_path.startswith('services/'):
        priority = '0.8'
    elif url_path.startswith('locations/'):
        priority = '0.6'
    else:
        priority = '0.9'
        
    full_url = f"{base_url}/{url_path}"
    
    sitemap_content.append('  <url>')
    sitemap_content.append(f'    <loc>{full_url}</loc>')
    sitemap_content.append(f'    <lastmod>{today}</lastmod>')
    sitemap_content.append(f'    <changefreq>weekly</changefreq>')
    sitemap_content.append(f'    <priority>{priority}</priority>')
    sitemap_content.append('  </url>')

sitemap_content.append('</urlset>')

# Write Sitemap
with open(sitemap_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(sitemap_content))

# Generate Robots.txt
robots_content = f"""User-agent: *
Allow: /

Sitemap: {base_url}/sitemap.xml
"""

with open(robots_path, 'w', encoding='utf-8') as f:
    f.write(robots_content)

print(f"Generated sitemap.xml with {len(html_files)} URLs")
print("Generated robots.txt")
