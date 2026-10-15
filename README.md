<h1 align="center">DiaSynSkill: Skill-Guided Synthesis of Multimodal Diagnostic Dialogues</h1>

<p align="center">
  <a href="README.md#overview">📖 Overview</a> •
  <a href="README.md#method">🛠️ Method</a> •
  <a href="README.md#examples">🧩 Examples</a>
</p>

<a id="overview"></a>

## 📖 Overview

**DiaSynSkill** introduces a skill-guided framework for synthesizing multi-turn diagnostic dialogues in Traditional Chinese Medicine (TCM). The framework organizes diagnostic inquiry strategies as reusable, disease-oriented skills and applies them to multimodal clinical information, including medical text, imaging descriptions, and laboratory findings.

The synthesis process consists of two stages:

1. **Skill accumulation**: generate and evaluate diagnostic trajectories, extract reusable inquiry patterns, and organize them into disease-specific skills.
2. **Skill-guided inference**: retrieve relevant skills for a new case and use them to guide coherent, structured doctor–patient dialogue generation.

This repository accompanies the DiaSynSkill study and provides the released implementation materials and representative examples.

<a id="method"></a>

## 🛠️ Method


The released implementation is organized around the following components:

- **Dialogue inference**: orchestration of multi-turn diagnostic dialogue generation.
- **Experience learning**: generation, storage, retrieval, and refinement of diagnostic experience.
- **Skill construction**: extraction and consolidation of reusable inquiry strategies.
- **Tool and context utilities**: request processing, token estimation, image handling, and tool registration.

The main source files are located in [`eval/`](eval/), with representative skill and dialogue materials in [`examples/`](examples/).

<a id="examples"></a>

## 🧩 Examples

### Diagnostic inquiry skills

The [skill examples](examples/skills/) cover trigger conditions, disease knowledge, syndrome differentiation, inquiry sequences, differential diagnosis, risk screening, and dialogue requirements.

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

The [dialogue examples](examples/dialogues/) illustrate skill-guided inquiry sequences and structured diagnostic summaries across neurological, respiratory, abdominal, metabolic, gynecological, and trauma-related cases.

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
├── eval/
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

See [`eval/learning/llm_client.py`](eval/learning/llm_client.py) for the request format and [`eval/infer_api.py`](eval/infer_api.py) for the inference and skill-accumulation entry points.

## 📄 License

This project follows the MIT License.
