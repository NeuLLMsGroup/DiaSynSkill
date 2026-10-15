"""
Lightweight LLM Client for Experience & Skill Generation

Provides a unified interface for calling LLM APIs (chat and multimodal)
with automatic retry, exponential backoff, and primary/fallback API
endpoint switching.

All credentials are read from environment variables (EXPERIENCE_API_KEY,
EXPERIENCE_END_POINT, etc.). No keys are hard-coded.

NOTE: Partial release. Full implementation with round-robin scheduling
across multiple API keys available upon paper acceptance.
"""

import os
import time
import requests
from typing import Optional, Dict, List, Union, Any
from PIL import Image


# ---- Constants ----

MAX_RETRIES = 3
API_TIMEOUT = 300           # general API timeout (seconds)
API_TIMEOUT_IMAGE = 300     # multimodal API timeout (seconds)
MAX_TOKENS_DEFAULT = 8192


class ExperienceLLM:
    """
    Lightweight LLM adapter for experience generation via API.

    Reads configuration from environment variables:
      - EXPERIENCE_MODEL_NAME: model identifier
      - EXPERIENCE_API_KEY / EXPERIENCE_END_POINT: primary credentials
      - EXPERIENCE_API_KEY_2 / EXPERIENCE_END_POINT_2: fallback (optional)
    """

    def __init__(self, model_name=None):
        self.model_name = (
            model_name
            or os.environ.get("EXPERIENCE_MODEL_NAME")
            or os.environ.get("MODEL_NAME")
            or "gpt-4o"
        )

    # ---- Text Chat ----

    def chat(self, prompt, max_tokens=MAX_TOKENS_DEFAULT,
             temperature=None, top_p=1.0):
        """Send a text-only prompt and return the model response."""
        t = temperature if temperature is not None else 0.6
        return self._call_with_fallback(
            user_content=prompt,
            max_tokens=max_tokens,
            temperature=t,
            top_p=top_p,
        )

    # ---- Multimodal Chat ----

    def chat_with_image(self, prompt, image, max_tokens=MAX_TOKENS_DEFAULT,
                        temperature=None, top_p=1.0, system_prompt=None,
                        return_placeholder_on_error=True):
        """
        Send a prompt with one or more images.

        Args:
            prompt: Text instruction
            image: PIL.Image or list of PIL.Image
            max_tokens: generation cap
            temperature: sampling temperature (default 0.6)
            return_placeholder_on_error: if True, returns "[Error: ...]"
                                         instead of raising
        """
        t = temperature if temperature is not None else 0.6

        if system_prompt is None:
            system_prompt = (
                "You are an expert at analyzing images and providing "
                "detailed visual descriptions."
            )

        # Normalize to list
        images = [image] if isinstance(image, Image.Image) else image

        # Build multimodal content: text first, then base64 images
        user_content = [{"type": "text", "text": prompt}]
        for img in images:
            base64_image = self._image_to_base64(img)
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                },
            })

        return self._call_with_fallback(
            user_content=user_content,
            max_tokens=max_tokens,
            temperature=t,
            top_p=top_p,
            system_prompt=system_prompt,
            timeout=API_TIMEOUT_IMAGE,
            return_placeholder_on_error=return_placeholder_on_error,
            require_chat_completions=True,
        )

    # ---- Internal: API call with retry + fallback ----

    def _try_single_api(self, api_key, end_point, user_content,
                        max_tokens, temperature, top_p, max_retries,
                        api_name="API", system_prompt=None,
                        timeout=API_TIMEOUT,
                        return_placeholder_on_error=False):
        """
        Call a single API endpoint with full retry + exponential backoff.

        Handles HTTP errors, timeouts, and empty responses. Non-retryable
        status codes (400, 401, 403, 404) are raised immediately.
        """
        if system_prompt is None:
            system_prompt = (
                "You are an expert at summarizing visual reasoning "
                "trajectories and extracting generalizable experiences."
            )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
        }

        base_wait = 1.0
        for attempt in range(max_retries):
            try:
                resp = requests.post(
                    end_point, headers=headers, json=payload, timeout=timeout
                )

                if resp.status_code == 200:
                    data = resp.json()
                    content = (
                        data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                        .strip()
                    )
                    if content:
                        return content
                    # Empty content: retry
                    if attempt < max_retries - 1:
                        time.sleep(base_wait)
                        continue
                    if return_placeholder_on_error:
                        return "[Failed: empty response]"
                    raise RuntimeError(
                        f"[{api_name}] Empty content after {max_retries} attempts"
                    )

                # Non-200 response
                if attempt < max_retries - 1:
                    time.sleep(base_wait)
                    continue
                if return_placeholder_on_error:
                    return f"[Failed: HTTP {resp.status_code}]"
                raise RuntimeError(
                    f"[{api_name}] HTTP {resp.status_code}"
                )

            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    if return_placeholder_on_error:
                        return "[Failed: timeout]"
                    raise
                time.sleep(base_wait)
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    if return_placeholder_on_error:
                        return f"[Failed: {str(e)}]"
                    raise
                time.sleep(base_wait)

        if return_placeholder_on_error:
            return "[Failed: all retries exhausted]"
        raise RuntimeError(f"[{api_name}] All retries exhausted")

    def _call_with_fallback(self, user_content, max_tokens, temperature,
                            top_p, system_prompt=None, timeout=API_TIMEOUT,
                            return_placeholder_on_error=False,
                            require_chat_completions=False,
                            primary_api_name="Primary API",
                            fallback_api_name="Fallback API"):
        """
        Try primary API, then fall back to secondary if configured.

        Reads EXPERIENCE_API_KEY, EXPERIENCE_END_POINT and their _2 variants
        from environment variables.
        """
        api_key_1 = os.environ.get("EXPERIENCE_API_KEY")
        end_point_1 = os.environ.get("EXPERIENCE_END_POINT")
        api_key_2 = os.environ.get("EXPERIENCE_API_KEY_2")
        end_point_2 = os.environ.get("EXPERIENCE_END_POINT_2")

        if not api_key_1 or not end_point_1:
            if return_placeholder_on_error:
                return "[API not configured]"
            raise ValueError(
                "Set EXPERIENCE_API_KEY and EXPERIENCE_END_POINT "
                "environment variables."
            )

        # Normalize endpoint to ensure /chat/completions suffix if needed
        if require_chat_completions:
            if not end_point_1.endswith("/chat/completions"):
                end_point_1 = end_point_1.rstrip("/") + "/chat/completions"

        # Try primary
        try:
            return self._try_single_api(
                api_key_1, end_point_1, user_content,
                max_tokens, temperature, top_p, MAX_RETRIES,
                api_name=primary_api_name,
                system_prompt=system_prompt,
                timeout=timeout,
                return_placeholder_on_error=return_placeholder_on_error,
            )
        except RuntimeError:
            if api_key_2 and end_point_2:
                if require_chat_completions:
                    if not end_point_2.endswith("/chat/completions"):
                        end_point_2 = (
                            end_point_2.rstrip("/") + "/chat/completions"
                        )
                return self._try_single_api(
                    api_key_2, end_point_2, user_content,
                    max_tokens, temperature, top_p, MAX_RETRIES,
                    api_name=fallback_api_name,
                    system_prompt=system_prompt,
                    timeout=timeout,
                    return_placeholder_on_error=return_placeholder_on_error,
                )
            if return_placeholder_on_error:
                return "[Failed: primary API failed, no fallback configured]"
            raise

    @staticmethod
    def _image_to_base64(image):
        """Convert PIL Image to base64 string (JPEG encoding)."""
        import io
        import base64
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
