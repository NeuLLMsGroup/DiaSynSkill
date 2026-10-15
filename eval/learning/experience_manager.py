"""
Experience Manager — Skill Library Maintenance

Manages the lifecycle of the experience/skill memory bank:
  - Incremental insertion with similarity-based deduplication
  - Hierarchical merge (L1→L2→L3) with capacity control
  - Periodic low-score pruning
  - Skill refinement triggers

The memory bank uses a three-level hierarchy:
  L1 (per-sample): Raw Skill Fragments extracted from single trajectories
  L2 (per-disease): Merged skills for a specific disease/syndrome
  L3 (cross-disease): Generalized diagnostic patterns applicable across diseases

NOTE: Partial release. Full implementation with embedding-based similarity
search and automatic merge triggering available upon paper acceptance.
"""

import os
import json
import re
import time
from typing import Optional, Dict, List, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from .llm_client import ExperienceLLM
from .experience_retriever import ExperienceRetriever


# ---- Constants ----

MAX_RETRIES = 3

# Similarity thresholds for merge triggers
SIMILARITY_THRESHOLD = 0.70         # trigger merge when cosine similarity ≥ this
SIMILARITY_THRESHOLD_REDUCTION = 0.60  # more aggressive threshold for compression

# Retrieval configuration
TOP_K_SIMILARITY_SEARCH = 10  # candidates to retrieve for similarity check

# Capacity limits
L1_CAPACITY = 200   # max raw fragments per disease category
L2_CAPACITY = 100   # max merged skills per disease category
SAFETY_MULTIPLIER = 1.2  # force compression when exceeded


def _strip_markdown_code_blocks(text):
    """Remove markdown code fence wrappers from LLM responses."""
    if "```" not in text:
        return text.strip()
    parts = text.split("```")
    if len(parts) > 2:
        return parts[2].strip()
    return (parts[0].strip() if parts else text).strip()


def _max_exp_id(exp_dict, default=0):
    """Return the maximum numeric suffix among experience IDs (E0, E1, ...)."""
    nums = []
    for k in exp_dict:
        if k.startswith("E") and len(k) > 1 and k[1:].isdigit():
            nums.append(int(k[1:]))
    return max(nums, default=default)


class ExperienceMemoryProvider:
    """
    Manages the experience memory bank with embedding-based retrieval
    and similarity-aware merge operations.

    Wraps ExperienceRetriever for embedding functionality and provides
    methods for batch insertion, deduplication, and library refinement.
    """

    def __init__(self, experiences, retriever=None):
        """
        Args:
            experiences: Dict of {exp_id: exp_text}
            retriever: Optional ExperienceRetriever instance
        """
        self.experiences = experiences
        self.retriever = retriever

    # Full implementation with embedding caching, merge triggering,
    # and hierarchical consolidation available in the complete release.
