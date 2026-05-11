# 🚀 Deploying Better Call Wes

## Step-by-Step: Coolify Setup (Current)

The site runs as a Docker container (nginx serving static files). Coolify builds the
Dockerfile automatically on every push to `main`.

### 1. Create a New Resource in Coolify
- Go to your Coolify dashboard → **New Resource** → **Application**
- Select **GitHub** and authorise the `newagedigitaluk/BetterCallWes` repo
- Set **Branch** to `main`
- Set **Build Pack** to `Dockerfile` (it will detect the Dockerfile automatically)

### 2. Configure the Application
| Setting | Value |
|---------|-------|
| **Port** | `80` |
| **Build command** | *(leave empty — Dockerfile handles it)* |
| **Health check path** | `/` |

### 3. Add Domain
- Under **Domains**, add `bettercallwes.co.uk` and `www.bettercallwes.co.uk`
- Enable **HTTPS / Let's Encrypt** — Coolify handles the cert automatically

### 4. DNS (Cloudflare)
Point your DNS to your Coolify server's IP address:

| Type | Name | Content |
|------|------|---------|
| A | `@` | *(your Coolify server IP)* |
| A | `www` | *(your Coolify server IP)* |

> ⚠️ If using Cloudflare proxy (orange cloud), set SSL/TLS mode to **Full** in Cloudflare
> to avoid redirect loops. Or turn the proxy off (grey cloud) for a direct connection.

### 5. Deploy
- Click **Deploy** in Coolify — it will build the Docker image and start the container
- Push to `main` in future to trigger auto-redeploy

---

## Step-by-Step: Cloudflare Pages Setup (Legacy)

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
| **Build output directory** | `website/site` |

- Click **"Save and Deploy"**

### 4. Add Custom Domain
- After the first deploy, go to your Pages project → **Custom domains**
- Add `bettercallwes.co.uk` and `www.bettercallwes.co.uk`
- Cloudflare handles SSL automatically

---

## How to Update the Site

Pages are now edited directly as HTML. The old Python page generators
(`build_hub_pages.py`, `build_child_pages.py`, etc.) have been retired —
edit the HTML files in `website/site/` directly and commit.

```bash
# 1. Edit the HTML file
$EDITOR website/site/services/boiler-repair.html

# 2. Preview locally (optional)
python3 -m http.server 8000 -d website/site
# Visit http://localhost:8000

# 3. Validate internal links
python3 website/scripts/validate_links.py

# 4. Commit and push (Coolify rebuilds automatically)
git add website/site/
git commit -m "describe the change"
git push
# Live in ~30 seconds
```

---

## File Structure

```
Better Call Wes/
├── Dockerfile                       ← Build config (COPY website/site → nginx)
├── nginx.conf                       ← Web-server config
├── README.md                        ← Top-level overview
├── CLAUDE.md                        ← Claude Code session instructions
├── docs/                            ← All documentation (you are here)
├── website/
│   ├── site/                        ← THE DEPLOYABLE WEBSITE
│   │   ├── index.html               ← Homepage
│   │   ├── services.html, services/ ← Services hub + 30 service pages
│   │   ├── locations.html, locations/ ← 21 Southampton location pages
│   │   ├── about.html, pricing.html, reviews.html, contact.html, booking.html
│   │   ├── 404.html, sitemap.xml, robots.txt, llms.txt
│   │   ├── css/styles.css           ← All styling
│   │   ├── js/main.js               ← All JavaScript
│   │   └── assets/                  ← Images (WebP) and logo
│   ├── scripts/
│   │   ├── seo/                     ← DataForSEO + VebAPI SEO pipeline
│   │   ├── validate_links.py        ← Internal-link audit
│   │   └── build_technical_seo.py   ← Sitemap + robots.txt generator
│   ├── social/                      ← Social media automation
│   ├── ServiceM8/                   ← Job management
│   └── marketingskills/             ← Marketing content library
└── workspace/                       ← Business ops (Obsidian, session scripts)
```

## Common Tasks

| I want to... | Edit this file |
|---|---|
| Change pricing displayed on a service page | `website/site/services/<name>.html` |
| Update a service page description / FAQ | `website/site/services/<name>.html` |
| Edit a location page | `website/site/locations/<slug>.html` |
| Change contact info | Each HTML file's footer (search for `07700 155 655` to find them all) |
| Update images | Replace files in `website/site/assets/images/` |
| Change CSS/design | `website/site/css/styles.css` |
| Regenerate sitemap | `python3 website/scripts/build_technical_seo.py` |
