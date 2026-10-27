# ClaimSense AI

AI-assisted review for personal auto physical-damage claims. The AI triages and scores; a human adjuster reviews and makes every decision. The model never approves or denies a claim — it ranks the queue and flags what deserves a closer look, with a full audit trail of every analysis and decision.

## What works today

- **Claims queue & review workspace** — React frontend over a FastAPI backend and PostgreSQL: claim facts, AI analysis, evidence, and the adjuster decision on one screen.
- **ML fraud scoring** — a RandomForest trained on 15,420 historical claims (Kaggle `fraud_oracle`), one-hot encoded to 123 features. The decision threshold is set to **0.20, deliberately**: at the textbook 0.50 the model catches almost no fraud (recall 0.04). At 0.20 it catches ~74% of fraud and flags about 1 in 4 claims for human review (precision 0.17) — the right trade when a person makes the final call. The score is blended 50/50 with transparent rules (model version `rules-v0.1+rf-v1`).
- **Rule-based severity & priority** — an ML severity model was trained and evaluated (accuracy 0.35) and **rejected**: the severity labels don't separate on the available features (the median Total Loss claim sits between Minor and Major), so a model's confident wrong answer would be worse than honest rules. The experiment is kept in `data/scripts/train_severity.py` as the record of that decision.
- **Document evidence pipeline** — upload PDF/PNG/JPG up to 25MB per claim. Files are SHA-256 checksummed; an exact duplicate is refused (HTTP 409). Documents land in storage with extraction status `pending` and are listed on the claim's review page.
- **Adjuster decision loop** — recording a decision in the UI flips the claim to `decided`, with rationale required. Analyses, uploads, and decisions all write audit events.

## Stack

- **Backend:** Python, FastAPI, SQLAlchemy
- **Frontend:** React + TypeScript (Vite)
- **Database:** PostgreSQL + pgvector (Docker)
- **ML:** scikit-learn (RandomForest), joblib model bundle with the serving threshold and feature columns versioned together

## Run it locally

Order matters: database first, backend second, frontend last.

```bat
:: 1. Start Docker Desktop and wait for "Engine running", then:
docker compose up -d db

:: 2. Backend — run from the backend folder
cd backend
python -m uvicorn app.main:app --reload
:: API docs: http://localhost:8000/docs

:: 3. Frontend — run from the frontend folder, in a second terminal
cd frontend
npm run dev
:: App: http://localhost:5173/
```

Leave each server's terminal open — closing one stops that part of the stack.

## Training data

Public Kaggle datasets: `shivamb/vehicle-claim-fraud-detection` (fraud model) and `buntyshah/auto-insurance-claims-data` (severity experiment). Raw data and trained model files are git-ignored; training scripts live in `data/scripts/`.

## Roadmap

Deploying to Azure: FastAPI on Azure Container Apps, PostgreSQL Flexible Server, documents in Azure Blob Storage, the React build on Azure Static Web Apps, and the LLM features — document extraction, claim summaries, content safety — on Microsoft Foundry. The scikit-learn fraud model ships inside the API container; Foundry covers the language-model parts.
