import os
import glob

def add_favicon_to_html(dir_path):
    count = 0
    for filepath in glob.glob(os.path.join(dir_path, '**/*.html'), recursive=True):
        with open(filepath, 'r') as f:
            content = f.read()
            
        # Check if favicon is already added to avoid duplicates
        if 'favicon.ico' in content or 'favicon.png' in content:
            continue
            
        # Determine relative path base by checking depth relative to dir_path
        rel_path = os.path.relpath(filepath, dir_path)
        depth = rel_path.count(os.sep)
        prefix = '../' * depth
        
        favicon_tags = f"""    <link rel="icon" href="{prefix}assets/favicon.ico" sizes="any">
    <link rel="apple-touch-icon" href="{prefix}assets/favicon.png">
</head>"""

        new_content = content.replace('</head>', favicon_tags)
        
        if new_content != content:
            with open(filepath, 'w') as f:
                f.write(new_content)
            count += 1
            print(f"Updated {filepath}")
            
    print(f"Total HTML files updated with favicon: {count}")

add_favicon_to_html('/home/antigravity/Projects/Better Call Wes/Website')
