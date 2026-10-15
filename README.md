<h1 align="center">DiaSynSkill: Skill-Guided Synthesis of Multimodal Diagnostic Dialogues</h1>

<p align="center">
  <a href="https://anonymous.4open.science/r/DiaSynSkill/"><img src="https://img.shields.io/badge/Paper-Anonymous%20Submission-b31b1b" alt="Paper"></a>
  <a href="README.md#method">🛠️ Method</a>
  <a href="README.md#experiments">📊 Experiments</a>
  <a href="README.md#examples">🧩 Examples</a>
</p>

<p align="center">
  <a href="README.md#overview">📖 Overview</a> •
  <a href="README.md#method">🛠️ Method</a> •
  <a href="README.md#dataset">🥸 Dataset</a> •
  <a href="README.md#experiments">📊 Experiments</a>
</p>

<a id="overview"></a>

## 📖 Overview

**DiaSynSkill** is a skill-guided framework for synthesizing multi-turn diagnostic dialogues from multimodal real-world Traditional Chinese Medicine (TCM) clinical cases. Rather than generating conversations directly from model priors, DiaSynSkill extracts transferable diagnostic skills from agentic reasoning trajectories and uses them as procedural guidance for dialogue synthesis.

The framework combines **Agentic Trajectory Collection**, **Trajectory Assessment and Skill Distillation**, a **Multi-Disease Clinical Skill Library**, and a **Multimodal Multi-Turn Doctor–Patient Dialogue Dataset**. The resulting skills encode information acquisition patterns, syndrome differentiation logic, contrastive diagnosis strategies, and evidence-grounded generation constraints.

<p align="center">
  <img src="assets/dialogue-example.png" width="90%" alt="Examples of multimodal multi-turn diagnostic dialogues">
</p>
<p align="center"><em>Examples of multimodal doctor–patient diagnostic dialogues synthesized by DiaSynSkill.</em></p>

<a id="method"></a>

## 🛠️ Method

<p align="center">
  <img src="assets/framework.png" width="100%" alt="Overview of the DiaSynSkill framework">
</p>
<p align="center"><em>Overview of the DiaSynSkill framework.</em></p>

DiaSynSkill follows a four-component workflow:

1. **Agentic trajectory collection**: a ReAct-style TCM agent uses clinical records and external medical tools to generate structured diagnostic strategies and interaction trajectories.
2. **Trajectory assessment and skill distillation**: a TCM practitioner agent evaluates trajectories from multiple dimensions and abstracts reusable case-level diagnostic skills.
3. **Multi-disease skill library construction**: case-level skills are aligned and consolidated into disease-level skills covering recurrent inquiry routines, syndrome reasoning, differential diagnosis, and evidence constraints.
4. **Skill-guided dialogue synthesis**: the disease-level skill is retrieved as a structured prior for generating multimodal, multi-turn doctor–patient dialogues.

The released implementation is organized in [`eval/`](eval/), including the inference orchestration, experience learning, skill construction, tool registration, and context utilities.

<a id="dataset"></a>

## 🥸 Dataset

DiaSynSkill generates two complementary resources:

- **Skill Library**: 426 diagnostic skills organized across 35 TCM diseases.
- **Multimodal Multi-Turn Doctor–Patient Dialogue Dataset**: 2,491 dialogue samples spanning five TCM departments.

<p align="center">
  <img src="assets/disease-sunburst-leader-compact-combined.png" width="58%" alt="Disease and department distribution">
</p>
<p align="center"><em>Disease and department distribution of the synthesized resources.</em></p>

The repository also includes representative diagnostic skill documents in [`examples/skills/`](examples/skills/) and generated dialogue examples in [`examples/dialogues/`](examples/dialogues/).

<a id="experiments"></a>

## 📊 Experiments

We evaluate DiaSynSkill with general multi-dimensional dialogue quality metrics, TCM-specific diagnostic metrics, pairwise comparison, and downstream diagnostic response modeling. The evaluation compares DiaSynSkill with strong MLLM baselines and two ablations that remove the induced skills and tool-supported trajectory process.

### Pairwise comparison

<p align="center">
  <img src="assets/pairwise-comparison.png" width="78%" alt="Pairwise comparison results">
</p>
<p align="center"><em>Pairwise comparison results under general LLM-based and clinical practitioner evaluation.</em></p>

DiaSynSkill receives the highest preference across pneumonia and stroke comparisons, with consistent trends from both automated judges and clinical TCM practitioners.

### Automatic evaluation

The following scores are from DeepSeek-V3.2 evaluation. **General** aggregates factuality, conciseness, fluency, and naturalness; **TCM** aggregates clinical factuality, diagnostic expertise, dialogue integrity, and communication quality.

| Disease | Method | General total | TCM total |
|---------|--------|--------------:|----------:|
| Pneumonia | DiaSynSkill | **93.65** | **91.54** |
| Pneumonia | w/o skill | 92.95 | 90.51 |
| Pneumonia | w/o skill & tool | 92.45 | 84.37 |
| Stroke | DiaSynSkill | **93.60** | **91.01** |
| Stroke | w/o skill | 92.25 | 89.86 |
| Stroke | w/o skill & tool | 90.80 | 89.28 |

Compared with direct prompting of advanced MLLMs, DiaSynSkill shows its largest gains on diagnostic expertise, dialogue integrity, and communication quality.

### Downstream diagnostic response modeling

<p align="center">
  <img src="assets/tcm_agent_accuracy_v4.png" width="78%" alt="Downstream diagnostic response accuracy">
</p>
<p align="center"><em>Accuracy comparison for TCM diagnostic response models.</em></p>

The downstream model trained with DiaSynSkill-generated dialogue data achieves **77%** accuracy in the reported comparison.

<a id="examples"></a>

## 🧩 Examples

### Diagnostic inquiry skills

| Skill | Topic |
|-------|-------|
| [Stroke](examples/skills/skill_01_stroke.md) | Qi-Yin deficiency with blood stasis |
| [Pneumonia](examples/skills/skill_02_pneumonia.md) | Phlegm-heat in the lung |
| [Diabetes](examples/skills/skill_03_diabetes.md) | Xiaoke with comorbidity |
| [Acute abdomen](examples/skills/skill_04_acute_abdomen.md) | Cholecystitis and appendicitis |
| [Chronic bronchitis](examples/skills/skill_05_bronchitis.md) | Phlegm-dampness |
| [Headache](examples/skills/skill_06_headache.md) | Intracranial mass |
| [Ovarian tumor](examples/skills/skill_07_ovarian_tumor.md) | Qi stagnation and blood stasis |
| [Trauma](examples/skills/skill_08_trauma.md) | Open wounds and fractures |
| [Parotid mass](examples/skills/skill_09_parotid_mass.md) | Phlegm nucleus |
| [Mycoplasma pneumonia](examples/skills/skill_10_mycoplasma.md) | Atypical cough |

### Generated dialogues

| Dialogue | Topic |
|----------|-------|
| [Headache](examples/dialogues/dialogue_01_headache.md) | Intracranial mass |
| [Cholecystitis](examples/dialogues/dialogue_02_cholecystitis.md) | Acute abdominal pain |
| [Pneumonia and cancer](examples/dialogues/dialogue_03_pneumonia_cancer.md) | Respiratory disease with comorbidity |
| [Stroke](examples/dialogues/dialogue_04_stroke.md) | Neurological deficits |
| [Appendicitis](examples/dialogues/dialogue_05_appendicitis.md) | Acute abdominal pain |
| [Diabetes](examples/dialogues/dialogue_06_diabetes.md) | Xiaoke with comorbidity |
| [Chronic bronchitis](examples/dialogues/dialogue_07_bronchitis.md) | Acute exacerbation |
| [Ovarian tumor](examples/dialogues/dialogue_08_ovarian_tumor.md) | Abdominal mass |
| [Trauma](examples/dialogues/dialogue_09_trauma.md) | Hand injury |
| [Mycoplasma pneumonia](examples/dialogues/dialogue_10_mycoplasma.md) | Persistent cough |

## 📁 Repository Structure

```text
.
├── assets/                         # Paper figures and experiment plots
├── eval/                           # Inference and skill construction code
│   ├── infer_api.py
│   ├── requirements.txt
│   ├── engine/
│   ├── learning/
│   ├── tools/
│   └── utils/
├── examples/
│   ├── skills/
│   └── dialogues/
└── README.md
```

## 🚀 Getting Started

Install the Python dependencies with:

```bash
python -m pip install -r eval/requirements.txt
```

The experience-generation client accepts an OpenAI-compatible chat completion service through environment variables:

```bash
export EXPERIENCE_MODEL_NAME="your-model-name"
export EXPERIENCE_API_KEY="your-api-key"
export EXPERIENCE_END_POINT="https://your-endpoint"
```

See [`eval/learning/llm_client.py`](eval/learning/llm_client.py) for request construction and [`eval/infer_api.py`](eval/infer_api.py) for inference and skill-accumulation entry points.

## 📄 Citation

```bibtex
@article{diasynskill,
  title   = {DiaSynSkill: Skill-Guided Synthesis of Multimodal Diagnostic Dialogues},
  author  = {Anonymous},
  journal = {匿名投稿},
  year    = {2026}
}
```
