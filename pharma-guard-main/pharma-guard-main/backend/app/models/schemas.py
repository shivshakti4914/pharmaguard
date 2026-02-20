from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class DetectedVariant(BaseModel):
    rsid: str
    gene: str
    star_allele: str
    chromosome: str
    position: int
    ref: str
    alt: str
    genotype: str


class RiskAssessment(BaseModel):
    risk_label: str  # Safe | Adjust Dosage | Toxic | Ineffective | Unknown
    confidence_score: float
    severity: str    # none | low | moderate | high | critical


class PharmacogenomicProfile(BaseModel):
    primary_gene: str
    diplotype: str
    phenotype: str   # PM | IM | NM | RM | URM | Unknown
    detected_variants: List[DetectedVariant]


class ClinicalRecommendation(BaseModel):
    action: str
    dosing_guidance: str
    alternative_drugs: List[str]
    monitoring_required: bool
    cpic_guideline: str


class LLMExplanation(BaseModel):
    summary: str
    mechanism: str
    variant_impact: str
    clinical_significance: str


class QualityMetrics(BaseModel):
    vcf_parsing_success: bool
    variants_detected: int
    genes_analyzed: List[str]
    confidence_basis: str


class AnalysisResponse(BaseModel):
    patient_id: str
    drug: str
    timestamp: str
    risk_assessment: RiskAssessment
    pharmacogenomic_profile: PharmacogenomicProfile
    clinical_recommendation: ClinicalRecommendation
    llm_generated_explanation: LLMExplanation
    quality_metrics: QualityMetrics


class AnalysisRequest(BaseModel):
    drug: str
    patient_id: Optional[str] = "PATIENT_001"
