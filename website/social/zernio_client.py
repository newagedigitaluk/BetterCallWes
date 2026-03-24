"""
Zernio client for uploading media and posting to social platforms.

API docs: https://docs.zernio.com
Base URL: https://zernio.com/api/v1
"""

import os
import io
import requests


ZERNIO_API_KEY = os.environ.get("ZERNIO_API_KEY", "")
BASE_URL = "https://zernio.com/api/v1"

# Platform name mapping (Zernio uses lowercase platform strings)
PLATFORM_MAP = {
    "facebook": "facebook",
    "instagram": "instagram",
    "twitter": "twitter",
    "x": "twitter",
    "googlebusiness": "googlebusiness",
    "google": "googlebusiness",
}


class ZernioClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or ZERNIO_API_KEY
        if not self.api_key:
            raise ValueError("ZERNIO_API_KEY environment variable is not set.")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    def list_accounts(self) -> list:
        """
        List all connected social media accounts.

        Returns:
            List of normalised dicts: [{ 'id': '...', 'platform': 'facebook|instagram|...',
                                         'displayName': '...', 'followersCount': N }]
        """
        resp = self.session.get(f"{BASE_URL}/accounts")
        resp.raise_for_status()
        data = resp.json()

        # Response is { "accounts": [...], "hasAnalyticsAccess": bool }
        raw_accounts = data.get("accounts", data) if isinstance(data, dict) else data

        normalised = []
        for acc in raw_accounts:
            normalised.append({
                "id": acc.get("_id") or acc.get("id", ""),
                "platform": acc.get("platform", "").lower(),
                "displayName": acc.get("displayName") or acc.get("username", ""),
                "followersCount": acc.get("followersCount"),
                "isActive": acc.get("isActive", True),
            })
        return normalised

    def upload_image_for_kie(self, local_path: str) -> str:
        """
        Upload a local image to catbox.moe and return its public URL.
        Used to give Kie AI a public URL for base image input.

        Args:
            local_path: Absolute path to a local image file

        Returns:
            Public URL string (e.g. https://files.catbox.moe/abc123.jpg)

        Raises:
            FileNotFoundError: If local file doesn't exist
            RuntimeError: If upload fails
        """
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Image file not found: {local_path}")

        filename = os.path.basename(local_path)
        ext = os.path.splitext(filename)[1].lower()
        content_type = "image/png" if ext == ".png" else (
            "image/webp" if ext == ".webp" else "image/jpeg"
        )

        with open(local_path, "rb") as f:
            resp = requests.post(
                "https://catbox.moe/user/api.php",
                data={"reqtype": "fileupload", "userhash": ""},
                files={"fileToUpload": (filename, f, content_type)},
                timeout=60,
            )
        resp.raise_for_status()
        public_url = resp.text.strip()
        if not public_url.startswith("http"):
            raise RuntimeError(f"catbox.moe upload failed: {public_url}")
        print(f"  [catbox] Uploaded: {public_url}")
        return public_url

    def rehost_url_to_catbox(self, image_url: str) -> str:
        """
        Download an image from a URL and re-upload it to catbox.moe.

        Used to convert a temporary Kie AI URL into a permanent catbox.moe
        URL before posting to multiple platforms sequentially. Kie AI URLs
        expire quickly, causing failures on the 2nd or 3rd platform call.

        Args:
            image_url: Any publicly accessible image URL

        Returns:
            Permanent catbox.moe URL (e.g. https://files.catbox.moe/abc123.jpg)

        Raises:
            RuntimeError: If download or upload fails
        """
        # Download the image bytes
        dl_resp = requests.get(image_url, timeout=60)
        dl_resp.raise_for_status()
        image_bytes = dl_resp.content

        # Detect content type from response or URL
        content_type = dl_resp.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
        ext_map = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
        ext = ext_map.get(content_type, ".jpg")
        filename = f"kie_generated{ext}"

        # Upload to catbox.moe
        resp = requests.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload", "userhash": ""},
            files={"fileToUpload": (filename, io.BytesIO(image_bytes), content_type)},
            timeout=60,
        )
        resp.raise_for_status()
        public_url = resp.text.strip()
        if not public_url.startswith("http"):
            raise RuntimeError(f"catbox.moe rehost failed: {public_url}")
        print(f"  [catbox] Rehosted Kie AI image: {public_url}")
        return public_url

    def create_post(
        self,
        content: str,
        platform: str,
        account_id: str,
        media_url: str = None,
        publish_now: bool = True,
    ) -> dict:
        """
        Create a post on a single platform.

        Args:
            content: Post text
            platform: 'facebook', 'instagram', or 'twitter' (used for logging only)
            account_id: Zernio account _id (e.g. '69224444f43160a0bc998bc4')
            media_url: Public URL of image to attach (optional)
            publish_now: Post immediately if True, save as draft if False

        Returns:
            Zernio post response dict
        """
        payload = {
            "content": content,
            "platforms": [{"accountId": account_id, "platform": platform}],
            "publishNow": publish_now,
        }

        if media_url:
            payload["mediaItems"] = [{"url": media_url, "mediaType": "image"}]

        resp = self.session.post(f"{BASE_URL}/posts", json=payload)
        resp.raise_for_status()
        result = resp.json()
        post_data = result.get("post", result)
        post_id = post_data.get("_id") or post_data.get("id", "unknown")
        print(f"  [Zernio] Posted to {platform}: post ID {post_id}")
        return result


if __name__ == "__main__":
    # Quick test — list connected accounts
    client = ZernioClient()
    accounts = client.list_accounts()
    print(f"\nConnected accounts ({len(accounts)}):")
    for acc in accounts:
        print(f"  {acc.get('platform', '?'):15} | ID: {acc.get('id', '?')}")
