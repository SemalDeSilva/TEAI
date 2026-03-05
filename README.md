# TEAI – Tea Expert AI Platform

TEAI (Tea Expert AI) is a multi-module artificial intelligence platform designed to support *end-to-end quality assessment and decision-making in the tea industry*.  

The system combines *computer vision, machine learning, reinforcement learning and sensor data* to replicate and enhance the work of human tea tasters, field supervisors and factory managers.

This repo is organised around *four main components*, each owned by one team member:

1. Vision-based Tea Taster (adjective prediction + RL feedback)  
2. Plucking Quality Grading (2 leaves + 1 bud → Best / Best-Below / Poor)  
3. Withering Moisture Estimation & Optimal Withering Time Suggestion  
4. Auction Price Prediction & Foreign Particle Detection

---

## 1. Component 1 – Vision-Based Tea Taster (De Silva P.S - IT22223326)

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

## 2. Component 2 – Plucking Quality Grading (Shavinda G.M.V - IT22224248)

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

## 3. Component 3 – Withering Moisture & Optimal Withering Time (Sooriyaarachchi N.D - IT22254702)

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

## 4. Component 4 – Auction Price Prediction & Foreign Particle Detection (Liyanage S.N - IT22211996)

This member handles *two complementary sub-components* that use quality and process data to support *market decisions* and *safety/QC*.

### 4.1 Auction Price Prediction

*Goal:*  
Predict the *likely auction price* for a tea batch based on quality metrics and process parameters.

*Inputs may include:*

- Region, Estate, Grade, Exchange Rate (LKR/USD), Rainfall, Date / Seasonality  
- Historical auction data

*Outputs:*

- Predicted *price per kg*.
- Useful for:
  - Predicting auction bid prices
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

---

## Repository Structure (Backend + Components)

This repository is organised so **each component can be developed independently** by different team members, while still integrating through a single **FastAPI backend** running on the PC (the same machine that runs model inference). The **frontend can call each component separately** via its own API endpoint.

### Backend (FastAPI on PC)

```bash
TEAI/
└── backend/
    ├── app/
    │   ├── main.py                      # FastAPI entrypoint (mounts /api/v1)
    │   ├── core/                        # config, logging, shared dependencies
    │   ├── api/v1/
    │   │   ├── router.py                # includes endpoint routers
    │   │   └── endpoints/
    │   │       ├── health.py            # GET /api/v1/health
    │   │       ├── modules.py           # GET /api/v1/modules (which components are enabled)
    │   │       ├── foreign_obj.py       # Foreign particle detection (detect + detect-and-act)
    │   │       ├── iot.py               # PC ↔ Arduino Serial control (stop/start/status)
    │   │       ├── taster.py            # Component 1 API
    │   │       ├── plucking.py          # Component 2 API
    │   │       ├── withering.py         # Component 3 API
    │   │       └── auction.py           # Component 4 API (price)
    │   ├── schemas/                    # Pydantic request/response models
    │   ├── services/                   # business logic (calls ML + logs + IoT actions)
    │   ├── ml/                         # model loaders + inference wrappers (.pt / .pkl)
    │   ├── serial_comm/                # USB Serial manager + STOP/START protocol
    │   ├── persistence/                # file logs now; optional DB layer later
    │   ├── utils/                      # helpers (images, ids, time)
    │   └── tests/                      # API tests (mock serial + mock ML)
    ├── models_store/                   # saved trained models by component/version
    │   ├── foreign_obj/v1/best.pt
    │   ├── taster/v1/...
    │   ├── plucking/v1/best.pt
    │   ├── withering/v1/model.pkl
    │   └── auction/v1/model.pkl
    ├── uploads/                        # optional image/frame storage
    ├── logs/                           # JSONL event logs + app logs
    ├── requirements.txt
    └── README.md
```

### Component-to-API mapping (for frontend integration)

| Component | API Endpoint (examples) | Owner updates here |
|---|---|---|
| Foreign Particle Detection + Conveyor Stop | `/api/v1/foreign-obj/*` + `/api/v1/iot/*` | `backend/app/ml/foreign_obj/`, `backend/app/services/foreign_obj_service.py` |
| Component 1 – Tea Taster | `/api/v1/taster/evaluate` | `backend/app/ml/taster/`, `backend/app/services/taster_service.py` |
| Component 2 – Plucking Quality | `/api/v1/plucking/grade` | `backend/app/ml/plucking/`, `backend/app/services/plucking_service.py` |
| Component 3 – Withering Prediction | `/api/v1/withering/predict` | `backend/app/ml/withering/`, `backend/app/services/withering_service.py` |
| Component 4 – Auction Price | `/api/v1/auction/predict` | `backend/app/ml/auction/`, `backend/app/services/auction_service.py` |

### Where to place your trained models
- Put **YOLO/PyTorch `.pt`** files in: `backend/models_store/<component>/v1/`
- Put **sklearn/CatBoost `.pkl`** files in: `backend/models_store/<component>/v1/`
- If your model needs extra assets (scalers/encoders/labels), keep them in the **same version folder**.

### Team workflow (simple rule)
Each member should:
1. Update only their component’s `ml/` wrapper and `services/` logic.
2. Keep API contracts stable (schemas in `backend/app/schemas/`).
3. Add a short note in `backend/README.md` describing how to run/test that component.
