TRACE — Transnational Darknet & Encrypted Commerce Examiner
<p align="center">
  <strong>AI-Assisted Digital Investigation & Cyber Forensics Platform</strong>
</p><p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.x-blue">
  <img alt="Backend" src="https://img.shields.io/badge/Backend-FastAPI-009688">
  <img alt="Machine Learning" src="https://img.shields.io/badge/ML-scikit--learn-orange">
  <img alt="Database" src="https://img.shields.io/badge/Database-SQLite-003B57">
  <img alt="Interface" src="https://img.shields.io/badge/Frontend-HTML%20%7C%20CSS%20%7C%20JavaScript-E34F26">
</p>TRACE is an AI-assisted digital investigation platform designed to organize and analyze suspicious online listings and related entities. It brings together text-based slang detection, vendor/entity linking, cryptocurrency transaction-flow analysis, alerts, and digital evidence integrity features in a unified web dashboard.

The project uses demonstration and synthetic data to illustrate how multiple investigative signals can be reviewed together. It is a prototype and should not be treated as an operational law-enforcement system or as proof that an individual has committed a crime.
Table of Contents
- Problem Statement
- Our Solution
- Key Features
- How It Works
- System Architecture
- Technology Stack
- Machine Learning Approach
- Project Structure
- Getting Started
- API Overview
- Data, Privacy, and Limitations
- Future Enhancements
- Contributing
- License
Problem Statement
Digital investigations may involve large amounts of unstructured text, multiple vendor profiles, cryptocurrency transactions, and evidence records. Reviewing each source separately can make it difficult to organize signals and identify relationships that may warrant further examination.

The challenge: How can text analysis, entity linking, transaction graphing, and evidence integrity tools be brought together in one investigation-support interface while keeping findings reviewable by a human investigator?
Our Solution
TRACE combines a web dashboard and Python-based analysis modules to help users explore investigation-related data in one place. The current prototype includes:
1. Text analysis for potentially relevant slang and listing indicators.
2. Listing and vendor records with filters and detail views.
3. Entity-linking features to represent possible relationships between vendor profiles.
4. Cryptocurrency wallet and transaction-flow analysis using available project data.
5. Evidence capture and integrity-verification workflows.
6. Watchlist management and dashboard alerts.
7. Synthetic/demo data to support development and demonstrations.
Key Features
1. Text and Slang Analysis
Uses a machine-learning pipeline and a slang lexicon to analyze submitted text and return indicators for further review. Model output is a signal, not a definitive classification of intent or illegal activity.
2. Listing Review
Provides listing records, detail endpoints, and filters such as source and minimum score to help users review relevant entries.
3. Vendor and Entity Linking
Organizes vendor profiles and possible links. The project includes text-style analysis and graph data generation to help visualize potential relationships; matches require independent verification.
4. Cryptocurrency Wallet Analysis
Provides wallet and transaction records, wallet-risk indicators, and fund-flow graph construction based on the data available to the application. This is not a direct blockchain intelligence feed unless separately connected to a verified data provider.
5. Digital Evidence Locker
Includes evidence capture, verification, and dossier-related functionality. Hash-based checks can help detect changes to stored evidence, but do not by themselves establish authenticity, lawful collection, or a complete chain of custody.
6. Alerts and Watchlists
Supports viewing dashboard alerts, marking alerts as read, and managing watchlist entries.
7. Web Dashboard and REST API
A FastAPI application serves the dashboard and API endpoints, with static CSS/JavaScript assets and Jinja2 HTML templates.
How It Works
1. Data input: The application loads records from its local database and can analyze text submitted through the interface/API.
2. Text analysis: The slang detector combines its trained model and lexicon-based indicators.
3. Entity review: Vendor and listing information is used to calculate or display possible links.
4. Transaction review: Wallet and transaction records are organized into wallet details and fund-flow graphs.
5. Evidence handling: Evidence records can be captured and checked through the evidence module.
6. Dashboard presentation: Alerts, listings, vendors, wallet information, and other results are presented through the web interface.
7. Human verification: Any findings should be checked against reliable independent sources before decisions are made.
System Architecture
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
     Slang/Text       Entity Linking   Crypto Tracer
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
Technology Stack
Component	Technologies
Programming Language	Python
Backend / REST API	FastAPI
ASGI Server	Uvicorn
HTML Templates	Jinja2
Frontend	HTML5, CSS3, JavaScript
Machine Learning	scikit-learn, TF-IDF, LinearSVC, calibrated classifier
Numerical Processing	NumPy, SciPy
Database	SQLite (sqlite3)
Data Formats	JSON, JSONL, CSV
Evidence Integrity	Hash-based verification (implemented in the evidence module)


Machine Learning Approach
The repository includes a model-training module for text/slang detection. The code uses a TF-IDF text representation and a LinearSVC-based classifier with calibration support, alongside a lexicon-based component.

A typical development workflow is:
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
The included data is synthetic/demo data. Model performance on synthetic examples does not establish accuracy on real-world content. Before any real-world use, evaluate with appropriately collected and labeled data, document false-positive/false-negative rates, and conduct ongoing bias and drift checks.
Project Structure
TRACE-main/
├── app.py                           # FastAPI application and API routes
├── run.bat                          # Windows startup helper
├── generate_synthetic_dataset.py    # Synthetic dataset generation
├── data/
│   ├── slang_lexicon.json           # Slang/indicator lexicon
│   ├── synthetic_drug_slang_dataset.json
│   └── synthetic_drug_slang_dataset.jsonl
├── models/
│   ├── database.py                  # SQLite persistence and queries
│   ├── slang_detector.py            # Text/slang analysis
│   ├── train_slang_model.py         # Model training and evaluation
│   ├── slang_model.pkl              # Serialized model artifact
│   ├── entity_linker.py             # Vendor/entity linking
│   ├── crypto_tracer.py             # Wallet and transaction-flow analysis
│   ├── evidence_locker.py           # Evidence capture/verification
│   └── data_generator.py            # Demo data generation
├── templates/
│   └── index.html                   # Dashboard page
├── static/
│   ├── css/style.css                # Dashboard styles
│   └── js/app.js                    # Frontend behavior
└── trace.db                         # Local SQLite database (demo data)
Getting Started
Prerequisites
- Python 3.10 or newer recommended.
- pip and a terminal.
- A modern web browser.
1. Clone the Repository
Replace the repository URL below with your actual TRACE GitHub URL:
git clone <YOUR-TRACE-REPOSITORY-URL>
cd TRACE-main
2. Create a Virtual Environment
Windows PowerShell:
python -m venv .venv
.\.venv\Scripts\Activate.ps1
Windows Command Prompt:
python -m venv .venv
.venv\Scripts\activate.bat
macOS/Linux:
python3 -m venv .venv
source .venv/bin/activate
3. Install Dependencies
The uploaded project archive does not include a requirements.txt file. Install the primary runtime and machine-learning dependencies in the activated environment:
python -m pip install fastapi uvicorn jinja2 numpy scipy scikit-learn
If an import error identifies another required package, install it in the virtual environment and add the confirmed dependency to a requirements.txt file for reproducible setup.
4. Run the Application
From the project root, run:
uvicorn app:app --host 127.0.0.1 --port 8000
Then open http://127.0.0.1:8000 in your browser. Interactive API documentation is available at http://127.0.0.1:8000/docs.

On Windows, run.bat is also included as a startup helper, but it expects a requirements.txt file; use the manual installation steps above if that file is not present in your checkout.
API Overview
The FastAPI application exposes endpoints including:
Method	Endpoint	Purpose
GET	/api/dashboard/stats	Retrieve dashboard statistics
GET	/api/dashboard/alerts	List alerts with optional filtering
GET	/api/dashboard/alert-counts	Retrieve alert counts
POST	/api/dashboard/alerts/{alert_id}/read	Mark an alert as read
GET	/api/listings	List/filter listing records
GET	/api/listings/{listing_id}	Retrieve a listing
POST	/api/analyze	Analyze submitted text
GET	/api/vendors	List/filter vendors
GET	/api/vendors/{vendor_id}	Retrieve vendor details and related records
GET	/api/vendors/graph/data	Generate vendor graph data
GET	/api/crypto/wallets	List wallet records
GET	/api/crypto/wallet/{address}	Retrieve wallet details and analysis
GET	/api/crypto/flow/{address}	Build a wallet fund-flow graph
GET	/api/crypto/transactions	List transaction records
GET	/api/crypto/risk/{address}	Retrieve the configured wallet risk assessment
GET	/api/evidence	List evidence records
POST	/api/evidence/capture	Capture an evidence record
POST	/api/evidence/verify/{evidence_id}	Verify an evidence record
GET	/api/evidence/dossier/{vendor_id}	Generate a vendor-related dossier response
GET	/api/watchlist	List watchlist entries
POST	/api/watchlist	Add a watchlist entry
DELETE	/api/watchlist/{watchlist_id}	Remove a watchlist entry
GET	/api/slang/drift	Review slang drift records/status
POST	/api/slang/analyze	Run slang analysis
GET	/api/slang/lexicon	Retrieve the configured lexicon


Use /docs while the server is running to inspect the request and response schemas.
Data, Privacy, and Limitations
- The project contains synthetic/demo data and a local SQLite database. Review all records before publishing or sharing the repository.
- Do not commit real personal data, confidential case information, credentials, API keys, or private evidence.
- Treat machine-learning scores, slang matches, entity links, and wallet risk outputs as investigative leads—not proof of wrongdoing.
- Entity matches can be coincidental, text can be ambiguous, and the included wallet analysis operates on the data available to the application.
- Hash verification can help detect changes but does not independently prove evidence authenticity or legal admissibility.
- The prototype is not a substitute for validated forensic procedures, legal review, or human investigation.
- Restrict access and use only lawfully obtained data in any authorized testing or deployment.
Future Enhancements
Potential improvements include:
- Add a maintained requirements.txt and automated tests.
- Add authentication, role-based authorization, and audit logging.
- Improve model evaluation with carefully governed and representative datasets.
- Add explainability details and clear confidence/uncertainty reporting.
- Add stronger evidence metadata, timestamps, and auditable custody events.
- Connect to verified data providers only where authorized and technically implemented.
- Improve database migrations, backup procedures, and deployment hardening.
- Add dashboard screenshots and a reproducible demo walkthrough.
These are proposed enhancements, not claims that they are already implemented.
Contributing
Contributions, bug reports, and suggestions are welcome. For changes, create a branch, document the purpose of the change, and test the affected functionality before opening a pull request.
