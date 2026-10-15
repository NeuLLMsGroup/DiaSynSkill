"""
Trajectory Summarization Module

Summarizes multi-turn agent trajectories (ReAct loops) into structured
text for downstream experience extraction and skill building.

Key responsibilities:
  - Parse traj.jsonl files (one JSON record per turn)
  - Generate per-image captions via multimodal LLM
  - Merge multiple rollouts into a unified summary
  - Produce structured output with question, ground truth, and per-turn analysis

NOTE: Partial release. The full implementation with multi-rollout cross-
comparison and visual grounding is available upon paper acceptance.
"""

import os
import json
import re
import time
from pathlib import Path
from typing import Optional, Dict, List, Union, Any
from PIL import Image

from .llm_client import ExperienceLLM
from .multimodal_analysis import generate_image_captions


# ---- Constants ----

MAX_RETRIES = 3
MAX_TOKENS = 8192  # max tokens for trajectory summarization


def _normalize_traj_paths(traj_paths):
    """Normalize trajectory path input to a list of paths."""
    if isinstance(traj_paths, str):
        return [traj_paths]
    return list(traj_paths) if traj_paths else []


def _scan_all_images(sample_dir):
    """
    Scan a sample directory for all image files (tool outputs,
    search results, original case images) across both the top-level
    and per-rollout subdirectories.

    Returns a dict mapping caption_key to metadata including file_path,
    rollout_dir, and whether the image is an original case image.
    """
    sample_path = Path(sample_dir)
    if not sample_path.exists() or not sample_path.is_dir():
        return {}

    image_map = {}

    # Scan top-level
    for img_file in sample_path.glob("*"):
        if img_file.is_file() and img_file.suffix.lower() in (
            '.jpg', '.jpeg', '.png'
        ):
            image_map[img_file.name] = {
                "file_path": img_file,
                "rollout_dir": "",
                "is_original": img_file.name.startswith("original_image"),
            }

    # Scan rollout_X subdirectories
    for item in sample_path.iterdir():
        if item.is_dir() and item.name.startswith("rollout_"):
            for img_file in item.glob("*"):
                if img_file.is_file() and img_file.suffix.lower() in (
                    '.jpg', '.jpeg', '.png'
                ):
                    key = f"{item.name}/{img_file.name}"
                    image_map[key] = {
                        "file_path": img_file,
                        "rollout_dir": item.name,
                        "is_original": False,
                    }

    return image_map


def summarize_rollouts(traj_paths, llm, sample_dir=""):
    """
    Produce a unified summary from one or more trajectory files.

    Parses each traj.jsonl, collects turn-level (Observation, Thought,
    Action, Result) data, generates image captions where needed, and
    sends the combined structured data to an LLM for summarization.

    Args:
        traj_paths: list of paths to traj.jsonl files
        llm: ExperienceLLM instance
        sample_dir: root directory for the sample (for image resolution)

    Returns:
        Dict with keys: question, ground_truth, system_prompt,
        and per-rollout summary sections.
        Returns empty dict on failure.
    """
    # Full implementation in complete release
    if not traj_paths:
        return {}

    # Parse all trajectories, extract turns, generate captions,
    # and produce a merged summary.
    # See the complete release for the full pipeline.
    return {}
