# TEAI – Tea Expert AI Platform

TEAI (Tea Expert AI) is a multi-module artificial intelligence platform designed to support *end-to-end quality assessment and decision-making in the tea industry*.  

The system combines *computer vision, machine learning, reinforcement learning and sensor data* to replicate and enhance the work of human tea tasters, field supervisors and factory managers.

This repo is organised around *four main components*, each owned by one team member:

1. Vision-based Tea Taster (adjective prediction + RL feedback)  
2. Plucking Quality Grading (2 leaves + 1 bud → Best / Best-Below / Poor)  
3. Withering Moisture Estimation & Optimal Withering Time Suggestion  
4. Auction Price Prediction & Foreign Particle Detection

---

## 1. Component 1 – Vision-Based Tea Taster (Member 1)

*Goal:*  
Mimic a *human tea taster’s visual evaluation* by analysing tea leaf/powder images and generating *descriptive adjectives* and quality notes (e.g. “more blackish with slight reddish note, good twist”).

*Key ideas:*

- Use *computer vision / deep learning* to extract:
  - Colour characteristics (blackish, brownish, reddish notes, brightness, uniformity)
  - Texture and twist of the leaf or grain
  - Visual defects or irregularities (uneven colour, flakes, etc.)
- Map these features to *taster-style adjectives* and qualitative outputs.

*Reinforcement learning loop:*

- A *human tea taster* (ground truth expert) reviews the system’s output.
- If the machine’s description is *aligned* with the taster’s judgement → reinforce current model behaviour.
- If the output is *not accurate*:
  - Feedback is used as a *reward/penalty signal*.
  - A *reinforcement learning (RL) layer* updates the model/policy to gradually match expert preferences.
- Over time, the model becomes closer to a *digital tea taster assistant* that learns directly from expert corrections.

*Typical outputs:*

- Adjective-style descriptions (e.g. “well-twisted, blackish grade, slight reddish hint”).
- A visual quality score or class (e.g. High / Medium / Low visual appearance).

---

## 2. Component 2 – Plucking Quality Grading (Member 2)

*Goal:*  
Evaluate *tea plucking quality* based on the classic standard *“two leaves and one bud”*, and classify each sample into:

- *Best*
- *Best-Below*
- *Poor*

*Industrial context:*

- In real factories, large quantities (e.g. *1000 kg*) are collected.
- A *sample batch* (e.g. *250 samples*) is taken.
- Supervisors manually categorise samples into Best / Best-Below / Poor.
- This component aims to *automate* that using vision and a conveyor system.

*System behaviour:*

- Tea samples are *placed on a conveyor* under a camera.
- The model:
  - Detects *buds* and *leaves* in each sample.
  - Counts combinations like *“2 leaves + 1 bud”*.
- Classification logic (example):

  - *Best* – Ideal combinations (e.g. 1 bud + 2 young leaves).
  - *Best-Below* – Slightly over-plucked but still acceptable quality.
  - *Poor* – Over-plucked, coarse leaves or wrong combinations.

*Output example:*

- Out of *250 samples*, system predicts:
  - *200* → Best  
  - *35* → Best-Below  
  - *15* → Poor  

This gives the factory a *quantitative plucking quality report* for each batch.

---

## 3. Component 3 – Withering Moisture & Optimal Withering Time (Member 3)

*Goal:*  
Estimate *moisture content* during the *withering stage* and suggest *optimal withering duration* under current environmental conditions.

*Industrial background:*

- Fresh tea leaves have a high *water content*.
- During *withering, water evaporates and **weight drops*.
- Correct moisture level is critical for *flavour, aroma and processing quality*.

*What this component does:*

- Uses:
  - *Weight drop data* (before vs during vs after withering)
  - *Images* of the withering leaves
  - *Environmental parameters* (temperature, humidity, airflow, etc. – if available)
- Trains a model to:
  - Estimate *current moisture content* from these inputs.
  - Predict *how long* it will take to reach target moisture.

*Example model behaviour:*

- Input: early stage *unwithered leaf image* + initial weight and environment.
- Output:
  - “Estimated moisture: 74%”
  - “Target moisture: 55%”
  - “Recommended withering time: ~10 hours under current conditions”

*Benefits:*

- Helps supervisors avoid *under-withering* or *over-withering*.
- Supports more *consistent quality* and *energy-efficient* withering decisions.

---

## 4. Component 4 – Auction Price Prediction & Foreign Particle Detection (Member 4)

This member handles *two complementary sub-components* that use quality and process data to support *market decisions* and *safety/QC*.

### 4.1 Auction Price Prediction

*Goal:*  
Predict the *likely auction price* for a tea batch based on quality metrics and process parameters.

*Inputs may include:*

- Visual quality scores (from Components 1 & 2)  
- Withering characteristics (from Component 3)  
- Grade, origin, factory, season  
- Historical auction data

*Outputs:*

- Predicted *price per kg* or *price band*.
- Useful for:
  - Planning production
  - Negotiating with buyers
  - Comparing batches and optimising quality for target markets.

---

### 4.2 Foreign Particle Detection

*Goal:*  
Detect *foreign objects* mixed with tea during *final manufacturing / packing*, such as:

- Threads / fibres  
- Insects or animal parts (e.g. gecko tail)  
- Plastic pieces, stones, etc.

*System behaviour:*

- Camera is positioned near the *end of the production line*.
- The model:
  - Scans images for *non-tea objects*.
  - Flags suspicious regions.
- Potential actions:
  - Trigger an *alert*.
  - Stop the conveyor (in a real deployment).
  - Log images for review.

*Impact:*

- Improves *food safety* and *export compliance*.
- Reduces *customer complaints* and risk of *rejected shipments*.

---

## Project Structure (Suggested)

```bash
TEAI/
│
├── component_1_tea_taster/          # Vision + adjectives + RL feedback
│   ├── data/
│   ├── models/
│   └── notebooks/
│
├── component_2_plucking_quality/    # 2 leaves + 1 bud grading
│   ├── data/
│   ├── models/
│   └── conveyor_pipeline/
│
├── component_3_withering_moisture/  # Moisture + optimal withering time
│   ├── data/
│   ├── models/
│   └── analysis/
│
├── component_4_price_fp/            # Auction price + foreign particle detection
│   ├── price_prediction/
│   └── foreign_particle_detection/
│
├── common_utils/
│   ├── image_processing.py
│   ├── data_preprocessing.py
│   └── evaluation_metrics.py
│
├── docs/
│   ├── architecture_diagram.png
│   └── component_overview.md
│
├── README.md
├── requirements.txt
└── LICENSE
