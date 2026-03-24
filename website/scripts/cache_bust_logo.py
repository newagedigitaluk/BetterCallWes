import os
import glob
import re

def cache_bust_logo(dir_path):
    count = 0
    for filepath in glob.glob(os.path.join(dir_path, '**/*.html'), recursive=True):
        with open(filepath, 'r') as f:
            content = f.read()
            
        # Update logo.png?v=2 to ?v=3
        new_content = re.sub(r'logo\.png\?v=2"', r'logo.png?v=3"', content)
        new_content = re.sub(r'logo\.png"', r'logo.png?v=3"', new_content)
        
        if new_content != content:
            with open(filepath, 'w') as f:
                f.write(new_content)
            count += 1
            print(f"Updated {filepath}")
            
    print(f"Total HTML files updated with logo cache bust: {count}")

cache_bust_logo('/home/antigravity/Projects/Better Call Wes/Website')
