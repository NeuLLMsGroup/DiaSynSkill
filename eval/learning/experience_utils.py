"""
Experience Utilities — I/O and Formatting Helpers

Provides functions for loading, saving, and formatting experience entries
from the JSON-based memory bank.

NOTE: Partial release. Full implementation with embedding caching and
FAISS index construction available upon paper acceptance.
"""

import os
import json
import base64
import io
from typing import Dict
from PIL import Image


# ---- Image Encoding ----

def image_to_base64(image):
    """Convert a PIL Image to a base64-encoded JPEG string."""
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')


# ---- Experience Library I/O ----

def load_existing(path):
    """
    Load existing experiences from a JSON file.

    Supports two formats:
      1. {"experiences": {"E0": "...", "E1": "...", ...}}
      2. {"E0": "...", "E1": "...", ...}  (flat dict)

    Returns an empty dict if the file does not exist or is malformed.
    """
    try:
        data = json.load(open(path, "r", encoding="utf-8"))
        if isinstance(data, dict) and "experiences" in data:
            return data["experiences"]
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def save_library(path, experiences):
    """
    Save experiences dict to a JSON file in the standard format:
    {"experiences": { "E0": "...", "E1": "...", ... }}
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"experiences": experiences}, f, ensure_ascii=False, indent=2)


def load_experiences(path):
    """Convenience wrapper around load_existing."""
    if path and os.path.exists(path):
        return load_existing(path)
    return {}


def format_for_prompt(experiences, max_items=32):
    """
    Format experiences as a bulleted string for injection into system prompts.

    Each entry is prefixed with its ID (e.g., "- [E0] <text>").

    Args:
        experiences: Dict of {exp_id: exp_text}
        max_items: Cap on number of entries to include

    Returns:
        Formatted string ready for prompt concatenation, or "" if empty.
    """
    if not experiences:
        return ""

    items = list(experiences.items())[:max_items]
    bullets = "\n".join([f"- [{k}] {v}" for k, v in items])

    # INJECTION_HEADER is imported from prompts in the full release
    header = (
        "## Retrieved Experiences\n"
        "The following patterns were retrieved from the memory bank. "
        "Use them to guide your diagnostic reasoning:\n\n"
    )
    return header + bullets
