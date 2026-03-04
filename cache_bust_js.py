import re, os, glob

def update_html(dir_path):
    count = 0
    for filepath in glob.glob(os.path.join(dir_path, '**/*.html'), recursive=True):
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Cache bust js/main.js
        new_content = re.sub(r'src="js/main\.js"', r'src="js/main.js?v=1.1"', content)
        new_content = re.sub(r'src="\.\./js/main\.js"', r'src="../js/main.js?v=1.1"', new_content)
        
        # Cache bust styles.css (handles both "css/styles.css?v=1.2" and "../css/styles.css?v=1.2")
        new_content = re.sub(r'css/styles\.css\?v=1\.2"', r'css/styles.css?v=1.3"', new_content)
        
        if new_content != content:
            with open(filepath, 'w') as f:
                f.write(new_content)
            count += 1
            print(f"Updated {filepath}")
            
    print(f"Total HTML files updated: {count}")

update_html('/home/antigravity/Projects/Better Call Wes/Website')
