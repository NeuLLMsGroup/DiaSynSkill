---
name: tcm-stroke-inquiry
description: >
  Multi-turn TCM diagnostic inquiry skill for Stroke (Zhongfeng) with
  Qi-Yin deficiency and blood stasis blocking collaterals. Generates
  8-12 round doctor-patient dialogues covering etiology, syndrome
  differentiation, similar-disease differentiation, and risk screening.
disease_category: Neurology (TCM)
syndrome_type: Qi-Yin Deficiency with Blood Stasis Obstructing Collaterals
source_cases: 16
---

# TCM Diagnostic Inquiry Skill: Stroke (Qi-Yin Deficiency, Blood Stasis)

## When to Use This Skill

Use this skill when:
- Generating a TCM multi-turn diagnostic dialogue for Stroke (Zhongfeng)
- The case involves hemiplegia, numbness, fixed stabbing pain, or speech impairment
- The case mentions Qi deficiency signs (fatigue, shortness of breath) combined with
  Yin deficiency signs (dry mouth, night sweats, soreness of the lower back)
- CT/MRI shows ischemic infarcts or encephalomalacia

## Skill Role

You are a TCM clinical inquiry expert specializing in **Stroke (Zhongfeng)** with
**Qi-Yin deficiency and blood stasis obstructing collaterals** syndrome.

## Required Inputs

- Patient case data (chief complaint, present illness, past history)
- Inquiry logic (optional; built-in standard logic used if empty)
- Dynamic examination results (optional; if empty, note data unavailability
  in the diagnostic summary without fabricating results)

## Core Disease Knowledge

- **Disease Definition**: Stroke (Zhongfeng, meridian pattern). Characterized by
  hemiplegia, unilateral numbness, deviated mouth and eyes, and speech difficulty,
  with clear consciousness. The disease is located in the brain collaterals and
  limb meridians.
- **Etiology**: Aging, depletion of Liver and Kidney, leading to Qi-Yin deficiency.
- **Pathomechanism**: Qi deficiency causes impaired propulsion; Yin deficiency
  causes vessel dryness. Blood circulation becomes stagnant, producing blood stasis
  that blocks brain collaterals and limb meridians.
- **Disease Nature**: Root deficiency (Qi-Yin deficiency) with branch excess
  (blood stasis).

## Standard Inquiry Logic

Stroke specialty inquiry → Etiology and disease progression inquiry →
Core symptom inquiry (hemiplegia, numbness, pain characteristics) →
Qi deficiency syndrome cluster differentiation →
Yin deficiency syndrome cluster differentiation →
Blood stasis sign differentiation →
Zang-fu pathomechanism targeted inquiry →
Similar-disease differentiation (Bi syndrome, Wei syndrome, visceral stroke) →
Critical condition and complication screening →
Inspection and palpation supplement →
Imaging examination verification →
Core syndrome comprehensive differentiation →
TCM disease diagnosis confirmation.

## Similar-Disease Differentiation

### Bi Syndrome (Arthralgia)
- **Why Confusable**: Both present with limb pain and numbness.
- **Key Differences**: Bi syndrome is typically joint-localized, aggravated by
  weather changes, without CT/MRI-confirmed brain lesions. Stroke has fixed
  neurological deficits and imaging evidence.

### Wei Syndrome (Flaccidity)
- **Why Confusable**: Both involve limb weakness.
- **Key Differences**: Wei syndrome manifests as flaccid weakness without
  numbness or pain, no imaging-confirmed brain lesions. Stroke typically
  presents with unilateral involvement.

## Risk Screening Rules

- **Intracranial Hypertension Risk**: Progressive worsening headache with
  projectile vomiting indicates elevated intracranial pressure — high risk.
- **Brain Herniation Warning Signs**: Sudden severe headache, deteriorating
  consciousness, unilateral pupil dilation, limb convulsions — requires
  immediate emergency intervention.
- **Neurological Deficit Monitoring**: Document muscle strength grade,
  gait stability, speech clarity at each assessment.

## Output Format

Each dialogue must conclude with a structured diagnostic summary:
```
【Diagnostic Summary】
TCM Disease Diagnosis: ...
Core Syndrome Type: ...
Key Differentiation Evidence:
  1. ...
  2. ...
Similar-Disease Differentiation Results:
  1. ...
Risk Screening Results:
  1. ...
Multimodal Data Verification Results:
  1. ...
```
