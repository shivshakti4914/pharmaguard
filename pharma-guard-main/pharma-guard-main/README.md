# PharmaGuard — Pharmacogenomic Risk Prediction System

> RIFT 2026 Hackathon · Pharmacogenomics / Explainable AI Track · HealthTech

---

## Live Demo & Links

- **Live App:** (https://pharmaguard-green.vercel.app/)
- **API Docs:** https://pharmaguard-1-fp7v.onrender.com/
- **GitHub:** *(this repo)*

---

## What It Does

PharmaGuard analyzes patient genetic data (VCF files) and predicts personalized pharmacogenomic risks for 6 critical drugs, generating clinically actionable recommendations with AI-generated explanations.

**No API key required to run** — all pharmacogenomics logic is embedded. OpenAI integration is optional (graceful fallback to rule-based explanations).

---

## Architecture

```
pharma_guard/
├── backend/
│   ├── app/
│   │   ├── main.py                  ← FastAPI entry point
│   │   ├── models/schemas.py        ← Pydantic data models
│   │   ├── routers/
│   │   │   ├── analysis.py          ← POST /api/analyze
│   │   │   └── health.py            ← GET /api/health
│   │   ├── services/
│   │   │   ├── vcf_parser.py        ← VCF 4.2 parser
│   │   │   ├── pgx_engine.py        ← Diplotype/phenotype/risk engine
│   │   │   └── llm_service.py       ← OpenAI integration (optional)
│   │   └── utils/
│   │       └── knowledge_base.py    ← CPIC-aligned rules (no API needed)
│   ├── tests/test_pharma_guard.py
│   ├── sample_vcf/sample_patient.vcf
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── App.jsx                  ← Full React UI
    │   ├── main.jsx
    │   └── index.css
    ├── index.html
    ├── package.json
    └── vite.config.js
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, Vite, pure CSS-in-JS |
| Backend | Python 3.11+, FastAPI, Pydantic v2 |
| AI/LLM | OpenAI GPT-4o-mini (optional) — rule-based fallback included |
| VCF Parsing | Custom VCF 4.2 parser (no external library needed) |
| PGx Logic | CPIC-aligned knowledge base (embedded, no API) |
| Deploy | Vercel (frontend) + Render (backend) |

---

## Supported Genes & Drugs

| Gene | Drug | Key Interaction |
|------|------|----------------|
| CYP2D6 | CODEINE | URM → Toxic (respiratory depression); PM → Ineffective |
| CYP2C19 | CLOPIDOGREL | PM → Ineffective (stent thrombosis risk) |
| CYP2C9 | WARFARIN | PM → Adjust (bleeding risk) |
| SLCO1B1 | SIMVASTATIN | PM → Toxic (myopathy/rhabdomyolysis) |
| TPMT | AZATHIOPRINE | PM → Toxic (myelosuppression) |
| DPYD | FLUOROURACIL | PM → Toxic (life-threatening) |

---

## Setup & Installation

### Backend

```bash
cd backend
pip install -r requirements.txt
cp ../.env.example .env   # edit if you have OpenAI key (optional)
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env      # set VITE_API_URL if needed
npm run dev               # runs on http://localhost:5173
```

### Run Tests

```bash
cd backend
pytest tests/ -v
```

---

## API Reference

### `POST /api/analyze`

Analyze VCF file for pharmacogenomic drug risks.

**Form Data:**
- `vcf_file`: `.vcf` file (max 5MB)
- `drugs`: comma-separated drug names (e.g. `CODEINE,WARFARIN`)

**Response:** Array of `AnalysisResponse` objects matching the required JSON schema.

### `GET /api/health`
Returns service health status.

### `GET /api/drugs`
Lists all supported drugs.

### `GET /api/genes`
Lists all supported pharmacogenes.

---

## JSON Output Schema

```json
{
  "patient_id": "PATIENT_001",
  "drug": "CODEINE",
  "timestamp": "2026-01-01T00:00:00Z",
  "risk_assessment": {
    "risk_label": "Toxic",
    "confidence_score": 0.97,
    "severity": "critical"
  },
  "pharmacogenomic_profile": {
    "primary_gene": "CYP2D6",
    "diplotype": "*1/*1xN",
    "phenotype": "URM",
    "detected_variants": [...]
  },
  "clinical_recommendation": {
    "action": "Contraindicated — Toxicity Risk",
    "dosing_guidance": "...",
    "alternative_drugs": ["Acetaminophen", "NSAIDs"],
    "monitoring_required": true,
    "cpic_guideline": "CPIC Guideline for Codeine and CYP2D6"
  },
  "llm_generated_explanation": {
    "summary": "...",
    "mechanism": "...",
    "variant_impact": "...",
    "clinical_significance": "..."
  },
  "quality_metrics": {
    "vcf_parsing_success": true,
    "variants_detected": 8,
    "genes_analyzed": ["CYP2D6", "CYP2C19"],
    "confidence_basis": "CPIC guidelines + pharmacogenomic star-allele database"
  }
}
```

---

## Deployment

### Vercel (Frontend)

```bash
cd frontend
npm run build
# Deploy dist/ folder to Vercel
# Set env var: VITE_API_URL=https://your-backend.onrender.com/api
```

### Render (Backend)

- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Set env: `OPENAI_API_KEY` (optional)

---

## Team

*Add team member names here*

---

## Tags

`#RIFT2026` `#PharmaGuard` `#Pharmacogenomics` `#AIinHealthcare`
# pharma-guard
