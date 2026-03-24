import os
import glob

def cache_bust_css(directory):
    count = 0
    for filepath in glob.glob(os.path.join(directory, '**/*.html'), recursive=True):
        with open(filepath, 'r') as file:
            s = file.read()
        
        # Replace href="css/styles.css" or href="../css/styles.css" with ?v=1.1
        if 'css/styles.css"' in s:
            new_s = s.replace('css/styles.css"', 'css/styles.css?v=1.1"')
            with open(filepath, 'w') as file:
                file.write(new_s)
            count += 1
            print(f"Updated {filepath}")
            
    print(f"Total files updated: {count}")

cache_bust_css('/home/antigravity/Projects/Better Call Wes/Website')
