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

import json
import os
import shutil
import subprocess
from pathlib import Path

# Absolute paths for cron (fnm shims don't exist in non-interactive shells).
_FNM_NODE = "/home/wes/.local/share/fnm/node-versions/v22.22.2/installation/bin/node"
_CLI_JS = ("/home/wes/.local/share/fnm/node-versions/v22.22.2/installation"
           "/lib/node_modules/@higgsfield/cli/bin/higgsfield.js")

DEFAULT_MODEL = "gpt_image_2"


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
    ) -> str:
        """
        Generate or edit an image. Returns the result URL (Higgsfield CDN).

        Args:
            prompt:            Structured GPT-Image-2 prompt (TASK/SOURCE/CHANGE/...)
            image_input_path:  LOCAL path to the base photo (preferred — CLI
                               auto-uploads it). None for pure text-to-image.
            image_input_url:   Public URL fallback for kie_client call-site
                               compat. Used only if no local path given.
        """
        args = [
            "generate", "create", model,
            "--prompt", prompt,
            "--aspect_ratio", aspect_ratio,
            "--resolution", resolution,
            "--quality", quality,
            "--wait", "--wait-timeout", f"{timeout}s",
        ]
        base = image_input_path or image_input_url
        if base:
            args += ["--image", str(base)]

        out = self._run(args, timeout=timeout + 60)
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
        print(f"  [Higgsfield] Generated: {url[:70]}...")
        return url

    def check_credits(self) -> float:
        """Return remaining credit balance (annual plan)."""
        out = self._run(["account", "status"], timeout=30)
        data = json.loads(out)
        return data.get("credits", 0)


if __name__ == "__main__":
    client = HiggsfieldClient()
    print(f"Higgsfield credits remaining: {client.check_credits()}")
