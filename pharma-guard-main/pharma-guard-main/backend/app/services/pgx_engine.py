"""
PGx Engine — maps variants → diplotype → phenotype → risk assessment.
All rules come from knowledge_base.py (no external API required).
"""
from typing import List, Tuple
from app.models.schemas import (
    DetectedVariant, RiskAssessment, PharmacogenomicProfile
)
from app.utils.knowledge_base import (
    DRUG_GENE_MAP, SUPPORTED_GENES,
    get_allele_function, diplotype_to_phenotype,
    RISK_RULES, get_clinical_rec, MECHANISMS
)
from app.services.vcf_parser import determine_diplotype, get_gene_variants


def analyze_drug(drug: str, variants: List[DetectedVariant]) -> Tuple[
    RiskAssessment, PharmacogenomicProfile
]:
    """
    Given a drug name and list of variants, compute risk and profile.
    """
    drug_upper = drug.upper()
    primary_gene = DRUG_GENE_MAP.get(drug_upper, "")

    if not primary_gene:
        # Unknown drug fallback
        risk = RiskAssessment(
            risk_label="Unknown",
            confidence_score=0.0,
            severity="none",
        )
        profile = PharmacogenomicProfile(
            primary_gene="Unknown",
            diplotype="*1/*1",
            phenotype="Unknown",
            detected_variants=[],
        )
        return risk, profile

    # Get variants for this gene
    gene_variants = get_gene_variants(variants, primary_gene)

    # Determine diplotype
    diplotype = determine_diplotype(variants, primary_gene)

    # Parse diplotype to get allele functions
    parts = diplotype.split("/")
    a1, a2 = parts[0], parts[1] if len(parts) > 1 else "*1"
    func1 = get_allele_function(a1)
    func2 = get_allele_function(a2)

    # Get phenotype
    phenotype = diplotype_to_phenotype(primary_gene, func1, func2)

    # Get risk from rules
    drug_rules = RISK_RULES.get(drug_upper, {})
    rule = drug_rules.get(phenotype, drug_rules.get("Unknown", ("Unknown", 0.5, "moderate", "")))
    risk_label, confidence, severity, _ = rule

    risk = RiskAssessment(
        risk_label=risk_label,
        confidence_score=confidence,
        severity=severity,
    )

    profile = PharmacogenomicProfile(
        primary_gene=primary_gene,
        diplotype=diplotype,
        phenotype=phenotype,
        detected_variants=gene_variants if gene_variants else variants[:2],
    )

    return risk, profile


def get_mechanism(gene: str) -> str:
    return MECHANISMS.get(gene, f"{gene} is a pharmacogenomically relevant gene affecting drug metabolism.")
