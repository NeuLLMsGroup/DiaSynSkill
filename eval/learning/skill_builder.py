"""
Skill Builder — SOP (Standard Operating Procedure) Generation from Trajectories

Extracts structured, reusable Skill documents from agent trajectories using
LLM-based summarization and critique. Each Skill follows a 16-section format
covering disease knowledge, syndrome differentiation, risk screening, and
dialogue generation rules.

Key functions:
  - extract_trajectory_from_file: reads <trajectory> content from summary files
  - generate_skill_for_sample: produces a 12-section Raw Skill Fragment
  - merge_skills: consolidates multiple raw fragments into a final 16-section Skill

NOTE: Partial release. Full implementation including the merge pipeline,
refinement strategies, and skill-splitting logic available upon acceptance.
"""

import os
import re
from typing import List, Dict, Any, Optional


def extract_trajectory_from_file(sample_dir):
    """
    Extract <trajectory>...</trajectory> content from a sample's
    exp_summary_prompt.txt file, generated during the experience phase.
    """
    path = os.path.join(sample_dir, "exp_summary_prompt.txt")
    if not os.path.exists(path):
        return None

    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        match = re.search(
            r'<trajectory>(.*?)</trajectory>', content, re.DOTALL
        )
        if match:
            return match.group(1).strip()
    except Exception as e:
        print(f"  Warning: Error extracting trajectory from {path}: {e}")

    return None


def generate_skill_for_sample(sample_info, llm, args, ground_truth=""):
    """
    Generate a Raw Skill Fragment for one sample.

    The LLM analyzes the trajectory against ground truth and produces a
    structured markdown document with 12 sections:

      1. Source quality summary
      2. Tool-use lessons
      3. Retained inquiry logic
      4. Retained disease knowledge
      5. Retained syndrome differentiation logic
      6. Retained similar-disease differentiation rules
      7. Retained risk screening rules
      8. Dynamic examination and multimodal rules
      9. Dialogue style patterns
      10. Candidate few-shot material
      11. Negative rules (prohibited behaviors)
      12. Merge notes

    Args:
        sample_info: Dict with question_id, sample_dir, and rollout results
        llm: ExperienceLLM instance for API calls
        args: Command-line arguments
        ground_truth: Gold-standard diagnosis for correctness verification

    Returns:
        Dict with keys: sample_id, success, skill_content, error
    """
    question_id = sample_info['question_id']
    sample_dir = sample_info['sample_dir']

    result = {
        'sample_id': question_id,
        'success': False,
        'skill_content': '',
        'error': None,
    }

    trajectory = extract_trajectory_from_file(sample_dir)
    if not trajectory:
        result['error'] = "No trajectory content found"
        return result

    try:
        # Prompt template imported from prompts.skill_prompts in full release
        # GENERATE_SKILL_PROMPT guides the LLM to extract actionable SOPs
        from prompts.skill_prompts import GENERATE_SKILL_PROMPT

        prompt = GENERATE_SKILL_PROMPT.format(
            trajectory=trajectory,
            ground_truth=ground_truth or "[NOT PROVIDED]",
        )
        skill_content = llm.chat(prompt)

        if skill_content:
            # Strip markdown code fences from LLM response
            skill_content = re.sub(r'^```markdown\n', '', skill_content)
            skill_content = re.sub(r'^```\n', '', skill_content)
            skill_content = re.sub(r'\n```$', '', skill_content)
            skill_content = skill_content.strip()

            skill_file = os.path.join(sample_dir, 'skill_raw.md')
            with open(skill_file, 'w', encoding='utf-8') as f:
                f.write(skill_content)

            result['success'] = True
            result['skill_content'] = skill_content
        else:
            result['error'] = "LLM returned empty skill content"
    except Exception as e:
        result['error'] = str(e)

    return result


def merge_skills(raw_skills, llm, max_per_batch=5):
    """
    Merge multiple Raw Skill Fragments into a consolidated 16-section Skill.

    Strategy: when the number of fragments exceeds max_per_batch, a
    hierarchical merge is performed — batches of ≤5 are merged into
    intermediate results, which are then merged in a final pass.

    NOTE: Full merge implementation available in complete release.
    """
    # Full implementation in complete release
    pass
