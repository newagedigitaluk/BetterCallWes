import os
import glob

def find_replace(directory, old, new):
    count = 0
    for filepath in glob.glob(os.path.join(directory, '**/*.html'), recursive=True):
        with open(filepath, 'r') as file:
            s = file.read()
        if old in s:
            s = s.replace(old, new)
            with open(filepath, 'w') as file:
                file.write(s)
            print(f"Updated {filepath}")
            count += 1
    print(f"Total files updated: {count}")

find_replace('/home/antigravity/Projects/Better Call Wes/Website', 'logo.jpg', 'logo.png')
