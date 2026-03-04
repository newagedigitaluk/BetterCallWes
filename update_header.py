import re, os, glob

def update_html(dir_path):
    # Regex to capture the whole top bar
    top_bar_pattern = re.compile(r'<!-- Top Bar -->\s*<div class="top-bar">[\s\S]*?</div>\s*</div>\s*</div>', re.MULTILINE)
    
    # Adust header class
    header_pattern = re.compile(r'<header class="header has-topbar">')
    
    count = 0
    for filepath in glob.glob(os.path.join(dir_path, '**/*.html'), recursive=True):
        with open(filepath, 'r') as f:
            content = f.read()
        
        new_content = top_bar_pattern.sub('', content)
        new_content = header_pattern.sub('<header class="header">', new_content)
        
        # Cache bust styles.css (handles both "css/styles.css?v=1.1" and "../css/styles.css?v=1.1")
        new_content = re.sub(r'css/styles\.css\?v=1\.1"', r'css/styles.css?v=1.2"', new_content)
        new_content = re.sub(r'css/styles\.css"', r'css/styles.css?v=1.2"', new_content)
        
        if new_content != content:
            with open(filepath, 'w') as f:
                f.write(new_content)
            count += 1
            print(f"Updated {filepath}")
            
    print(f"Total HTML files updated: {count}")

update_html('/home/antigravity/Projects/Better Call Wes/Website')
