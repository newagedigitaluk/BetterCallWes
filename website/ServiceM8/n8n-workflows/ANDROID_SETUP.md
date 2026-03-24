# Android Lead Relay Setup Guide (MacroDroid)

This guide replaces the need for Bright Data or complex APIs. Your Android phone will act as the "Listener" for Facebook leads.

## 1. Install MacroDroid
1.  Go to the **Google Play Store** on your Android phone.
2.  Download **MacroDroid - Device Automation**.
3.  Open the app and grant the necessary permissions (Accessibility, Notifications, etc.). These are required for it to "read" your notifications.

## 2. Create the Macro
1.  Tap **"Add Macro"** (the big + button).
2.  Name it: `Facebook Lead Forwarder`.

### Step 2.1: The Trigger (When to run)
1.  In the red **Triggers** section, tap the **+** button.
2.  Search for **"Notification"** and select **Notification Received**.
3.  Select **Select Applications**.
4.  Find and check **Facebook** (and **Business Suite** if you use that too).
5.  **Text Content:** Select **Any**.
6.  Tap **OK**.

### Step 2.2: The Action (What to do)
1.  In the blue **Actions** section, tap the **+** button.
2.  Search for **"HTTP"** and select **HTTP Request**.
3.  **URL:** Paste your n8n Webhook URL here.
    *   *Example:* `https://<your-n8n-instance>/webhook/facebook-android-relay`
    *   *Note:* Ensure you use the "Production" URL (without `-test`) once you are ready, or keep the n8n editor open to test.
4.  **Method:** GET (or POST). Let's use **POST** to send data.
5.  **Content Type:** `application/json`
6.  **Body:**
    ```json
    {
      "text": "[notification_title] - [notification_text]"
    }
    ```
    *   *Tip:* When typing the body, tap the **...** button in MacroDroid to insert "Special Text". Look for `[notification_title]` and `[notification_text]`. This sends the actual content of the alert.
7.  Tap **OK**.

## 3. Test It
1.  Save the Macro (tick button in bottom right).
2.  Open your **n8n workflow**.
3.  Click **Execute Node** on the Webhook node (so it's listening).
4.  On your phone, trigger a test notification (or ask a friend to tag you in a Facebook group).
5.  You should see the data appear in n8n immediately!

## 4. Why this is better
*   **Speed:** Instant.
*   **Cost:** Free (MacroDroid has a free tier, or cheap one-time payment).
*   **Safety:** Uses your real phone behavior, so Facebook won't ban you for "scraping".
