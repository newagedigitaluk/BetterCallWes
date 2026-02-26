# 🚀 Deploying Better Call Wes

## Step-by-Step: Cloudflare Pages Setup

### 1. Create a Cloudflare Account
- Go to [dash.cloudflare.com](https://dash.cloudflare.com) and sign up (free)

### 2. Connect Your Domain
- In the Cloudflare dashboard, click **"Add a site"**
- Enter `bettercallwes.co.uk`
- Select the **Free plan**
- Cloudflare will give you 2 nameservers — update these at your domain registrar (e.g., GoDaddy, Namecheap, etc.)
- Wait for DNS to propagate (usually 5-30 minutes)

### 3. Set Up Cloudflare Pages
- In the Cloudflare dashboard, go to **Workers & Pages** → **Create**
- Select **"Connect to Git"**
- Authorize GitHub and select the **`newagedigitaluk/BetterCallWes`** repo
- Configure the build:

| Setting | Value |
|---------|-------|
| **Production branch** | `main` |
| **Build command** | *(leave empty)* |
| **Build output directory** | `Website` |

- Click **"Save and Deploy"**

### 4. Add Custom Domain
- After the first deploy, go to your Pages project → **Custom domains**
- Add `bettercallwes.co.uk` and `www.bettercallwes.co.uk`
- Cloudflare handles SSL automatically

---

## How to Update the Site

### Quick Text/Content Changes
```bash
# 1. Edit the Python generator scripts (e.g., build_hub_pages.py)
# 2. Rebuild all pages
./rebuild.sh

# 3. Push to GitHub (auto-deploys to Cloudflare)
git add .
git commit -m "Updated pricing info"
git push
```

### Full Workflow
```bash
# 1. Make your changes to the generator scripts
# 2. Rebuild & preview locally
./rebuild.sh
python3 -m http.server 8000 -d Website
# 3. Check http://localhost:8000 in your browser
# 4. Happy? Push to deploy
git add .
git commit -m "Describe what you changed"
git push
# ✅ Live in ~30 seconds
```

---

## File Structure

```
Better Call Wes/
├── Website/                  ← This folder is what gets deployed
│   ├── index.html            ← Homepage
│   ├── css/styles.css        ← All styling
│   ├── js/main.js            ← All JavaScript
│   ├── assets/images/        ← All images
│   ├── services/             ← Service pages (generated)
│   ├── locations/            ← Location pages (generated)
│   ├── sitemap.xml           ← SEO sitemap
│   └── robots.txt            ← SEO robots
├── build_hub_pages.py        ← Generates service hub pages
├── build_child_pages.py      ← Generates child service pages
├── build_advanced_location_pages.py  ← Generates location pages
├── build_trust_pages.py      ← Generates about/contact/pricing/reviews
├── build_technical_seo.py    ← Generates sitemap & robots.txt
├── rebuild.sh                ← One-command full rebuild
└── DEPLOY.md                 ← This file
```

## Common Tasks

| I want to... | Edit this file |
|---|---|
| Change pricing | `build_hub_pages.py` → `price` field |
| Update service descriptions | `build_hub_pages.py` or `build_child_pages.py` |
| Add a new location | `build_advanced_location_pages.py` → `locations` list |
| Change contact info | `Website/index.html` (footer) + `build_trust_pages.py` |
| Update images | Replace files in `Website/assets/images/` |
| Change CSS/design | `Website/css/styles.css` |
