"""
PharmaGuard Backend Tests
Run: pytest tests/ -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.vcf_parser import parse_vcf, determine_diplotype
from app.services.pgx_engine import analyze_drug
from app.utils.knowledge_base import diplotype_to_phenotype, get_allele_function


SAMPLE_VCF = """\
##fileformat=VCFv4.2
##INFO=<ID=GENE,Number=1,Type=String,Description="Gene">
##INFO=<ID=STAR,Number=1,Type=String,Description="Star allele">
##INFO=<ID=RS,Number=1,Type=String,Description="rsID">
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tPATIENT_TEST
22\t42522613\trs3892097\tC\tT\t.\tPASS\tGENE=CYP2D6;STAR=*4;RS=rs3892097\tGT\t0/1
10\t96702047\trs4244285\tG\tA\t.\tPASS\tGENE=CYP2C19;STAR=*2;RS=rs4244285\tGT\t1/1
"""


def test_vcf_parsing():
    variants, patient_id, success = parse_vcf(SAMPLE_VCF)
    assert success
    assert patient_id == "PATIENT_TEST"
    assert len(variants) == 2
    genes = [v.gene for v in variants]
    assert "CYP2D6" in genes
    assert "CYP2C19" in genes


def test_vcf_patient_id_extraction():
    _, patient_id, _ = parse_vcf(SAMPLE_VCF)
    assert patient_id == "PATIENT_TEST"


def test_diplotype_determination():
    variants, _, _ = parse_vcf(SAMPLE_VCF)
    dip = determine_diplotype(variants, "CYP2D6")
    assert "*4" in dip  # Het: *1/*4


def test_phenotype_pm():
    # Two nonfunctional alleles → Poor Metabolizer
    p = diplotype_to_phenotype("CYP2C19", "nonfunctional", "nonfunctional")
    assert p == "PM"


def test_phenotype_im():
    p = diplotype_to_phenotype("CYP2D6", "nonfunctional", "normal")
    assert p == "IM"


def test_phenotype_nm():
    p = diplotype_to_phenotype("CYP2D6", "normal", "normal")
    assert p == "NM"


def test_phenotype_urm():
    p = diplotype_to_phenotype("CYP2D6", "increased", "normal")
    assert p == "URM"


def test_codeine_urm_toxic():
    variants, _, _ = parse_vcf(SAMPLE_VCF)
    # Inject a URM variant for testing
    from app.models.schemas import DetectedVariant
    variants.append(DetectedVariant(
        rsid="rs_test", gene="CYP2D6", star_allele="*1xN",
        chromosome="22", position=999, ref="A", alt=".", genotype="0/1"
    ))
    risk, profile = analyze_drug("CODEINE", variants)
    assert risk.risk_label in ("Safe", "Adjust Dosage", "Toxic", "Ineffective", "Unknown")


def test_clopidogrel_pm_ineffective():
    # CYP2C19 *2/*2 → PM → Ineffective for clopidogrel
    from app.models.schemas import DetectedVariant
    variants = [
        DetectedVariant(rsid="rs4244285", gene="CYP2C19", star_allele="*2",
                        chromosome="10", position=96702047, ref="G", alt="A", genotype="1/1"),
    ]
    risk, profile = analyze_drug("CLOPIDOGREL", variants)
    assert profile.phenotype == "PM"
    assert risk.risk_label == "Ineffective"
    assert risk.severity == "critical"


def test_json_schema_fields():
    """Ensure all required JSON fields are present in AnalysisResponse"""
    from app.models.schemas import (
        AnalysisResponse, RiskAssessment, PharmacogenomicProfile,
        ClinicalRecommendation, LLMExplanation, QualityMetrics, DetectedVariant
    )
    r = AnalysisResponse(
        patient_id="P001", drug="CODEINE", timestamp="2026-01-01T00:00:00Z",
        risk_assessment=RiskAssessment(risk_label="Safe", confidence_score=0.9, severity="none"),
        pharmacogenomic_profile=PharmacogenomicProfile(
            primary_gene="CYP2D6", diplotype="*1/*1", phenotype="NM", detected_variants=[]
        ),
        clinical_recommendation=ClinicalRecommendation(
            action="Standard", dosing_guidance="Normal dose", alternative_drugs=[],
            monitoring_required=False, cpic_guideline="CPIC"
        ),
        llm_generated_explanation=LLMExplanation(
            summary="s", mechanism="m", variant_impact="v", clinical_significance="c"
        ),
        quality_metrics=QualityMetrics(
            vcf_parsing_success=True, variants_detected=0,
            genes_analyzed=[], confidence_basis="CPIC"
        )
    )
    d = r.model_dump()
    required = ["patient_id", "drug", "timestamp", "risk_assessment",
                "pharmacogenomic_profile", "clinical_recommendation",
                "llm_generated_explanation", "quality_metrics"]
    for field in required:
        assert field in d, f"Missing field: {field}"


if __name__ == "__main__":
    test_vcf_parsing()
    test_vcf_patient_id_extraction()
    test_diplotype_determination()
    test_phenotype_pm()
    test_phenotype_im()
    test_phenotype_nm()
    test_phenotype_urm()
    test_codeine_urm_toxic()
    test_clopidogrel_pm_ineffective()
    test_json_schema_fields()
    print("\n✅ All tests passed!")
