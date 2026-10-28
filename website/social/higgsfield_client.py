"""
Higgsfield client for image generation via the Higgsfield CLI.

Replaces kie_client.py (Kie ran on pay-per-use credits which silently ran out
on 2026-05-30 and blacked out Instagram for 12 days; Wes has an annual
Ultimate plan on Higgsfield, so generation now bills to that instead).

Same model (GPT Image 2) and the same structured prompts — only the transport
changed. The CLI accepts LOCAL file paths for the base image (auto-uploads),
so the old "upload base photo to catbox first" step is no longer needed.

Auth: handled by the CLI itself (~/.config/higgsfield/credentials.json),
set up once via `higgsfield auth login`. No env var needed.

Cron-safety: the `higgsfield` shim on PATH lives in an fnm multishell dir
that does NOT exist outside an interactive shell, so we invoke the real
node + script directly with absolute paths, with PATH fallbacks.
"""

import hashlib
import json
import os
import shutil
import time
import subprocess
from pathlib import Path

# Absolute paths for cron (fnm shims don't exist in non-interactive shells).
_FNM_NODE = "/home/wes/.local/share/fnm/node-versions/v22.22.2/installation/bin/node"
_CLI_JS = ("/home/wes/.local/share/fnm/node-versions/v22.22.2/installation"
           "/lib/node_modules/@higgsfield/cli/bin/higgsfield.js")

DEFAULT_MODEL = "gpt_image_2"

# Cached CDN URLs for static assets, keyed by file content hash.
URL_CACHE_PATH = Path(__file__).parent / "state" / "higgsfield_url_cache.json"


def _cli_command() -> list:
    """Resolve the most reliable way to invoke the CLI."""
    if os.path.exists(_FNM_NODE) and os.path.exists(_CLI_JS):
        return [_FNM_NODE, _CLI_JS]
    on_path = shutil.which("higgsfield")
    if on_path:
        return [on_path]
    node = shutil.which("node")
    if node and os.path.exists(_CLI_JS):
        return [node, _CLI_JS]
    raise RuntimeError(
        "higgsfield CLI not found — checked fnm install, PATH, and system node. "
        "Run `npm i -g @higgsfield/cli` or fix paths in higgsfield_client.py."
    )


class HiggsfieldClient:
    def __init__(self):
        self._cli = _cli_command()

    def _run(self, args: list, timeout: int = 360) -> str:
        result = subprocess.run(
            self._cli + args + ["--json", "--no-color"],
            capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"higgsfield {' '.join(args[:3])} failed "
                f"(exit {result.returncode}): {result.stderr.strip()[:300]}"
            )
        return result.stdout

    @staticmethod
    def _is_transient(err: str) -> bool:
        """True if the error looks like a temporary Higgsfield/AWS blip that
        a retry would likely clear.

        Observed in production 2026-08-17→20 (8 of 9 runs failed):
          - SignatureDoesNotMatch  — bad presigned S3 URL from their API
          - HTTP 502 / 503         — their API gateway
          - Cannot reach ...       — DNS/network blip
        All of these fail within seconds, so retrying is cheap.
        """
        e = err.lower()
        return any(s in e for s in (
            "signaturedoesnotmatch", "http 502", "http 503", "http 504",
            "cannot reach", "econnreset", "etimedout", "socket hang up",
            "internal server error", "bad gateway", "service unavailable",
        ))

    def generate_image(
        self,
        prompt: str,
        image_input_path: str = None,
        image_input_url: str = None,   # accepted for kie_client signature compat
        aspect_ratio: str = "1:1",
        resolution: str = "1k",        # 1k is plenty for social feeds
        quality: str = "high",
        model: str = DEFAULT_MODEL,
        poll_interval: int = 5,        # kie_client compat — unused, CLI waits
        timeout: int = 300,
        max_attempts: int = 3,
        budget_seconds: int = 700,
    ) -> str:
        """
        Generate or edit an image. Returns the result URL (Higgsfield CDN).

        Retries transient failures within a total time budget, so a stuck or
        blipping job doesn't cost the post its image.

        Args:
            prompt:            Structured GPT-Image-2 prompt (TASK/SOURCE/CHANGE/...)
            image_input_path:  LOCAL path to the base photo (preferred — CLI
                               auto-uploads it). None for pure text-to-image.
            image_input_url:   Public URL fallback for kie_client call-site
                               compat. Used only if no local path given.
            timeout:           Per-attempt wait (s). Normal generations run
                               140-191s, so 300 is generous; hitting it means
                               the job is stuck and worth abandoning.
            budget_seconds:    Total wall-clock across all attempts. 700 keeps
                               us inside the 900s cron timeout with room for
                               upload + posting afterwards.
        """
        args = [
            "generate", "create", model,
            "--prompt", prompt,
            "--aspect_ratio", aspect_ratio,
            "--resolution", resolution,
            "--quality", quality,
            "--wait", "--wait-timeout", f"{timeout}s",
        ]
        # Resolve the base image to a Higgsfield media UUID FIRST, rather than
        # handing the CLI a local path. The CLI's internal auto-upload is the
        # component that fails with SignatureDoesNotMatch — it broke every
        # image-to-image post 2026-08-17→20 while text-to-image kept working.
        # Our uploader retries and caches, so this both fixes the failure and
        # skips re-uploading assets we've used before.
        base = image_input_path or image_input_url
        if base:
            ref = str(base)
            if image_input_path and os.path.exists(str(image_input_path)):
                try:
                    ref = self.upload_media_id(str(image_input_path))
                except Exception as e:
                    print(f"  [Higgsfield] Pre-upload failed ({str(e)[:90]}); "
                          f"falling back to letting the CLI upload the path")
                    ref = str(image_input_path)
            args += ["--image", ref]

        # RETRY. Higgsfield fails transiently (SignatureDoesNotMatch, 502s) —
        # 8 of 9 runs failed 2026-08-17→20 with a single attempt and no retry.
        # Successful generations take 140-191s, so the budget below allows a
        # stuck job to be abandoned and retried inside the 900s cron window.
        deadline = time.time() + budget_seconds
        last_err = None
        for attempt in range(1, max_attempts + 1):
            remaining = deadline - time.time()
            if remaining < 60:
                break  # not enough left for a meaningful attempt
            attempt_timeout = int(min(timeout, remaining))
            # Set the --wait-timeout VALUE by position of its flag. Using
            # args[-1] was wrong once --image was appended after it, and
            # silently overwrote the image reference.
            args[args.index("--wait-timeout") + 1] = f"{attempt_timeout}s"
            try:
                out = self._run(args, timeout=attempt_timeout + 60)
                jobs = json.loads(out)
                if not jobs:
                    raise RuntimeError("Higgsfield returned no jobs.")
                job = jobs[0] if isinstance(jobs, list) else jobs
                status = job.get("status")
                if status != "completed":
                    raise RuntimeError(f"Higgsfield job {job.get('id')} ended as '{status}'.")
                url = job.get("result_url")
                if not url:
                    raise RuntimeError(f"Higgsfield job {job.get('id')} completed but no result_url.")
                if attempt > 1:
                    print(f"  [Higgsfield] Succeeded on attempt {attempt}")
                break
            except Exception as e:
                last_err = e
                msg = str(e)
                stuck = "timeout after" in msg.lower() or isinstance(e, subprocess.TimeoutExpired)
                if attempt >= max_attempts or (deadline - time.time()) < 60:
                    raise
                if self._is_transient(msg) or stuck:
                    wait = 5 * attempt
                    reason = "stuck job" if stuck else "transient error"
                    print(f"  [Higgsfield] Attempt {attempt} failed ({reason}) — "
                          f"retrying in {wait}s: {msg[:110]}")
                    time.sleep(wait)
                    continue
                raise  # non-transient (bad prompt, auth, credits) — don't burn budget
        else:
            raise last_err or RuntimeError("Higgsfield generation failed")

        print(f"  [Higgsfield] Generated: {url[:70]}...")
        return url

    def upload_media(self, local_path: str, timeout: int = 120) -> str:
        """Upload a local image and return a public CloudFront URL.

        Used as the PRIMARY image host for posting. Replaces catbox.moe,
        which went down (HTTP 412) on 2026-08-13 and silently cost us the
        image on a review-card post — and with it the whole Instagram post,
        since IG rejects imageless posts.

        This runs on the paid Higgsfield plan we already have, serves from
        CloudFront, and needs no auth to fetch (verified) — so Zernio and
        Meta can pull the image fine.
        """
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Image not found: {local_path}")

        # Cache: static assets (review cards, brand photos) are uploaded over
        # and over. Keyed by file content hash, so one successful upload is
        # reused forever — removing the upload step (and its failure mode)
        # entirely for repeat posts. Cache busts automatically if a file changes.
        digest = hashlib.sha256(open(local_path, "rb").read()).hexdigest()[:20]
        cache = self._load_url_cache()
        if digest in cache:
            entry = cache[digest]
            url = entry["url"] if isinstance(entry, dict) else entry
            print(f"  [Higgsfield] Cached URL (no upload needed): {url[:70]}")
            return url

        # Retry — same transient AWS/API failures as generation.
        last_err = None
        for attempt in range(1, 4):
            try:
                out = self._run(["upload", "create", str(local_path)], timeout=timeout)
                data = json.loads(out)
                if isinstance(data, list):
                    data = data[0]
                url = data.get("url")
                if not url:
                    raise RuntimeError(f"Higgsfield upload returned no url: {str(data)[:200]}")
                print(f"  [Higgsfield] Uploaded: {url}")
                cache[digest] = {"url": url, "id": data.get("id")}
                self._save_url_cache(cache)
                return url
            except Exception as e:
                last_err = e
                if attempt < 3 and self._is_transient(str(e)):
                    print(f"  [Higgsfield] Upload attempt {attempt} failed — retrying in {5 * attempt}s")
                    time.sleep(5 * attempt)
                    continue
                raise
        raise last_err

    def upload_media_id(self, local_path: str, timeout: int = 120) -> str:
        """Return the Higgsfield media UUID for a local file (uploading if needed).

        Used to feed `generate create --image <uuid>` instead of a local path.
        The CLI's own auto-upload of local paths is what was throwing
        SignatureDoesNotMatch and killing image-to-image generation for days,
        while text-to-image (no upload) kept working. Going through our own
        retrying + cached uploader avoids that path entirely — and once an
        asset is cached, generation needs no upload at all.
        """
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Image not found: {local_path}")
        digest = hashlib.sha256(open(local_path, "rb").read()).hexdigest()[:20]
        cache = self._load_url_cache()
        entry = cache.get(digest)
        if isinstance(entry, dict) and entry.get("id"):
            return entry["id"]

        last_err = None
        for attempt in range(1, 4):
            try:
                out = self._run(["upload", "create", str(local_path)], timeout=timeout)
                data = json.loads(out)
                if isinstance(data, list):
                    data = data[0]
                mid, url = data.get("id"), data.get("url")
                if not mid:
                    raise RuntimeError(f"Higgsfield upload returned no id: {str(data)[:200]}")
                cache[digest] = {"url": url, "id": mid}
                self._save_url_cache(cache)
                return mid
            except Exception as e:
                last_err = e
                if attempt < 3 and self._is_transient(str(e)):
                    print(f"  [Higgsfield] Upload attempt {attempt} failed — retrying in {5 * attempt}s")
                    time.sleep(5 * attempt)
                    continue
                raise
        raise last_err

    # ---- static-asset URL cache -------------------------------------------

    def _load_url_cache(self) -> dict:
        try:
            return json.loads(URL_CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_url_cache(self, cache: dict):
        try:
            URL_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            URL_CACHE_PATH.write_text(json.dumps(cache, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"  [Higgsfield] (could not save URL cache: {e})")

    def check_credits(self) -> float:
        """Return remaining credit balance (annual plan)."""
        out = self._run(["account", "status"], timeout=30)
        data = json.loads(out)
        return data.get("credits", 0)


if __name__ == "__main__":
    client = HiggsfieldClient()
    print(f"Higgsfield credits remaining: {client.check_credits()}")
