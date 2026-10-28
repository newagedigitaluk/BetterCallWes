"""
Zernio client for uploading media and posting to social platforms.

API docs: https://docs.zernio.com
Base URL: https://zernio.com/api/v1
"""

import os
import io
import time
import uuid
import requests

import zernio_limits as limits


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


def ensure_instagram_safe(image_bytes: bytes, filename: str) -> tuple:
    """Convert WebP → JPEG so Instagram accepts the image.

    Instagram's API rejects WebP (returns a 400). Most of the BCW asset
    library is .webp, so any time a WebP reached the upload step — via the
    generation fallback, or a WebP base photo — Instagram silently failed
    while Facebook and Google Business posted fine.

    PNG is left alone (it posts successfully). Only WebP is converted.

    Returns: (image_bytes, filename, content_type)
    """
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".webp":
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(image_bytes))
            # JPEG has no alpha channel — flatten onto white if needed
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGBA")
                bg = Image.new("RGB", img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[-1])
                img = bg
            else:
                img = img.convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=92)
            new_name = os.path.splitext(filename)[0] + ".jpg"
            print(f"  [image] Converted WebP → JPEG for Instagram compatibility ({new_name})")
            return buf.getvalue(), new_name, "image/jpeg"
        except Exception as e:
            print(f"  [image] ⚠️  WebP→JPEG conversion failed ({e}); uploading as-is")
            return image_bytes, filename, "image/webp"
    if ext == ".png":
        return image_bytes, filename, "image/png"
    return image_bytes, filename, "image/jpeg"


def _safe_json(resp) -> dict:
    try:
        return resp.json() or {}
    except ValueError:
        return {}


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

    # ---------------------------------------------------------------------
    # Every write goes through here.
    #
    # Zernio's idempotency guide: send x-request-id (UUIDv4) and a retry of
    # the SAME id inside ~5 minutes returns the original post instead of
    # creating a second one. That matters because this client retries on
    # 5xx/timeouts — without the header, a request that succeeded server-side
    # but died on the way back would post twice.
    #
    # Also documented and handled here:
    #   409 -> content duplicate within 24h; body carries existingPostId
    #   429 -> back off by Retry-After / details.retryAfterSeconds
    # ---------------------------------------------------------------------
    def _post_idempotent(self, path: str, payload: dict, timeout: int = 120,
                         attempts: int = 3) -> dict:
        request_id = str(uuid.uuid4())
        last_exc = None
        for attempt in range(1, attempts + 1):
            try:
                resp = self.session.post(
                    f"{BASE_URL}{path}", json=payload, timeout=timeout,
                    headers={"x-request-id": request_id},
                )
            except requests.RequestException as e:
                last_exc = e
                if attempt == attempts:
                    raise
                time.sleep(min(2 ** attempt, 20))
                continue

            if resp.status_code == 429:
                body = _safe_json(resp)
                wait = (resp.headers.get("Retry-After")
                        or (body.get("details") or {}).get("retryAfterSeconds")
                        or 60)
                wait = min(int(float(wait)), 300)
                if attempt == attempts:
                    raise RuntimeError(f"Zernio rate limited; retry after {wait}s")
                print(f"  [Zernio] 429 rate limited — waiting {wait}s")
                time.sleep(wait)
                continue

            if resp.status_code == 409:
                # Same content within 24h. Not an error worth failing a cron
                # run over — surface the existing post and move on.
                body = _safe_json(resp)
                existing = body.get("existingPostId") or (body.get("details") or {}).get("existingPostId")
                print(f"  [Zernio] Duplicate content (409); existing post {existing}")
                return {"duplicate": True, "existingPostId": existing, **body}

            if resp.status_code >= 500:
                if attempt == attempts:
                    resp.raise_for_status()
                print(f"  [Zernio] {resp.status_code} — retrying with same x-request-id")
                time.sleep(min(2 ** attempt, 20))
                continue

            resp.raise_for_status()
            body = _safe_json(resp)
            if body.get("existingPost"):
                print("  [Zernio] Idempotent replay — returning the original post")
            return body
        raise last_exc or RuntimeError("Zernio post failed")

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

        with open(local_path, "rb") as f:
            image_bytes = f.read()

        image_bytes, filename, content_type = ensure_instagram_safe(image_bytes, filename)

        # PRIMARY HOST: Zernio's own media endpoint.
        #
        # Host history, and why this is the right answer:
        #   catbox.moe      — sole host until it started 412ing (13 Aug)
        #   Higgsfield CDN  — replaced it, then its uploads began failing with
        #                     SignatureDoesNotMatch (17 Aug, still failing)
        #   BOTH failed at once on 21 Aug 13:07 → post published with no image
        #                     → Instagram rejected it entirely.
        #
        # Zernio hosts media itself, and Zernio is the service we post THROUGH.
        # If it's up enough to publish, it's up enough to host — so this removes
        # the "independent third party goes down" failure mode rather than just
        # moving it. The other two remain as fallbacks.
        try:
            files = {"files": (filename, io.BytesIO(image_bytes), content_type)}
            # NOT self.session — its default Content-Type: application/json
            # overrides the multipart boundary and the API rejects it as 400.
            resp = requests.post(
                f"{BASE_URL}/media", files=files,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=90,
            )
            resp.raise_for_status()
            url = (resp.json().get("files") or [{}])[0].get("url")
            if url:
                print(f"  [Zernio media] Uploaded: {url}")
                return url
            print("  [Zernio media] No URL in response; trying Higgsfield…")
        except Exception as e:
            print(f"  [Zernio media] Upload failed ({str(e)[:90]}); trying Higgsfield…")

        # FALLBACK 1: Higgsfield CDN (paid plan, CloudFront, public).
        # WebP is converted above, so what we upload here is already IG-safe.
        tmp_path = None
        try:
            from higgsfield_client import HiggsfieldClient
            upload_src = local_path
            if filename != os.path.basename(local_path):
                # ensure_instagram_safe converted the bytes (WebP→JPEG);
                # write the converted version out so we upload the right one.
                import tempfile
                fd, tmp_path = tempfile.mkstemp(suffix=os.path.splitext(filename)[1])
                with os.fdopen(fd, "wb") as tf:
                    tf.write(image_bytes)
                upload_src = tmp_path
            return HiggsfieldClient().upload_media(upload_src)
        except Exception as e:
            print(f"  [Higgsfield] Upload failed ({e}); falling back to catbox…")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

        # Try litterbox.catbox.moe (anonymous, 72h expiry — long enough for posting)
        try:
            resp = requests.post(
                "https://litterbox.catbox.moe/resources/internals/api.php",
                data={"reqtype": "fileupload", "time": "72h"},
                files={"fileToUpload": (filename, io.BytesIO(image_bytes), content_type)},
                timeout=60,
            )
            resp.raise_for_status()
            public_url = resp.text.strip()
            if public_url.startswith("http"):
                print(f"  [litterbox] Uploaded: {public_url}")
                return public_url
        except Exception as e:
            print(f"  [litterbox] Failed ({e}), trying catbox...")

        # Fallback: catbox.moe permanent anonymous upload
        resp = requests.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload", "userhash": ""},
            files={"fileToUpload": (filename, io.BytesIO(image_bytes), content_type)},
            timeout=60,
        )
        resp.raise_for_status()
        public_url = resp.text.strip()
        if not public_url.startswith("http"):
            raise RuntimeError(f"catbox.moe upload failed: {public_url}")
        print(f"  [catbox] Uploaded: {public_url}")
        return public_url

    def upload_video(self, local_path: str) -> str:
        """Upload an MP4 and return a public URL for posting as a Reel.

        Zernio only tags the file as video when the multipart part carries an
        explicit video/mp4 content-type — without it the API stores it as
        application/octet-stream and the platforms reject the post.
        """
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Video not found: {local_path}")
        filename = os.path.basename(local_path)
        with open(local_path, "rb") as f:
            data = f.read()
        files = {"files": (filename, io.BytesIO(data), "video/mp4")}
        resp = requests.post(
            f"{BASE_URL}/media", files=files,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=300,
        )
        resp.raise_for_status()
        entry = (resp.json().get("files") or [{}])[0]
        if entry.get("type") != "video":
            raise RuntimeError(f"Zernio did not register the upload as video: {entry}")
        url = entry.get("url")
        if not url:
            raise RuntimeError(f"No URL returned for video upload: {entry}")
        print(f"  [Zernio media] Video uploaded: {url}")
        return url

    def create_reel(self, content: str, platform: str, account_id: str,
                    video_url: str, video_path: str = None,
                    platform_data: dict = None) -> dict:
        """Publish a Reel (video post) to one platform.

        video_path is the local file, used only for preflight checks — the
        duration windows differ (Instagram 3-90s, Facebook 3-60s), so the
        same clip can be legal on one and rejected by the other.
        """
        problems = limits.validate_text(platform, content)
        problems += limits.validate_video(platform, video_path)
        if problems:
            raise limits.PostValidationError("; ".join(problems))

        # platformSpecificData belongs INSIDE the platform entry, and is not
        # keyed by platform name — see docs.zernio.com/platforms/facebook.
        # Put at the top level it is silently ignored, which is how our first
        # reel went out as an ordinary feed video rather than a Reel.
        plat = {"accountId": account_id, "platform": platform}
        if platform == "facebook":
            # Without contentType, Facebook publishes a plain feed video.
            plat["platformSpecificData"] = {"contentType": "reel"}
        elif platform == "instagram":
            # A lone video becomes a Reel automatically; shareToFeed also
            # puts it in the grid instead of the Reels tab only.
            plat["platformSpecificData"] = {"shareToFeed": True}
        if platform_data:
            problems = limits.validate_platform_data(platform, platform_data)
            if problems:
                raise limits.PostValidationError("; ".join(problems))
            plat["platformSpecificData"] = {**plat.get("platformSpecificData", {}),
                                            **platform_data}

        payload = {
            "content": content,
            "platforms": [plat],
            "mediaItems": [{"url": video_url, "type": "video"}],
            "publishNow": True,
        }

        result = self._post_idempotent("/posts", payload)
        if result.get("duplicate"):
            return result
        pid = (result.get("post") or result).get("_id", "unknown")
        print(f"  [Zernio] Reel posted to {platform}: {pid}")
        return result

    def rehost_url_to_catbox(self, image_url: str) -> str:
        """
        Re-host a generated image at a stable public URL.

        Generation URLs can expire quickly, which breaks posting to the 2nd
        or 3rd platform in a run. Images generated by Higgsfield already sit
        on its CloudFront CDN, so those are returned as-is — no rehost, no
        third-party dependency, no failure mode.

        Anything else is downloaded and pushed to catbox.moe as before.
        (Name kept for call-site compatibility.)

        Args:
            image_url: Any publicly accessible image URL

        Returns:
            A stable public image URL

        Raises:
            RuntimeError: If download or upload fails
        """
        # Higgsfield images are already on a permanent public CDN — using the
        # URL directly removes a whole class of failure (catbox outages) and
        # a needless download+upload round trip.
        if "cloudfront.net" in image_url:
            print(f"  [image] Already on CDN, no rehost needed: {image_url[:70]}")
            return image_url

        # Download the image bytes
        dl_resp = requests.get(image_url, timeout=60)
        dl_resp.raise_for_status()
        image_bytes = dl_resp.content

        # Detect content type from response or URL, then make Instagram-safe
        content_type = dl_resp.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
        ext_map = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
        filename = f"generated{ext_map.get(content_type, '.jpg')}"
        image_bytes, filename, content_type = ensure_instagram_safe(image_bytes, filename)

        # Try litterbox first, then catbox as fallback
        try:
            resp = requests.post(
                "https://litterbox.catbox.moe/resources/internals/api.php",
                data={"reqtype": "fileupload", "time": "72h"},
                files={"fileToUpload": (filename, io.BytesIO(image_bytes), content_type)},
                timeout=60,
            )
            resp.raise_for_status()
            public_url = resp.text.strip()
            if public_url.startswith("http"):
                print(f"  [litterbox] Rehosted Kie AI image: {public_url}")
                return public_url
        except Exception as e:
            print(f"  [litterbox] Rehost failed ({e}), trying catbox...")

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
        platform_data: dict = None,
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
        problems = limits.validate_text(platform, content)
        if problems:
            raise limits.PostValidationError("; ".join(problems))

        entry = {"accountId": account_id, "platform": platform}
        if platform_data:
            # e.g. Instagram {"firstComment": ...}, Google Business
            # {"callToAction": {"type": "BOOK", "url": https-url}}. Lives
            # inside the platform entry, never at the top level.
            problems = limits.validate_platform_data(platform, platform_data)
            if problems:
                raise limits.PostValidationError("; ".join(problems))
            entry["platformSpecificData"] = platform_data
        payload = {
            "content": content,
            "platforms": [entry],
            "publishNow": publish_now,
        }

        if media_url:
            # Documented field is `type` (image|video|gif|document).
            payload["mediaItems"] = [{"url": media_url, "type": "image"}]

        result = self._post_idempotent("/posts", payload)
        if result.get("duplicate"):
            return result
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
