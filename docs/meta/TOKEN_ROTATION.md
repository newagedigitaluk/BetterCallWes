# Meta Token Rotation — System User Setup

Follow these steps in order. Once complete, paste the new App Secret and System User token into `.env` and tell me — I'll redeploy n8n + build v3.

---

## Step 1 — Reset the App Secret

1. Open: **https://developers.facebook.com/apps/1454174139594007/settings/basic/**
2. Scroll to the **App Secret** field
3. Click **Show** → enter your Facebook password if prompted
4. Click **Reset**
5. Copy the new value — you'll paste it into `.env` as `META_APP_SECRET=...`

---

## Step 2 — Revoke the leaked user token

1. Open: **https://www.facebook.com/settings?tab=business_tools**
   (or: Settings & Privacy → Settings → Business Integrations)
2. Find **BCW Ads** in the list of apps
3. Click **Remove** → confirm
4. This immediately kills the old token so anyone who scraped the GitHub repo can no longer do anything with it.

---

## Step 3 — Create the System User

1. Open: **https://business.facebook.com/settings**
2. Left sidebar → **Users** → **System Users**
3. Click **Add**
4. Name: `BCW Automation`
5. Role: **Admin** (full access — needed to manage ads and fire CAPI events)
6. Click **Create System User**

---

## Step 4 — Assign assets to the System User

The System User needs access to your ad account, page, and pixel. Do each in turn.

While viewing your new `BCW Automation` System User:

### 4a. Ad Account
1. Click **Assign Assets** → **Ad Accounts**
2. Select: **Better Call Wes** (account ID `act_1157261541704017`)
3. Turn on **Full Control**
4. Save

### 4b. Facebook Page
1. Click **Assign Assets** → **Pages**
2. Select: **Better Call Wes** (page ID `178728745664355`)
3. Turn on **Full Control** (this enables both ad management and CAPI)
4. Save

### 4c. Pixel (Dataset)
1. Left sidebar → **Data Sources** → **Datasets** (sometimes called "Pixels")
2. Select your pixel: **Better Call Wes Pixel** (`1612104182479593`)
3. Click **Assigned Users** → **Add People** → select `BCW Automation` System User → grant **Manage Dataset** permission
4. Save

---

## Step 5 — Generate the System User access token

1. Still in Business Settings → **Users** → **System Users** → click `BCW Automation`
2. Click **Generate New Token** button
3. In the dialog:
   - **App**: select **BCW Ads**
   - **Token Expiration**: select **Never**
   - **Permissions** — tick all of:
     - `ads_management`
     - `ads_read`
     - `pages_manage_ads`
     - `pages_read_engagement`
     - `pages_show_list`
     - `business_management`
     - `public_profile`
4. Click **Generate Token**
5. **Important: Copy the token immediately — it's only shown once.** Meta does not let you view it again after you close the dialog.

The token will start with `EAA` and be very long (200+ characters).

---

## Step 6 — Update .env and tell me

Open `/home/wes/Coding/Projects/Better Call Wes/.env` and replace the two values:

```
META_APP_SECRET=<the new secret from Step 1>
META_ACCESS_TOKEN=<the new System User token from Step 5>
```

Save the file. Tell me "done" and I'll:
1. Verify the new token works (debug_token check)
2. Redeploy the n8n workflow with the new token
3. Build the v3 campaign via API
4. Activate v3

---

## What if anything goes wrong

- **Can't find "System Users"** → make sure you're in **Business Settings** (business.facebook.com/settings), not account settings
- **Can't assign the pixel** → Datasets live under Data Sources in the new UI. If you can't find it, go to Events Manager → Settings → "Assign Partners / Users" works too
- **Token doesn't have required scopes when generated** → hit Generate Token again, scroll the permission list more carefully; all six must be ticked
- **Forgot to copy the token** → generate a new one; the old one stays valid until manually revoked, but best to just issue a fresh one

---

## Why this is better than the user token

| | Old (user token) | New (System User) |
|---|---|---|
| Tied to your personal FB account | Yes | No |
| Survives you logging out / losing access | No | Yes |
| Appears in your personal "connected apps" list | Yes | No |
| Can be leaked via personal account compromise | Yes | No |
| Expires | Every 60 days unless long-lived | Never |
| Suitable for server automation | Marginal | Yes — purpose-built |
