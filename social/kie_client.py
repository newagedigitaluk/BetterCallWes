"""
Kie AI client for image generation via Nano Banana 2.

Usage:
  - Brand/work/asset posts: provide image_input_url (real photo) + caption overlay prompt
  - AI posts: provide prompt only (fully generated image)

API docs: https://docs.kie.ai
"""

import os
import json
import time
import requests


KIE_API_KEY = os.environ.get("KIE_API_KEY", "")
BASE_URL = "https://api.kie.ai/api/v1"


class KieClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or KIE_API_KEY
        if not self.api_key:
            raise ValueError("KIE_API_KEY environment variable is not set.")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    def generate_image(
        self,
        prompt: str,
        image_input_url: str = None,
        aspect_ratio: str = "1:1",
        resolution: str = "1K",
        output_format: str = "jpg",
        poll_interval: int = 5,
        timeout: int = 180,
    ) -> str:
        """
        Generate or edit an image using Kie AI Nano Banana 2.

        Args:
            prompt: Text description (for ai type) or overlay instruction (for brand/work/asset)
            image_input_url: Public URL of a base image to edit (None for pure generation)
            aspect_ratio: '1:1' recommended for all platforms
            resolution: '1K', '2K', or '4K'
            output_format: 'jpg' or 'png'
            poll_interval: Seconds between status checks
            timeout: Max seconds to wait for generation

        Returns:
            Public URL of the generated/edited image

        Raises:
            RuntimeError: If generation fails or times out
        """
        payload = {
            "model": "nano-banana-2",
            "input": {
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "output_format": output_format,
                "image_input": [image_input_url] if image_input_url else [],
            },
        }

        # Submit task
        resp = self.session.post(f"{BASE_URL}/jobs/createTask", json=payload)
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 200:
            raise RuntimeError(f"Kie AI task creation failed: {data.get('msg')}")

        task_id = data["data"]["taskId"]
        print(f"  [Kie AI] Task created: {task_id}")

        # Poll for completion
        elapsed = 0
        while elapsed < timeout:
            time.sleep(poll_interval)
            elapsed += poll_interval

            status_resp = self.session.get(
                f"{BASE_URL}/jobs/recordInfo", params={"taskId": task_id}
            )
            status_resp.raise_for_status()
            status_data = status_resp.json()

            if status_data.get("code") != 200:
                raise RuntimeError(f"Kie AI status check failed: {status_data.get('msg')}")

            job = status_data["data"]
            state = job.get("state", "")
            print(f"  [Kie AI] Status: {state} ({elapsed}s)")

            if state == "success":
                result_json = job.get("resultJson", "{}")
                result = json.loads(result_json) if isinstance(result_json, str) else result_json
                urls = result.get("resultUrls", [])
                if not urls:
                    raise RuntimeError("Kie AI returned success but no result URLs.")
                return urls[0]

            elif state == "fail":
                fail_msg = job.get("failMsg", "Unknown error")
                raise RuntimeError(f"Kie AI generation failed: {fail_msg}")

            # States: waiting, queuing, generating — keep polling

        raise RuntimeError(f"Kie AI generation timed out after {timeout}s for task {task_id}")

    def check_credits(self) -> int:
        """Return remaining credit balance."""
        resp = self.session.get(f"{BASE_URL}/chat/credit")
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 200:
            raise RuntimeError(f"Failed to check credits: {data.get('msg')}")
        return data["data"]


if __name__ == "__main__":
    # Quick test
    client = KieClient()
    credits = client.check_credits()
    print(f"Kie AI credits remaining: {credits}")
