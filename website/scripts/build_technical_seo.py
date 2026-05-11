import os
import re
import subprocess
from datetime import datetime, timezone

base_url = "https://bettercallwes.co.uk"
# Resolve website_dir relative to the repo root, so the script works on any host
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
website_dir = os.path.join(repo_root, "Website")


def file_lastmod(path):
    """Return YYYY-MM-DD for a file. Prefer git's last-commit date; fall back to mtime."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", path],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        iso = result.stdout.strip()
        if iso:
            return iso[:10]
    except Exception:
        pass
    mtime = os.path.getmtime(path)
    return datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d")


html_files = []
for root, dirs, files in os.walk(website_dir):
    for file in files:
        if file.endswith(".html"):
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, website_dir)
            html_files.append(rel_path)

# 1. Generate sitemap.xml
sitemap_content = ['<?xml version="1.0" encoding="UTF-8"?>']
sitemap_content.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

for rel_path in html_files:
    if rel_path == "404.html":
        continue

    # Prioritize certain pages
    priority = "0.5"
    if rel_path == "index.html":
        url = base_url + "/"
        priority = "1.0"
    elif rel_path.startswith("services/") and "/" not in rel_path[9:]:
        url = base_url + "/" + rel_path.replace("\\", "/")
        priority = "0.9"  # Hub pages
    elif rel_path in ["about.html", "contact.html", "pricing.html", "reviews.html", "services.html", "booking.html"]:
        url = base_url + "/" + rel_path.replace("\\", "/")
        priority = "0.8"
    else:
        url = base_url + "/" + rel_path.replace("\\", "/")  # Child services and locations
        priority = "0.7"

    # Per-file lastmod (git commit date if available, else file mtime)
    lastmod = file_lastmod(os.path.join(website_dir, rel_path))

    sitemap_content.append('  <url>')
    sitemap_content.append(f'    <loc>{url}</loc>')
    sitemap_content.append(f'    <lastmod>{lastmod}</lastmod>')
    sitemap_content.append(f'    <priority>{priority}</priority>')
    sitemap_content.append('  </url>')

sitemap_content.append('</urlset>')

with open(os.path.join(website_dir, "sitemap.xml"), "w", encoding="utf-8") as f:
    f.write("\n".join(sitemap_content) + "\n")

# 2. Generate robots.txt
robots_content = f"""User-agent: *
Allow: /

Sitemap: {base_url}/sitemap.xml
"""
with open(os.path.join(website_dir, "robots.txt"), "w", encoding="utf-8") as f:
    f.write(robots_content)

# 3. Generate 404.html
index_html_path = os.path.join(website_dir, "index.html")
with open(index_html_path, "r", encoding="utf-8") as f:
    index_html = f.read()

head_match = re.search(r'(<!DOCTYPE html>.*?</head>)', index_html, re.DOTALL)
top_match = re.search(r'(<body>\s*<!-- Top Bar -->.*?</header>)', index_html, re.DOTALL)
footer_match = re.search(r'(<!-- Footer -->.*?</html>)', index_html, re.DOTALL)

base_head = head_match.group(1).replace(
    '<title>Better Call Wes - Your Local Southampton Plumber | Gas Safe Registered</title>',
    '<title>Page Not Found | Better Call Wes</title>',
)
base_head = re.sub(
    r'<meta name="description".*?>',
    '<meta name="description" content="The page you are looking for does not exist. Return to Better Call Wes.">',
    base_head,
)
base_head = base_head.replace('</head>', '<meta name="robots" content="noindex, follow">\n</head>')

base_top = top_match.group(1) if top_match else ''
base_footer = footer_match.group(1) if footer_match else ''

not_found_content = """
    <section class="hero text-center" style="background: var(--color-primary); min-height: 60vh; padding-top: 180px; padding-bottom: 80px; display: flex; align-items: center;">
        <div class="container">
            <h1 style="color: white; font-size: 8rem; margin-bottom: 1rem; line-height: 1;">404</h1>
            <h2 style="color: white; margin-bottom: 2rem;">Page Not Found</h2>
            <p style="color: rgba(255,255,255,0.8); font-size: 1.25rem; max-width: 600px; margin: 0 auto 3rem;">Sorry, the page you are looking for might have been removed, had its name changed, or is temporarily unavailable.</p>
            <div style="display: flex; gap: 1rem; justify-content: center;">
                <a href="/" class="btn btn-primary"><i data-lucide="home"></i> Return to Homepage</a>
                <a href="services.html" class="btn" style="background: white; color: var(--color-primary);">View All Services</a>
            </div>
        </div>
    </section>
"""

error_page_html = (
    base_head + "\n<body>\n" +
    base_top + "\n" +
    not_found_content + "\n" +
    base_footer
)

with open(os.path.join(website_dir, "404.html"), "w", encoding="utf-8") as f:
    f.write(error_page_html)

print(f"Technical SEO complete: Generated sitemap.xml with {len(html_files)-1} URLs, robots.txt, and 404.html.")
