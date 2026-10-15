"""
Processor Functions for Multi-Turn TCM Diagnostic Dialogue Generation

This module contains the core dialogue generation logic:
  - Stage 1: Generate diagnostic inquiry strategies (3 disease directions)
  - Stage 2: Generate full multi-turn doctor-patient dialogues (8-12 rounds)
  - Agent 2a: Trajectory quality evaluation (5 dimensions, 50 points)
  - Agent 2b: Dialogue quality evaluation (9 dimensions, 50 points)

The pipeline follows a ReAct (Reasoning + Acting) pattern: the agent
reasons about the case, optionally calls knowledge-retrieval tools,
generates dialogue turns, and receives dynamic examination results.

NOTE: This is a PARTIAL release showing the processor architecture and
key helper functions. Full prompt templates and the complete agent loop
are available upon paper acceptance. All API keys and endpoints are
read from environment variables — no credentials are hard-coded.
"""

import os
import json
import re
import threading

# ---- Global file-write lock ----
# Protects concurrent writes to the shared SKILL.md and raw_skills/ directory
# when multiple worker threads process samples in parallel.
_skill_file_lock = threading.Lock()

from utils.context_utils import process_image, pil_to_base64_data_uri
from utils.context_utils import estimate_tokens
from utils.llm_judger import compute_score
from utils.result_utils import save_trajectory
from search.tree import SearchNode

# Global system prompt, set once at pipeline initialization
SYSTEM_PROMPT = ""


def set_global_prompts(system_prompt):
    """
    Set the global system prompt used by all downstream processor functions.

    Called once at pipeline startup and may be re-called when experiences
    or adapted skills are injected for a specific sample.
    """
    global SYSTEM_PROMPT
    SYSTEM_PROMPT = system_prompt


# =====================================================================
# Helper: Extract Final Dialogue from Message History
# =====================================================================

def _extract_final_ai_content(messages):
    """
    Scan all AI messages in the conversation history and extract the
    complete multi-turn dialogue block.

    The dialogue is bounded by the markers:
        【TCM Diagnostic Multi-Turn Dialogue】 ... 【Diagnostic Summary】

    This function searches across all content sources (content,
    reasoning_content, additional_kwargs) to handle variability in
    how different LLM providers structure their response objects.
    """
    all_text = []
    for msg in reversed(messages):
        if not (hasattr(msg, 'type') and msg.type == 'ai'):
            continue

        sources = [msg.content]
        rc = getattr(msg, 'reasoning_content', None)
        if rc:
            sources.append(rc)

        # Additional kwargs may contain provider-specific fields
        ak = getattr(msg, 'additional_kwargs', {})
        from operator import itemgetter
        for val in ak.values():
            if isinstance(val, str):
                sources.append(val)

        combined = "\n".join(s for s in sources if s)
        all_text.append(combined)

    full_text = "\n".join(all_text)

    # Extract dialogue block via regex
    pattern = r'(?:【中医疾病诊断多轮对话】|【TCM Diagnostic Multi-Turn Dialogue】)(.*?)(?:【诊断总结】|【Diagnostic Summary】)'
    match = re.search(pattern, full_text, re.DOTALL)
    if match:
        return match.group(0).strip()

    # Fallback: return last meaningful AI content
    for t in all_text:
        if t.strip():
            return t.strip()[:8000]

    return ""


# =====================================================================
# Stage 1: Inquiry Logic Generation
# =====================================================================
# The stage1 prompt instructs the LLM to:
#   1. Identify 3 candidate TCM disease directions from the case
#   2. For each direction, produce a 8-10 step inquiry logic chain
#      (using "→" as the step connector)
#   3. Mandatory steps include: specialty inquiry, etiology, core
#      symptoms, TCM syndrome differentiation, similar-disease
#      differentiation, risk screening, and final diagnosis
#
# Full prompt text: ~55 lines, available in the complete release.
# See prompts/consultation_prompts.py for the stage1_system and
# stage1_msg templates.


# =====================================================================
# Stage 2: Multi-Turn Dialogue Generation
# =====================================================================
# Takes the inquiry logic from Stage 1 + case data and generates
# 8-12 rounds of doctor-patient dialogue ending with a structured
# 【Diagnostic Summary】 containing:
#   - TCM disease diagnosis
#   - Core syndrome type
#   - Key evidence basis (5-6 items)
#   - Similar-disease differentiation results
#   - Risk screening results
#   - Multimodal data verification results
#
# Full prompt text: ~85 lines, available in the complete release.


# =====================================================================
# Agent 2: Dual-Agent Quality Evaluation
# =====================================================================
# Agent 2a (Trajectory Judge, 50 pts): evaluates tool-call compliance,
#   necessity, reasoning completeness, evidence use, and internal
#   consistency of the agent's reasoning trace.
#
# Agent 2b (Dialogue Judge, 50 pts): evaluates inquiry logic adherence,
#   TCM professionalism, factual consistency, information completion,
#   similar-disease differentiation, risk screening, multimodal handling,
#   naturalness, and diagnostic summary quality.
#
# Combined score ≥ 60/100 is considered "passed".
# Full prompt texts: see judge_agent.py in the complete release.
