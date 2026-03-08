import os
import glob

website_dir = '/home/antigravity/Projects/Better Call Wes/Website'
html_files = glob.glob(os.path.join(website_dir, 'services/*.html'))

fixed_count = 0

for file_path in html_files:
    basename = os.path.basename(file_path)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # We want to find cases where a page links to ITSELF in the service grid.
    # Ex: <a href="../services/boiler-repair.html" class="learn-more">Learn More
    target_string = f'<a href="../services/{basename}" class="learn-more">Learn More'
    replacement_string = f'<a href="../booking.html" class="learn-more">Book Now'
    
    if target_string in content:
        content = content.replace(target_string, replacement_string)
        
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Fixed self-referential links in: {basename}')
        fixed_count += 1

print(f'Successfully updated links in {fixed_count} service pages.')
