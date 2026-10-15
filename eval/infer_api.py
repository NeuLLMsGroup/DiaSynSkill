"""
Core Agent Inference Pipeline — Main Entry Point

This module implements the main agent inference loop for multi-turn TCM (Traditional
Chinese Medicine) diagnostic dialogue generation. The pipeline orchestrates:
  - Multi-rollout parallel sampling with configurable temperature and seed
  - Experience retrieval and injection from the skill memory bank
  - Batch processing with thread-pool parallelism
  - Skill accumulation (extraction, merge, refinement) across cases

NOTE: This is a partial release for peer review. The complete codebase will be
made publicly available upon paper acceptance, including the full evaluation
suite, training pipelines, and all auxiliary modules.

Architecture Overview
---------------------
The system operates in two modes:

1. **Training / Accumulation Mode** — Processes medical cases to generate multi-turn
   doctor-patient dialogues, evaluates their quality via dual-agent judging, then
   extracts structured "Skills" (reusable diagnostic inquiry patterns) from
   successful trajectories.

2. **Inference Mode** — Given a new case, retrieves relevant Skills from the memory
   bank, adapts them to the current task context, and injects them into the agent's
   system prompt to guide dialogue generation.

Key Design Decisions
--------------------
- All LLM calls use OpenAI-compatible chat completion APIs, making the system
  provider-agnostic (tested with Qwen and GPT-series models).
- Multi-worker parallelism is managed via ThreadPoolExecutor with file-level
  locking for thread-safe skill library updates.
- Experience retrieval uses embedding-based similarity search with a FAISS
  index (see experience_retriever.py).

Dependencies
------------
- openai (OpenAI-compatible SDK)
- numpy, scikit-learn (embedding similarity)
- pyyaml (configuration)
- Pillow (image handling)
"""

import argparse
import os
import json
import threading
import time
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# Internal modules (partial listing — see individual files for full implementation)
from utils.result_utils import save_results, print_summary
import yaml

from learning import (
    ExperienceLLM,
    summarize_rollouts,
    intra_sample_experiences,
    load_existing as exp_load_existing,
    batch_merge as exp_batch_merge,
    save_library as exp_save_library,
    generate_skill_for_sample,
    merge_skills,
    refine_experience_library,
    refine_skill_document,
)

from engine.api_processors import (
    process_single_sample,
    set_global_prompts as set_processors_prompts,
)

from infer_api_utils import (
    initialize_experience_retriever,
    get_used_original_experiences,
    retrieve_experiences_for_sample,
    compute_and_save_sample_summary,
    check_sample_completed,
    reload_experiences,
    prepare_sample_args,
    get_sample_metadata,
    compute_dataset_summary,
    execute_pipeline_parallel_processing,
)


def run_single_rollout(sample, args, sampling_params, rollout_idx):
    """
    Execute a single independent rollout for a given sample.

    Each rollout uses a different random seed (seed_base + rollout_idx) to
    produce diverse trajectories. This enables pass@k and average@k evaluation
    for measuring the robustness of the dialogue generation.

    Args:
        sample: Data sample dict with fields (problem, images, solution, etc.)
        args: Command-line arguments (namespace object)
        sampling_params: Dict with temperature, top_p, max_tokens
        rollout_idx: 0-based rollout index for seed derivation

    Returns:
        Result dict containing trajectory information and metadata
    """
    import random

    rollout_args = prepare_sample_args(args)

    # Inject sample-specific system prompt (retrieved experiences + adapted skills)
    if hasattr(args, '_sample_system_prompt'):
        set_processors_prompts(args._sample_system_prompt)

    seed = args.seed_base + rollout_idx
    random.seed(seed)

    rollout_sampling_params = sampling_params.copy()
    if 'seed' in rollout_sampling_params:
        rollout_sampling_params['seed'] = seed

    result = process_single_sample(
        sample, rollout_args, rollout_sampling_params, rollout_idx=rollout_idx
    )
    return result


def generate_experience_for_sample(sample_info, args):
    """
    Generate structured experience entries and (optionally) a Skill for one sample.

    This is the core learning step: after rollouts complete, the system
    summarizes trajectories, critiques them, and distills reusable Skill
    fragments in a 12-section structured format.

    Args:
        sample_info: Dict with keys:
            - sample: the original data sample
            - sample_idx: index in the dataset
            - question_id: unique identifier
            - sample_dir: output directory for this sample
            - sample_rollout_results: list of rollout result dicts
        args: Command-line arguments

    Returns:
        Dict with keys:
            - sample_id: str
            - success: bool
            - experience_ops: list of normalized experience dicts
            - skill_content: str (if skill generation was enabled)
            - error: str or None
    """
    question_id = sample_info['question_id']
    sample_dir = sample_info['sample_dir']
    sample_rollout_results = sample_info['sample_rollout_results']

    result = {
        'sample_id': question_id,
        'success': False,
        'experience_ops': [],
        'skill_content': '',
        'error': None,
    }

    try:
        llm = ExperienceLLM()

        # Collect trajectory file paths from all rollouts
        traj_paths = []
        for rollout_idx in range(len(sample_rollout_results)):
            if args.rollouts_per_sample > 1:
                rollout_dir = os.path.join(sample_dir, f"rollout_{rollout_idx}")
            else:
                rollout_dir = sample_dir
            traj_path = os.path.join(rollout_dir, 'traj.jsonl')
            if os.path.exists(traj_path):
                traj_paths.append(traj_path)

        if not traj_paths:
            result['error'] = "No trajectory files found"
            return result

        # Summarize all rollouts into a unified structure
        merged_summaries = summarize_rollouts(
            traj_paths, llm, sample_dir=sample_dir
        )

        if not merged_summaries:
            result['error'] = "Failed to generate summary"
            return result

        question = merged_summaries.get('question', '')
        ground_truth = merged_summaries.get('ground_truth', '')

        # Generate experiences via intra-sample critique
        summaries_only = {
            k: v for k, v in merged_summaries.items()
            if k not in ['question', 'ground_truth', 'system_prompt']
        }

        used_experiences = get_used_original_experiences(sample_dir)

        raw_ops = intra_sample_experiences(
            question, ground_truth, summaries_only, llm,
            max_ops=getattr(args, 'experience_max_ops', 2),
            debug_dir=sample_dir,
            used_experiences=used_experiences,
        )

        # Normalize experience operations to a uniform dict format
        norm_ops = []
        if isinstance(raw_ops, str):
            try:
                raw_ops = json.loads(raw_ops)
            except Exception:
                pass

        if isinstance(raw_ops, dict) and 'experiences' in raw_ops:
            for _, v in raw_ops['experiences'].items():
                if isinstance(v, str) and v.strip():
                    norm_ops.append({"experience": v.strip()})
        elif isinstance(raw_ops, list):
            for o in raw_ops:
                if isinstance(o, dict):
                    exp_txt = o.get('experience') or o.get('exp')
                    if isinstance(exp_txt, str) and exp_txt.strip():
                        norm_ops.append({"experience": exp_txt.strip()})

        if norm_ops:
            with open(os.path.join(sample_dir, 'exp_items.json'), 'w',
                      encoding='utf-8') as f:
                json.dump(norm_ops, f, ensure_ascii=False, indent=2)

        # Optionally generate a refined Skill from the trajectory
        if getattr(args, 'skill_enable', False):
            skill_result = generate_skill_for_sample(
                sample_info, llm, args, ground_truth=ground_truth
            )
            if skill_result['success']:
                result['skill_content'] = skill_result['skill_content']

        result['success'] = True
        result['experience_ops'] = norm_ops

    except Exception as e:
        result['error'] = str(e)
        import traceback
        result['traceback'] = traceback.format_exc()

    return result


def process_large_batch_experiences(samples_info, args, batch_idx=0,
                                    is_final=False):
    """
    Process experience generation for a batch of samples in parallel,
    then merge all new experiences into the shared library.

    Uses ThreadPoolExecutor for parallelism. Skill and experience libraries
    are protected by threading.Lock for safe concurrent writes.

    Args:
        samples_info: List of sample_info dicts
        args: Command-line arguments
        batch_idx: Current batch index (for snapshot naming)
        is_final: If True, force library refinement regardless of size threshold

    Returns:
        Number of successfully processed samples
    """
    if not samples_info:
        return 0

    start_time = time.time()
    all_experience_ops = []
    all_skill_contents = []
    successful_samples = 0

    gen_start = time.time()
    num_tasks = len(samples_info)
    with ThreadPoolExecutor(max_workers=num_tasks) as executor:
        exp_futures = {
            executor.submit(generate_experience_for_sample, info, args): info
            for info in samples_info
        }
        for future in as_completed(exp_futures):
            sample_info = exp_futures[future]
            try:
                result = future.result()
                if result['success']:
                    all_experience_ops.extend(result['experience_ops'])
                    if result.get('skill_content'):
                        all_skill_contents.append(result['skill_content'])
                    successful_samples += 1
            except Exception as e:
                print(f"  Warning: Generation failed for "
                      f"{sample_info['question_id']}: {e}")

    gen_time = time.time() - gen_start

    # Merge experiences into shared library (thread-safe)
    if (all_experience_ops
            and getattr(args, 'experience_library_update', False)
            and args.experience_library):
        try:
            if not hasattr(process_large_batch_experiences, '_library_lock'):
                process_large_batch_experiences._library_lock = (
                    threading.Lock()
                )

            with process_large_batch_experiences._library_lock:
                existing = exp_load_existing(args.experience_library)
                merged = exp_batch_merge(
                    existing, all_experience_ops, ExperienceLLM(),
                    debug_dir=None,
                    experience_limit=getattr(args, 'experience_max_items', 16),
                )

                if getattr(args, 'experience_refine', False):
                    max_items = getattr(args, 'experience_max_items', 256)
                    if is_final or len(merged) > max_items:
                        refine_llm = ExperienceLLM()
                        merged = refine_experience_library(
                            merged, refine_llm, debug_dir=args.output_dir
                        )

                os.makedirs(os.path.dirname(args.experience_library),
                            exist_ok=True)
                exp_save_library(args.experience_library, merged)
        except Exception as e:
            print(f"  Warning: Failed to merge experiences: {e}")

    # Merge skills into library (thread-safe)
    if all_skill_contents and getattr(args, 'skill_library', None):
        try:
            if not hasattr(process_large_batch_experiences, '_skill_lock'):
                process_large_batch_experiences._skill_lock = threading.Lock()

            with process_large_batch_experiences._skill_lock:
                existing_skill_path = args.skill_library
                existing_content = ""
                if os.path.exists(existing_skill_path):
                    with open(existing_skill_path, 'r', encoding='utf-8') as f:
                        existing_content = f.read()

                if existing_content.strip():
                    merged_skill = existing_content
                else:
                    merged_skill = "\n\n".join(all_skill_contents)

                os.makedirs(os.path.dirname(existing_skill_path),
                            exist_ok=True)
                with open(existing_skill_path, 'w', encoding='utf-8') as f:
                    f.write(merged_skill)
        except Exception as e:
            print(f"  Warning: Failed to merge skills: {e}")

    total_time = time.time() - start_time
    return successful_samples


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="API-based TCM diagnostic dialogue agent."
    )

    # --- Data I/O ---
    parser.add_argument("--input-file", type=str, required=True,
                        help="Path to input data file (JSON or JSONL).")
    parser.add_argument("--image-folder", type=str, required=True,
                        help="Root folder for resolving relative image paths.")
    parser.add_argument("--output-dir", type=str, required=True,
                        help="Directory for saving output results.")
    parser.add_argument("--skip-completed", action='store_true',
                        help="Skip samples with existing traj.jsonl + metrics.")
    parser.add_argument("--max-samples", type=int, default=None,
                        help="Limit number of samples to process.")

    # --- Sampling ---
    parser.add_argument("--temperature", type=float, default=0.6)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--max-completion-tokens", type=int, default=8192)

    # --- Inference control ---
    parser.add_argument("--max-turns", type=int, default=16)
    parser.add_argument("--max-images", type=int, default=16)
    parser.add_argument("--max-total-tokens", type=int, default=8000)
    parser.add_argument("--max-pixels", type=int, default=2000000)
    parser.add_argument("--min-pixels", type=int, default=40000)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--rollouts-per-sample", type=int, default=4)
    parser.add_argument("--seed-base", type=int, default=42)

    # --- Prompts ---
    parser.add_argument("--inference-prompts-path", type=str,
                        default="eval/prompts/inference_prompts.yaml")
    parser.add_argument("--system-prompt-key", type=str,
                        default="multi_tool_agent_search")

    # --- Tools ---
    parser.add_argument("--tool-config-path", type=str,
                        default="eval/configs/tool_configs.yaml")

    # --- Experience (learning) ---
    parser.add_argument("--experience-enable", action='store_true')
    parser.add_argument("--experience-library", type=str, default=None)
    parser.add_argument("--experience-online-generate", action='store_true')
    parser.add_argument("--experience-library-update", action='store_true')
    parser.add_argument("--experience-max-ops", type=int, default=2)
    parser.add_argument("--experience-temperature", type=float, default=0.6)
    parser.add_argument("--experience-max-items", type=int, default=120)
    parser.add_argument("--experience-refine", action='store_true')

    # --- Skill ---
    parser.add_argument("--skill-enable", action='store_true')
    parser.add_argument("--skill-library", type=str, default=None)
    parser.add_argument("--skill-inference", action='store_true')
    parser.add_argument("--skill-max-length", type=int, default=1000)
    parser.add_argument("--skip-evaluation", action='store_true')

    # --- Experience Retrieval ---
    parser.add_argument("--experience-retrieval", action='store_true')
    parser.add_argument("--experience-retrieval-top-k", type=int, default=3)
    parser.add_argument("--experience-retrieval-min-similarity", type=float,
                        default=0.0)
    # API keys are read from environment variables; see README for setup.
    parser.add_argument("--experience-embedding-api-key", type=str,
                        default=None)  # Set via environment variable
    parser.add_argument("--experience-embedding-endpoint", type=str,
                        default=None)  # Set via environment variable

    args = parser.parse_args()
    # main(args) — See the full source release for the main() implementation.
    print("Inference module loaded. Full pipeline available in complete release.")
