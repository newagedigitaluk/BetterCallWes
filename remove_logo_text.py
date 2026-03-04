import os
import glob
import re

def remove_text(directory):
    count = 0
    pattern = re.compile(r'(<img[^>]*src="[^"]*logo\.png"[^>]*>)\s*Better Call Wes')
    for filepath in glob.glob(os.path.join(directory, '**/*.html'), recursive=True):
        with open(filepath, 'r') as file:
            s = file.read()
        
        new_s = pattern.sub(r'\1', s)
        if new_s != s:
            with open(filepath, 'w') as file:
                file.write(new_s)
            print(f"Updated {filepath}")
            count += 1
            
    print(f"Total files updated: {count}")

remove_text('/home/antigravity/Projects/Better Call Wes/Website')
