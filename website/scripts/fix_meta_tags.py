import os
import glob
import re

website_dir = '/home/antigravity/Projects/Better Call Wes/Website'
html_files = glob.glob(os.path.join(website_dir, '**/*.html'), recursive=True)

def format_name(filename):
    # Convert "boiler-repair" to "Boiler Repair"
    name = os.path.splitext(filename)[0]
    return ' '.join(word.capitalize() for word in name.split('-'))

updated_count = 0

for file_path in html_files:
    rel_path = os.path.relpath(file_path, website_dir)
    
    # Skip core pages which might have custom titles already, or handle them specifically
    if rel_path in ['index.html', 'about.html', 'contact.html', 'pricing.html', 'reviews.html', 'locations.html', 'services.html']:
        continue
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    filename = os.path.basename(file_path)
    
    # Generate unique SEO Title and Description based on folder structure
    if rel_path.startswith('locations/'):
        location_name = format_name(filename)
        new_title = f"Plumber in {location_name} | Heating Engineer | Better Call Wes"
        new_desc = f"Looking for a reliable local plumber and heating engineer in {location_name}? Better Call Wes provides trusted, Gas Safe registered plumbing services, boiler repairs, and installations in the {location_name} area."
    elif rel_path.startswith('services/'):
        service_name = format_name(filename)
        new_title = f"{service_name} Services in Southampton | Better Call Wes"
        new_desc = f"Professional {service_name.lower()} in Southampton and surrounding areas. Better Call Wes offers honest, reliable, and Gas Safe registered heating and plumbing services with transparent pricing."
    else:
        continue # Skip other random files
        
    # Replace <title>
    title_pattern = r'<title>.*?</title>'
    if re.search(title_pattern, content, re.IGNORECASE | re.DOTALL):
        content = re.sub(title_pattern, f"<title>{new_title}</title>", content, flags=re.IGNORECASE | re.DOTALL)
    else:
        # If no title tag exists, add one below head
        content = re.sub(r'<head>', f"<head>\n    <title>{new_title}</title>", content, flags=re.IGNORECASE)
        
    # Replace <meta name="description">
    desc_pattern = r'<meta\s+name="description"\s+content="[^"]*"\s*/?>|<meta\s+content="[^"]*"\s+name="description"\s*/?>'
    
    new_meta_tag = f'<meta name="description" content="{new_desc}">'
    
    if re.search(desc_pattern, content, re.IGNORECASE):
        content = re.sub(desc_pattern, new_meta_tag, content, flags=re.IGNORECASE)
    else:
        # If no meta desc exists, insert below <title>
        content = re.sub(r'(<title>.*?</title>)', rf'\1\n    {new_meta_tag}', content, flags=re.IGNORECASE | re.DOTALL)
        
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    updated_count += 1

print(f"Successfully updated unique SEO Meta Tags for {updated_count} location and service pages.")
