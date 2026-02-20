"""
LLM Service — generates clinical explanations.

Strategy:
  1. If OPENAI_API_KEY is set in environment → use OpenAI GPT-4o
  2. Otherwise → generate rich rule-based explanations from knowledge_base
     (no API key required, still clinically meaningful)
"""
import os
from app.models.schemas import LLMExplanation
from app.utils.knowledge_base import MECHANISMS, RISK_RULES


def _rule_based_explanation(
    drug: str, gene: str, phenotype: str, diplotype: str, risk_label: str
) -> LLMExplanation:
    """
    Generate a structured clinical explanation using embedded knowledge.
    No API key needed.
    """
    mechanism = MECHANISMS.get(gene, f"{gene} plays a role in drug metabolism.")
    drug_rules = RISK_RULES.get(drug, {})
    rule = drug_rules.get(phenotype, drug_rules.get("Unknown", ("Unknown", 0.5, "moderate", "")))
    _, _, _, rule_detail = rule

    phenotype_labels = {
        "PM": "Poor Metabolizer",
        "IM": "Intermediate Metabolizer",
        "NM": "Normal Metabolizer",
        "URM": "Ultra-Rapid Metabolizer",
        "RM": "Rapid Metabolizer",
        "Unknown": "Undetermined Metabolizer",
    }
    phenotype_long = phenotype_labels.get(phenotype, phenotype)

    summary = (
        f"This patient carries the {diplotype} diplotype in {gene}, "
        f"classifying them as a {phenotype_long} ({phenotype}). "
        f"For {drug}, this results in a '{risk_label}' risk assessment. "
        f"{rule_detail}"
    )

    variant_impact = (
        f"The detected {gene} diplotype ({diplotype}) alters enzyme activity "
        f"relevant to {drug} pharmacokinetics. "
        f"{'Reduced or absent enzyme activity leads to drug accumulation or lack of therapeutic effect.' if phenotype in ('PM', 'IM') else ''}"
        f"{'Excess enzyme activity leads to rapid drug conversion, potentially causing toxicity or therapeutic failure.' if phenotype == 'URM' else ''}"
        f"{'Normal enzyme activity is expected; standard pharmacokinetics apply.' if phenotype == 'NM' else ''}"
    ).strip()

    clinical_significance = (
        f"According to CPIC guidelines, patients with {gene} {phenotype} phenotype "
        f"have a clinically actionable pharmacogenomic interaction with {drug}. "
        f"Prescribers should review dosing recommendations and consider genetic test results "
        f"before initiating or continuing {drug} therapy."
    )

    return LLMExplanation(
        summary=summary,
        mechanism=mechanism,
        variant_impact=variant_impact,
        clinical_significance=clinical_significance,
    )


async def generate_explanation(
    drug: str,
    gene: str,
    phenotype: str,
    diplotype: str,
    risk_label: str,
    severity: str,
    dosing_guidance: str,
) -> LLMExplanation:
    """
    Try OpenAI first, fall back to rule-based explanation.
    """
    api_key = os.getenv("OPENAI_API_KEY", "")

    if api_key and api_key not in ("", "your_openai_api_key_here", "sk-..."):
        try:
            return await _openai_explanation(
                api_key, drug, gene, phenotype, diplotype,
                risk_label, severity, dosing_guidance
            )
        except Exception as e:
            print(f"[LLM] OpenAI call failed ({e}), falling back to rule-based.")

    # No key or failure — use rule-based
    return _rule_based_explanation(drug, gene, phenotype, diplotype, risk_label)


async def _openai_explanation(
    api_key: str,
    drug: str, gene: str, phenotype: str, diplotype: str,
    risk_label: str, severity: str, dosing_guidance: str
) -> LLMExplanation:
    from openai import AsyncOpenAI
    import json

    client = AsyncOpenAI(api_key=api_key)

    phenotype_labels = {
        "PM": "Poor Metabolizer", "IM": "Intermediate Metabolizer",
        "NM": "Normal Metabolizer", "URM": "Ultra-Rapid Metabolizer",
        "RM": "Rapid Metabolizer", "Unknown": "Undetermined Metabolizer",
    }

    prompt = f"""You are a clinical pharmacogenomics specialist. Generate a structured clinical explanation.

Patient Data:
- Drug: {drug}
- Gene: {gene}
- Diplotype: {diplotype}
- Phenotype: {phenotype_labels.get(phenotype, phenotype)} ({phenotype})
- Risk Label: {risk_label}
- Severity: {severity}
- Dosing Guidance: {dosing_guidance}

Respond ONLY with valid JSON (no markdown, no extra text):
{{
  "summary": "2-3 sentence plain-language summary for the prescribing physician",
  "mechanism": "Biological mechanism explaining how this gene variant affects drug metabolism (1-2 sentences)",
  "variant_impact": "Specific impact of this diplotype on the drug's pharmacokinetics (1-2 sentences)",
  "clinical_significance": "Clinical significance and what action the physician should take (1-2 sentences)"
}}"""

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=500,
    )

    text = response.choices[0].message.content.strip()
    # Strip markdown fences if present
    text = text.replace("```json", "").replace("```", "").strip()
    data = json.loads(text)

    return LLMExplanation(
        summary=data.get("summary", ""),
        mechanism=data.get("mechanism", ""),
        variant_impact=data.get("variant_impact", ""),
        clinical_significance=data.get("clinical_significance", ""),
    )
