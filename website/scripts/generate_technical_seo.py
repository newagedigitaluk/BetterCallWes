import os
import glob
from datetime import datetime

website_dir = '/home/antigravity/Projects/Better Call Wes/Website'
base_url = 'https://bettercallwes.co.uk'
html_files = glob.glob(os.path.join(website_dir, '**/*.html'), recursive=True)

sitemap_urls = []
updated_files_count = 0

for file_path in html_files:
    # Compute relative path
    rel_path = os.path.relpath(file_path, website_dir)
    
    # Normalize paths for Windows/Linux
    rel_path = rel_path.replace('\\', '/')
    
    # Calculate canonical URL
    if rel_path == 'index.html':
        canonical_url = f"{base_url}/"
    else:
        canonical_url = f"{base_url}/{rel_path}"
        
    sitemap_urls.append(canonical_url)
    
    # Inject canonical tag into the HTML file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        # Check if canonical tag already exists to avoid duplicates
        canonical_tag = f'<link rel="canonical" href="{canonical_url}" />'
        
        if '<link rel="canonical"' not in content:
            # Insert right before </head>
            content = content.replace('</head>', f'    {canonical_tag}\n</head>')
            
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            updated_files_count += 1
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

# Generate sitemap.xml
current_date = datetime.now().strftime('%Y-%m-%d')
sitemap_content = ['<?xml version="1.0" encoding="UTF-8"?>']
sitemap_content.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

for url in sorted(sitemap_urls):
    priority = '1.0' if url == f"{base_url}/" else '0.8'
    sitemap_content.append('  <url>')
    sitemap_content.append(f'    <loc>{url}</loc>')
    sitemap_content.append(f'    <lastmod>{current_date}</lastmod>')
    sitemap_content.append(f'    <changefreq>monthly</changefreq>')
    sitemap_content.append(f'    <priority>{priority}</priority>')
    sitemap_content.append('  </url>')

sitemap_content.append('</urlset>')

with open(os.path.join(website_dir, 'sitemap.xml'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(sitemap_content))

# Generate robots.txt
robots_txt_content = f"""User-agent: *
Allow: /

Sitemap: {base_url}/sitemap.xml
"""

with open(os.path.join(website_dir, 'robots.txt'), 'w', encoding='utf-8') as f:
    f.write(robots_txt_content)

print(f"Technical SEO Implementation Complete.")
print(f"Generated sitemap.xml with {len(sitemap_urls)} URLs.")
print(f"Generated robots.txt.")
print(f"Injected canonical tags into {updated_files_count} HTML files.")
