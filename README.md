<div align="center">

# TRACE

### Transnational Darknet & Encrypted Commerce Examiner

**An AI-assisted platform for digital investigation and cyber forensics research**

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)
![scikit-learn](https://img.shields.io/badge/ML-scikit--learn-F7931E?logo=scikitlearn&logoColor=white)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite&logoColor=white)
![Status](https://img.shields.io/badge/Status-Prototype-yellow)

</div>

---

> **Notice:** TRACE is a research prototype built on synthetic demonstration data. It is not an operational law-enforcement system, and its outputs must not be treated as proof that any individual or entity has committed a crime. See [Data, Privacy, and Limitations](#data-privacy-and-limitations).

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Machine Learning Approach](#machine-learning-approach)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [API Reference](#api-reference)
- [Data, Privacy, and Limitations](#data-privacy-and-limitations)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

## Overview

Digital investigations often involve large volumes of unstructured text, multiple vendor profiles, cryptocurrency transactions, and evidence records. When each source is reviewed in isolation, it is difficult to correlate signals and identify relationships that merit closer examination.

**TRACE** addresses this by consolidating text analysis, entity linking, transaction-flow graphing, and evidence-integrity tooling into a single web dashboard, while keeping every finding open to review by a human investigator.

## Key Features

| Capability | Description |
|---|---|
| **Text & Slang Analysis** | Combines a trained ML model with a slang lexicon to flag indicators in submitted text. Output is a review signal, not a determination of intent or illegality. |
| **Listing Review** | Browse listings with detail views and filters such as source and minimum score. |
| **Vendor & Entity Linking** | Organizes vendor profiles and generates graph data that visualizes possible relationships. Links require independent verification. |
| **Cryptocurrency Analysis** | Wallet and transaction records, wallet-risk indicators, and fund-flow graphs built from data available to the application. Not a live blockchain-intelligence feed unless connected to a verified provider. |
| **Digital Evidence Locker** | Evidence capture, hash-based verification, and vendor dossier generation. Hashing detects changes but does not establish authenticity, lawful collection, or chain of custody. |
| **Alerts & Watchlists** | Dashboard alerts with read-state tracking, plus watchlist management. |
| **Dashboard & REST API** | A FastAPI application serving a Jinja2/HTML/CSS/JavaScript dashboard and a documented JSON API. |

## System Architecture

```
                 Investigator / Analyst
                          |
                          v
              Web Dashboard (HTML/CSS/JS)
                          |
                          v
                   FastAPI Application
                          |
          +---------------+----------------+
          |               |                |
          v               v                v
     Slang / Text     Entity Linking   Crypto Tracer
      Detector                         & Fund Flow
          |               |                |
          +---------------+----------------+
                          |
                          v
              Evidence Locker / Watchlists
                          |
                          v
                    SQLite Database
                          |
                          v
                Dashboard Results & Alerts
```

**Workflow**

1. **Input** – Records are loaded from the local database; text can be submitted via the UI or API.
2. **Text analysis** – The detector combines model predictions with lexicon matches.
3. **Entity review** – Vendor and listing data are used to compute and display possible links.
4. **Transaction review** – Wallet and transaction records are assembled into wallet details and fund-flow graphs.
5. **Evidence handling** – Evidence is captured and verified through the evidence module.
6. **Presentation** – Alerts, listings, vendors, and wallet data are surfaced in the dashboard.
7. **Human verification** – All findings must be checked against reliable, independent sources before any decision is made.

## Technology Stack

| Layer | Technologies |
|---|---|
| Language | Python |
| Backend / API | FastAPI, Uvicorn (ASGI) |
| Templating | Jinja2 |
| Frontend | HTML5, CSS3, JavaScript |
| Machine Learning | scikit-learn (TF-IDF, LinearSVC, calibrated classifier) |
| Numerical Processing | NumPy, SciPy |
| Database | SQLite (`sqlite3`) |
| Data Formats | JSON, JSONL, CSV |
| Evidence Integrity | Hash-based verification |

## Machine Learning Approach

The slang-detection module uses a TF-IDF text representation with a calibrated LinearSVC classifier, complemented by a lexicon-based component.

```
Synthetic / Labeled Text Data
            |
            v
      Text Preparation
            |
            v
       TF-IDF Features
            |
            v
    LinearSVC Classifier
            |
            v
  Calibrated Model Output
            |
            v
 Lexicon + Model Analysis
            |
            v
   Indicators for Review
```

> **Important:** The bundled data is synthetic. Performance on synthetic examples does not indicate accuracy on real-world content. Before any real-world use, evaluate on appropriately collected and labeled data, document false-positive and false-negative rates, and perform ongoing bias and drift monitoring.

## Project Structure

```
TRACE-main/
├── app.py                              # FastAPI application and API routes
├── run.bat                             # Windows startup helper
├── generate_synthetic_dataset.py       # Synthetic dataset generation
├── trace.db                            # Local SQLite database (demo data)
├── data/
│   ├── slang_lexicon.json              # Slang / indicator lexicon
│   ├── synthetic_drug_slang_dataset.json
│   └── synthetic_drug_slang_dataset.jsonl
├── models/
│   ├── database.py                     # SQLite persistence and queries
│   ├── slang_detector.py               # Text / slang analysis
│   ├── train_slang_model.py            # Model training and evaluation
│   ├── slang_model.pkl                 # Serialized model artifact
│   ├── entity_linker.py                # Vendor / entity linking
│   ├── crypto_tracer.py                # Wallet and transaction-flow analysis
│   ├── evidence_locker.py              # Evidence capture and verification
│   └── data_generator.py               # Demo data generation
├── templates/
│   └── index.html                      # Dashboard page
└── static/
    ├── css/style.css                   # Dashboard styles
    └── js/app.js                       # Frontend behavior
```

## Getting Started

### Prerequisites

- Python 3.10 or newer
- `pip`
- A modern web browser

### 1. Clone the repository

```bash
git clone <YOUR-TRACE-REPOSITORY-URL>
cd TRACE-main
```

### 2. Create and activate a virtual environment

**Windows (PowerShell)**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt)**
```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install fastapi uvicorn jinja2 numpy scipy scikit-learn
```

> The repository does not currently include a `requirements.txt`. If you encounter an import error for another package, install it and add it to a `requirements.txt` for reproducible setups. Note that `run.bat` expects this file to exist.

### 4. Run the application

```bash
uvicorn app:app --host 127.0.0.1 --port 8000
```

| Resource | URL |
|---|---|
| Dashboard | http://127.0.0.1:8000 |
| Interactive API docs | http://127.0.0.1:8000/docs |

## API Reference

Full request and response schemas are available at `/docs` while the server is running.

**Dashboard**

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/dashboard/stats` | Retrieve dashboard statistics |
| GET | `/api/dashboard/alerts` | List alerts with optional filtering |
| GET | `/api/dashboard/alert-counts` | Retrieve alert counts |
| POST | `/api/dashboard/alerts/{alert_id}/read` | Mark an alert as read |

**Listings & Analysis**

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/listings` | List and filter listings |
| GET | `/api/listings/{listing_id}` | Retrieve a listing |
| POST | `/api/analyze` | Analyze submitted text |

**Vendors**

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/vendors` | List and filter vendors |
| GET | `/api/vendors/{vendor_id}` | Retrieve vendor details and related records |
| GET | `/api/vendors/graph/data` | Generate vendor graph data |

**Cryptocurrency**

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/crypto/wallets` | List wallet records |
| GET | `/api/crypto/wallet/{address}` | Retrieve wallet details and analysis |
| GET | `/api/crypto/flow/{address}` | Build a wallet fund-flow graph |
| GET | `/api/crypto/transactions` | List transaction records |
| GET | `/api/crypto/risk/{address}` | Retrieve the configured wallet risk assessment |

**Evidence**

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/evidence` | List evidence records |
| POST | `/api/evidence/capture` | Capture an evidence record |
| POST | `/api/evidence/verify/{evidence_id}` | Verify an evidence record |
| GET | `/api/evidence/dossier/{vendor_id}` | Generate a vendor-related dossier |

**Watchlist**

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/watchlist` | List watchlist entries |
| POST | `/api/watchlist` | Add a watchlist entry |
| DELETE | `/api/watchlist/{watchlist_id}` | Remove a watchlist entry |

**Slang**

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/slang/drift` | Review slang drift records and status |
| POST | `/api/slang/analyze` | Run slang analysis |
| GET | `/api/slang/lexicon` | Retrieve the configured lexicon |

## Data, Privacy, and Limitations

- **Demo data only.** The project ships with synthetic data and a local SQLite database. Review all records before publishing or sharing the repository.
- **No sensitive data in version control.** Never commit real personal data, confidential case information, credentials, API keys, or private evidence.
- **Leads, not proof.** Treat model scores, slang matches, entity links, and wallet risk outputs as investigative leads only. Entity matches can be coincidental, and text can be ambiguous.
- **Limited data scope.** Wallet analysis operates solely on data available to the application.
- **Integrity vs. authenticity.** Hash verification can detect modification but does not prove authenticity or legal admissibility.
- **Not a forensic standard.** The prototype does not replace validated forensic procedures, legal review, or human investigation.
- **Lawful use.** Restrict access and use only lawfully obtained data in authorized testing or deployment.

## Roadmap

The following are proposed enhancements, not implemented features.

- [ ] Maintained `requirements.txt` and automated test suite
- [ ] Authentication, role-based authorization, and audit logging
- [ ] Improved model evaluation on governed, representative datasets
- [ ] Explainability details and clear confidence/uncertainty reporting
- [ ] Richer evidence metadata, timestamps, and auditable custody events
- [ ] Integration with verified data providers, where authorized
- [ ] Database migrations, backup procedures, and deployment hardening
- [ ] Dashboard screenshots and a reproducible demo walkthrough

## Contributing

Contributions, bug reports, and suggestions are welcome.

1. Fork the repository and create a feature branch.
2. Make your changes and document their purpose.
3. Test the affected functionality.
4. Open a pull request with a clear description.

## License

No license has been specified for this project. Add a `LICENSE` file (for example, MIT or Apache-2.0) and update this section accordingly.
