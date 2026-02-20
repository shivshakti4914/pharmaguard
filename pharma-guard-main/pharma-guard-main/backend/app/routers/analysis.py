from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
from datetime import datetime, timezone
import json

from app.models.schemas import AnalysisResponse, QualityMetrics
from app.services.vcf_parser import parse_vcf
from app.services.pgx_engine import analyze_drug, get_mechanism
from app.services.llm_service import generate_explanation
from app.utils.knowledge_base import (
    SUPPORTED_DRUGS, DRUG_GENE_MAP, get_clinical_rec, SUPPORTED_GENES
)

router = APIRouter()


@router.post("/analyze", response_model=List[AnalysisResponse])
async def analyze(
    vcf_file: UploadFile = File(...),
    drugs: str = Form(...),
):
    """
    Analyze a VCF file for pharmacogenomic risk across one or more drugs.
    
    - vcf_file: .vcf file upload
    - drugs: comma-separated drug names (e.g. "CODEINE,WARFARIN")
    """
    # ── 1. Read & validate VCF ────────────────────────────────────────────────
    if not vcf_file.filename.endswith(".vcf"):
        raise HTTPException(400, "File must be a .vcf file")

    raw = await vcf_file.read()
    if len(raw) > 5 * 1024 * 1024:
        raise HTTPException(400, "File exceeds 5MB limit")

    content = raw.decode("utf-8", errors="replace")
    variants, patient_id, parse_success = parse_vcf(content)

    if not parse_success:
        raise HTTPException(422, "Could not parse any pharmacogenomic variants from VCF file. Check file format.")

    # ── 2. Parse drugs list ───────────────────────────────────────────────────
    drug_list = [d.strip().upper() for d in drugs.split(",") if d.strip()]
    if not drug_list:
        raise HTTPException(400, "At least one drug name required")

    unsupported = [d for d in drug_list if d not in SUPPORTED_DRUGS]
    if unsupported:
        raise HTTPException(400, f"Unsupported drug(s): {unsupported}. Supported: {SUPPORTED_DRUGS}")

    # ── 3. Analyze each drug ──────────────────────────────────────────────────
    results = []
    genes_analyzed = list(set(v.gene for v in variants if v.gene in SUPPORTED_GENES))

    for drug in drug_list:
        risk, profile = analyze_drug(drug, variants)
        clinical_rec = get_clinical_rec(drug, profile.phenotype)

        # ── 4. LLM explanation ────────────────────────────────────────────────
        explanation = await generate_explanation(
            drug=drug,
            gene=profile.primary_gene,
            phenotype=profile.phenotype,
            diplotype=profile.diplotype,
            risk_label=risk.risk_label,
            severity=risk.severity,
            dosing_guidance=clinical_rec["dosing_guidance"],
        )

        # ── 5. Build response ─────────────────────────────────────────────────
        from app.models.schemas import ClinicalRecommendation
        result = AnalysisResponse(
            patient_id=patient_id,
            drug=drug,
            timestamp=datetime.now(timezone.utc).isoformat(),
            risk_assessment=risk,
            pharmacogenomic_profile=profile,
            clinical_recommendation=ClinicalRecommendation(
                action=clinical_rec["action"],
                dosing_guidance=clinical_rec["dosing_guidance"],
                alternative_drugs=clinical_rec["alternative_drugs"],
                monitoring_required=clinical_rec["monitoring_required"],
                cpic_guideline=clinical_rec["cpic_guideline"],
            ),
            llm_generated_explanation=explanation,
            quality_metrics=QualityMetrics(
                vcf_parsing_success=parse_success,
                variants_detected=len(variants),
                genes_analyzed=genes_analyzed,
                confidence_basis="CPIC guidelines + pharmacogenomic star-allele database",
            ),
        )
        results.append(result)

    return results


@router.get("/drugs")
async def list_drugs():
    return {"supported_drugs": SUPPORTED_DRUGS}


@router.get("/genes")
async def list_genes():
    return {"supported_genes": SUPPORTED_GENES}
