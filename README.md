# SIFSentinel

### Detect the precursor. Understand the barrier. Prevent the event.

SIFSentinel is an AI/NLP-powered safety intelligence platform designed to identify **Serious Injury & Fatality (SIF) precursors** hidden inside free-text safety reports.

It transforms unstructured unsafe-act, unsafe-condition, near-miss and incident reports into actionable intelligence by combining:

- SIF-potential classification
- precursor extraction
- IOGP Life-Saving Rule mapping
- barrier and barrier-failure analysis
- risk and priority scoring
- semantic similarity search
- interactive safety intelligence dashboards

SIFSentinel was developed as a prototype for **Smart India Hackathon Problem Statement 26165** from Oil India Limited.

---

## Problem

Safety organizations receive large volumes of free-text reports describing unsafe acts, unsafe conditions, near misses and incidents.

Traditional review processes often rely on periodic manual triage, making it difficult to continuously identify the smaller subset of observations that may contain **serious injury or fatality potential**.

SIFSentinel addresses this by automatically analyzing safety reports and surfacing the precursor and barrier information that can help HSE teams prioritize preventive action.

---

## Solution

SIFSentinel converts an unstructured safety report into structured safety intelligence.

```text
                    Safety Report
                         │
                         ▼
                Ingestion & Validation
                         │
                         ▼
                 SIF Classification
                         │
                ┌────────┴────────┐
                ▼                 ▼
        Precursor Extraction   LSR Mapping
                │                 │
                └────────┬────────┘
                         ▼
                Unified Intelligence
                         │
                         ▼
                 Risk / Priority
                         │
                         ▼
                  Embeddings
                         │
                         ▼
                PostgreSQL + pgvector
                         │
                         ▼
                Interactive Dashboard
```

---

## Key Capabilities

### 1. SIF Potential Detection

Automatically classifies safety reports into:

* SIF-potential
* Non-SIF-potential

The classifier is implemented as a prototype baseline for prioritization rather than a calibrated production probability estimator.

### 2. Precursor Intelligence

Extracts relevant safety precursor information from free-text reports, including:

* Activity
* Hazard
* Exposure
* Barrier
* Barrier failure

This helps move beyond simply identifying whether a report is high risk and provides context about **why** it may represent serious injury or fatality potential.

### 3. IOGP Life-Saving Rule Mapping

Reports are automatically mapped to relevant IOGP Life-Saving Rules:

1. Bypassing Safety Controls
2. Confined Space
3. Driving
4. Energy Isolation
5. Hot Work
6. Line of Fire
7. Safe Mechanical Lifting
8. Work Authorisation
9. Working at Height

### 4. Risk & Priority Scoring

SIFSentinel combines multiple signals to prioritize reports.

Reports are categorized into:

* Low
* Moderate
* High
* Critical

The resulting priority score is intended to help HSE teams focus attention on observations with stronger precursor and fatal-potential signals.

### 5. Semantic Similarity

SIFSentinel generates sentence embeddings and stores them in PostgreSQL using `pgvector`.

This enables users to find historically similar safety reports and identify recurring patterns.

For example:

```text
Current report
      ↓
Semantic embedding
      ↓
Vector similarity search
      ↓
Similar historical reports
```

### 6. Interactive Safety Dashboard

The dashboard provides visibility into:

* SIF potential
* High-priority reports
* Critical reports
* Activities
* Life-Saving Rule distribution
* Priority reports
* Individual report intelligence
* Similar historical reports

---

# Technology Stack

## Frontend

* Next.js
* React
* TypeScript
* Tailwind CSS

## Backend

* FastAPI
* Python
* SQLAlchemy
* PostgreSQL
* pgvector

## Machine Learning / NLP

* Python
* scikit-learn
* PyTorch
* sentence-transformers
* TF-IDF
* Logistic Regression
* BGE embeddings
* Heuristic NLP-based precursor extraction

## Infrastructure

* Docker
* Docker Compose
* PostgreSQL + pgvector

---

# System Architecture

SIFSentinel consists of four main services:

```text
┌──────────────────┐
│     Frontend     │
│     Next.js      │
│     Port 3000    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│     Backend      │
│     FastAPI      │
│     Port 8000    │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────┐
│   PostgreSQL + pgvector  │
│       Port 5433          │
└──────────────────────────┘
         ▲
         │
┌──────────────────┐
│    ML Worker     │
│ NLP + Risk +     │
│ Embeddings       │
└──────────────────┘
```

Uploaded datasets are processed asynchronously by the ML worker so that the web application remains responsive while analysis is running.

---

# Project Structure

```text
sifsentinel-final/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   ├── lib/
│   ├── Dockerfile
│   ├── package.json
│   └── package-lock.json
│
├── ml/
│   ├── models/
│   │   └── sif_baseline_v03.joblib
│   ├── pipeline/
│   │   ├── ingest.py
│   │   ├── validate.py
│   │   ├── load_reports.py
│   │   ├── classify_sif.py
│   │   ├── extract_precursors.py
│   │   ├── map_lsr.py
│   │   ├── unified.py
│   │   ├── risk.py
│   │   ├── persist.py
│   │   ├── generate_embeddings.py
│   │   └── worker.py
│   ├── training/
│   │   ├── training_dataset.csv
│   │   └── human_holdout_15.csv
│   ├── Dockerfile
│   ├── requirements.txt
│   └── __init__.py
│
├── tests/
│   └── fixtures/
│
├── data/
│   ├── incoming/
│   └── processed/
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

# Running with Docker

SIFSentinel is fully containerized.

For normal usage, the host machine only needs:

* Docker
* Docker Compose

You do **not** need to install Python, Node.js, npm, PostgreSQL, or a Python virtual environment locally.

## 1. Clone or copy the project

```bash
git clone <YOUR_GITHUB_REPOSITORY>
cd sifsentinel-final
```

You can also run the project directly from a copied project directory.

## 2. Configure environment variables

The repository includes:

```text
.env.example
```

Create the local environment file:

```bash
cp .env.example .env
```

The default configuration is suitable for local development and demonstration.

Example `.env`:

```env
POSTGRES_DB=sifsentinel
POSTGRES_USER=sifsentinel
POSTGRES_PASSWORD=sifsentinel

DATABASE_URL=postgresql+psycopg://sifsentinel:sifsentinel@postgres:5432/sifsentinel

EMBEDDING_MODEL=BAAI/bge-base-en-v1.5
SIF_MODEL_PATH=/workspace/models/sif_baseline_v03.joblib
```

> Never commit `.env` to GitHub. Use `.env.example` as the public configuration template.

## 3. Build and start the application

From the project root:

```bash
docker compose up -d --build
```

This starts:

```text
PostgreSQL + pgvector
        +
FastAPI backend
        +
ML/NLP worker
        +
Next.js frontend
```

## 4. Check the containers

```bash
docker compose ps
```

A successful deployment should show:

```text
postgres
backend
ml
frontend
```

PostgreSQL should report:

```text
healthy
```

## 5. Open the application

Frontend:

```text
http://localhost:3000
```

Backend:

```text
http://localhost:8000
```

Backend health check:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "sifsentinel-api"
}
```

---

# Docker Commands

## Start

```bash
docker compose up -d
```

## Rebuild and start

```bash
docker compose up -d --build
```

## Stop

```bash
docker compose down
```

`docker compose down` stops and removes the containers while preserving the PostgreSQL Docker volume.

## Stop and remove database data

```bash
docker compose down -v
```

> `docker compose down -v` removes the PostgreSQL Docker volume and therefore deletes persisted application data.

## View running services

```bash
docker compose ps
```

## View backend logs

```bash
docker compose logs -f backend
```

## View ML worker logs

```bash
docker compose logs -f ml
```

## View frontend logs

```bash
docker compose logs -f frontend
```

## View PostgreSQL logs

```bash
docker compose logs -f postgres
```

---

# Uploading Safety Reports

Once SIFSentinel is running:

1. Open `http://localhost:3000`
2. Navigate to **Upload Report**
3. Select a CSV dataset
4. Upload it
5. Monitor the processing stages
6. Open **Reports** when processing is complete

Uploaded datasets are processed automatically by the ML worker.

The pipeline is:

```text
CSV Upload
    ↓
Ingestion
    ↓
Validation
    ↓
Report Loading
    ↓
SIF Classification
    ↓
Precursor Extraction
    ↓
IOGP Life-Saving Rule Mapping
    ↓
Unified Intelligence
    ↓
Risk Analysis
    ↓
Persistence
    ↓
Embedding Generation
    ↓
Processing Complete
```

The frontend polls the processing job and reports the current stage to the user.

Runtime files are generated under:

```text
data/incoming/
data/processed/
```

These directories are intentionally kept free of committed datasets and generated outputs.

---

# Machine Learning

## SIF Classifier

The current baseline uses:

```text
TF-IDF (unigrams + bigrams)
              +
Logistic Regression
              +
Class balancing
```

The model uses report text fields such as:

* Description
* Nature
* Event

The current implementation is a prototype baseline intended for ranking and prioritization.

Certain outcome-derived fields are deliberately not used as model inputs or SIF labels in order to avoid direct leakage from outcomes into prediction.

## Embeddings

SIFSentinel uses:

```text
BAAI/bge-base-en-v1.5
```

to generate:

* 768-dimensional embeddings
* normalized vectors

These are stored in PostgreSQL with `pgvector` and used for semantic similarity search.

The model is downloaded automatically by the ML container when required, with Hugging Face model caching persisted through Docker.

---

# Data

SIFSentinel can ingest free-text safety datasets through the application.

The project contains development/training artifacts for the current prototype, but does not require a large runtime dataset to be bundled with the application.

Public OSHA safety data may be used for development and validation of the prototype.

> Public OSHA data should not be represented as Oil India Limited proprietary data.

The intended production use case is ingestion of OIL's own unsafe-act, unsafe-condition, near-miss and incident reports.

---

# API

Selected API endpoints include:

```text
GET  /health

GET  /reports
GET  /reports/{report_id}
GET  /reports/{report_id}/analysis
GET  /reports/{report_id}/similar

POST /datasets/upload
GET  /datasets/{dataset_id}/status

GET  /analytics/overview
GET  /analytics/activities
GET  /analytics/lsr
GET  /analytics/priority-distribution
GET  /analytics/priority-reports
```

The Reports API supports server-side pagination and filtering, allowing the application to handle larger datasets without loading every report into the browser at once.

---

# Example Intelligence Flow

A report such as:

```text
During maintenance on an elevated pipe rack, a technician
used an unsecured ladder and was not connected to the available
fall-arrest system. The technician lost balance while reaching
for a tool but regained footing without injury.
```

can be transformed into structured intelligence such as:

```text
SIF Signal
High

Precursor
Unsecured access equipment

Precursor
Missing fall protection

Exposure
Working at height

Barrier
Fall protection

Barrier Failure
Required protection was not effectively implemented

Life-Saving Rule
Working at Height

Priority
High
```

The system can then use semantic search to identify similar historical reports and help reveal recurring patterns.

---

# Dashboard

The application provides three primary user-facing sections:

```text
Dashboard
Reports
Upload Report
```

### Dashboard

Provides a high-level overview of safety intelligence and priority patterns.

### Reports

Provides searchable, filterable and paginated safety reports with access to detailed intelligence.

### Upload Report

Allows users to submit new CSV datasets for asynchronous processing by the ML pipeline.

---

# Design Principles

SIFSentinel is designed around several principles:

### From incidents to precursors

The objective is not only to count incidents, but to identify conditions and barriers that may precede serious outcomes.

### Explainability

The system surfaces precursor, hazard, exposure and barrier information rather than presenting only a classification result.

### Prioritization

Reports are ranked so HSE teams can focus attention where the combined SIF and precursor signals are strongest.

### Continuous analysis

New reports can be uploaded and processed through the same automated pipeline rather than waiting for periodic manual triage.

### Historical learning

Semantic similarity allows current observations to be compared with previous reports to reveal recurring patterns.

---

# Performance & Scalability

The system is designed to support larger safety-report datasets through:

* asynchronous ML processing
* PostgreSQL persistence
* server-side report pagination
* server-side filtering
* vector similarity using `pgvector`
* persistent model caching
* Dockerized services

The current implementation is a prototype and should be validated and calibrated further against domain-specific operational data before production deployment.

---

# Project Status

SIFSentinel is a **working prototype** developed for the Smart India Hackathon.

Current capabilities include:

* End-to-end CSV ingestion
* Dataset validation
* Asynchronous processing
* SIF-potential classification
* Precursor extraction
* IOGP Life-Saving Rule mapping
* Barrier intelligence
* Risk and priority scoring
* Semantic similarity search
* PostgreSQL persistence
* Vector storage with pgvector
* Interactive dashboard
* Report-level intelligence
* Server-side pagination and filtering
* Dockerized deployment

The complete application has been tested using Docker on both Linux and macOS.

---

# Smart India Hackathon

**Problem Statement:** 26165

**Organization:** Oil India Limited

**Category:** Software

**Problem Statement:**

> AI/NLP Engine to Detect Serious Injury & Fatality (SIF) Precursors in OIL's Unsafe-Act/Unsafe-Condition and Near-Miss Reports

The prototype addresses the requested capabilities of:

* SIF-potential classification
* IOGP Life-Saving Rule mapping
* recurring precursor analysis
* interactive safety intelligence
* prioritization of reports where fatal potential is highest

---

# Team

Developed by the SIFSentinel team for the Smart India Hackathon.

### Tagline

**Detect the precursor. Understand the barrier. Prevent the event.**

---

# License

This project is licensed under the MIT License — see the LICENSE file for details.


