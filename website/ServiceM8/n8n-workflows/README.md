# Facebook Lead Sniper Setup Guide

## 1. Facebook Settings (Crucial)
You must ensure Facebook sends you an email for **every** group post, not just "Suggested" highlights.
- Go to **Settings** -> **Notifications** -> **Email**.
- Set "Comments" and "Posts in Groups" to **ON**.
- Ensure the frequency is set to **"All"** (not "Suggested").

## 2. Strategy: The "Dedicated Listener" (Recommended)
Instead of clogging your main business inbox with hundreds of Facebook notifications, the **best way** is to use a dedicated email address (e.g., create a free Gmail like `wes.leads.monitor@gmail.com`).
1.  Add this new email to your Facebook **Settings -> Contact Info**.
2.  Set it as the **Primary** notification email.
3.  Connect **n8n** to this specific account.
**Benefit:** Your main Outlook stays clean. n8n monitors the "Burner" account 24/7.

## 3. Gmail IMAP Settings (For your new account)
Use these exact details in n8n for your new Gmail account:

| Field | Value |
|-------|-------|
| **Protocol** | IMAP |
| **Host** | `imap.gmail.com` |
| **Port** | `993` |
| **SSL/TLS** | `true` |
| **Username** | Your new Gmail address |
| **Password** | **Must use App Password** (see below) |

### How to get a Gmail App Password
1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** (if not already on).
3. Search for **"App passwords"** in the top search bar.
4. Create a new one named `n8n`.
5. Copy the 16-character code. This is your password for n8n.

## 4. Outlook 365 IMAP Settings (Alternative)

| Field | Value |
|-------|-------|
| **Protocol** | IMAP |
| **Host** | `outlook.office365.com` |
| **Port** | `993` |
| **SSL/TLS** | `true` (Enable SSL) |
| **Username** | Your full email address |
| **Password** | **Must use App Password** (see below) |

### How to get an Outlook App Password
If you have 2FA enabled (most accounts do), your normal password **will not work**.
1. Go to [mysignins.microsoft.com/security-info](https://mysignins.microsoft.com/security-info)
2. Click **+ Add sign-in method**.
3. Choose **App password**.
4. Name it `n8n`.
5. Copy the code it generates. This is the password you paste into n8n.

## 3. Importing the Workflow
1. In n8n, click **Add Workflow** -> **Import from File**.
2. Select the `n8n_email_trap.json` file in this folder.
3. Update the credentials in the IMAP and Straico nodes.
