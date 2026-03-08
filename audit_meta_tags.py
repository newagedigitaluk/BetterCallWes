import os
import glob
from bs4 import BeautifulSoup
import json

website_dir = '/home/antigravity/Projects/Better Call Wes/Website'
html_files = glob.glob(os.path.join(website_dir, '**/*.html'), recursive=True)

audit_results = {
    "missing_title": [],
    "missing_description": [],
    "duplicate_titles": {},
    "duplicate_descriptions": {},
    "empty_or_short_titles": [],
    "empty_or_short_descriptions": [],
}

title_map = {}
desc_map = {}

for file_path in html_files:
    rel_path = os.path.relpath(file_path, website_dir)
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    title_tag = soup.find('title')
    desc_tag = soup.find('meta', attrs={'name': 'description'})
    
    # Check title
    if not title_tag or not title_tag.string:
        audit_results['missing_title'].append(rel_path)
    else:
        title_text = title_tag.string.strip()
        if len(title_text) < 10:
            audit_results['empty_or_short_titles'].append(f"{rel_path}: {title_text}")
        if title_text in title_map:
            title_map[title_text].append(rel_path)
        else:
            title_map[title_text] = [rel_path]
            
    # Check description
    if not desc_tag or not desc_tag.get('content'):
        audit_results['missing_description'].append(rel_path)
    else:
        desc_text = desc_tag.get('content').strip()
        if len(desc_text) < 30:
            audit_results['empty_or_short_descriptions'].append(f"{rel_path}: {desc_text}")
        if desc_text in desc_map:
            desc_map[desc_text].append(rel_path)
        else:
            desc_map[desc_text] = [rel_path]

# Find duplicates (more than 1 occurrence)
for title, paths in title_map.items():
    if len(paths) > 1:
        audit_results['duplicate_titles'][title] = paths

for desc, paths in desc_map.items():
    if len(paths) > 1:
        audit_results['duplicate_descriptions'][desc] = paths

print("Meta Tag Audit Results:")
print("-----------------------")
print(f"Missing Title: {len(audit_results['missing_title'])} pages")
print(f"Missing Description: {len(audit_results['missing_description'])} pages")
print(f"Duplicate Titles: {len(audit_results['duplicate_titles'])} unique titles reused")
print(f"Duplicate Descriptions: {len(audit_results['duplicate_descriptions'])} unique descriptions reused")
print(f"Empty or Short Titles: {len(audit_results['empty_or_short_titles'])} pages")
print(f"Empty or Short Descriptions: {len(audit_results['empty_or_short_descriptions'])} pages")

with open('/home/antigravity/Projects/Better Call Wes/seo_audit_results.json', 'w') as f:
    json.dump(audit_results, f, indent=4)
print("Detailed results saved to seo_audit_results.json")
