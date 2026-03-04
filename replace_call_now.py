import os
import glob
import re

def replace_buttons(dir_path):
    count = 0
    for filepath in glob.glob(os.path.join(dir_path, '**/*.html'), recursive=True):
        with open(filepath, 'r') as f:
            content = f.read()
        
        original = content
        
        # 1. Replace floating CTA button (at bottom of every page)
        # Pattern: <a href="tel:07700155655" class="floating-cta">
        #              <i data-lucide="phone"></i> Call Now
        #          </a>
        content = re.sub(
            r'<a href="tel:07700155655" class="floating-cta">\s*<i data-lucide="phone"></i> Call Now\s*</a>',
            '<a href="https://wa.me/447700155655" class="floating-cta"><i data-lucide="message-circle"></i> WhatsApp</a>',
            content, flags=re.DOTALL
        )

        # 2. Replace CTA section buttons that link to tel: with phone icon and "Call Now"
        # Pattern: <a href="tel:07700155655" class="btn ..."><i data-lucide="phone"></i> Call Now</a>
        content = re.sub(
            r'<a\s+href="tel:07700155655"\s+class="btn[^"]*"[^>]*>\s*<i data-lucide="phone"[^>]*></i>\s*Call Now\s*</a>',
            '<a href="https://wa.me/447700155655" class="btn btn-whatsapp" target="_blank"><i data-lucide="message-circle"></i> WhatsApp Me</a>',
            content, flags=re.DOTALL
        )

        # 3. Replace hero "Call Now" on index.html (inline style ghost button)
        # Pattern: <a href="tel:07700155655" class="btn btn-outline" style="..."> ... Call Now </a>
        content = re.sub(
            r'<a href="tel:07700155655" class="btn btn-outline"\s+style="[^"]*">\s*<i data-lucide="message-circle" size="18"></i> Call Now\s*</a>',
            '<a href="https://wa.me/447700155655" class="btn btn-whatsapp" target="_blank"><i data-lucide="message-circle" size="18"></i> WhatsApp Me</a>',
            content, flags=re.DOTALL
        )

        if content != original:
            with open(filepath, 'w') as f:
                f.write(content)
            count += 1
            print(f"Updated: {os.path.relpath(filepath, dir_path)}")
    
    print(f"\nTotal files updated: {count}")

replace_buttons('/home/antigravity/Projects/Better Call Wes/Website')
