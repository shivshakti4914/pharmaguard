"""
PharmaGuard Knowledge Base
CPIC-aligned pharmacogenomics data for 6 genes and 6 drugs.
No external API needed — all rules encoded here.
"""

# ─── GENE → DRUG INTERACTION MAP ─────────────────────────────────────────────
GENE_DRUG_MAP = {
    "CYP2D6":  ["CODEINE"],
    "CYP2C19": ["CLOPIDOGREL"],
    "CYP2C9":  ["WARFARIN"],
    "SLCO1B1": ["SIMVASTATIN"],
    "TPMT":    ["AZATHIOPRINE"],
    "DPYD":    ["FLUOROURACIL"],
}

DRUG_GENE_MAP = {v: k for k, values in GENE_DRUG_MAP.items() for v in values}

SUPPORTED_DRUGS = list(DRUG_GENE_MAP.keys())
SUPPORTED_GENES = list(GENE_DRUG_MAP.keys())

# ─── STAR ALLELE → PHENOTYPE MAP ─────────────────────────────────────────────
STAR_ALLELE_FUNCTION = {
    # CYP2D6
    "*1":  "normal",
    "*2":  "normal",
    "*4":  "nonfunctional",
    "*5":  "nonfunctional",
    "*6":  "nonfunctional",
    "*9":  "decreased",
    "*10": "decreased",
    "*17": "decreased",
    "*41": "decreased",
    "*1xN": "increased",  # gene duplication
    # CYP2C19
    "*2":  "nonfunctional",
    "*3":  "nonfunctional",
    "*17": "increased",
    # CYP2C9
    "*2":  "decreased",
    "*3":  "nonfunctional",
    # SLCO1B1
    "*5":  "decreased",
    "*15": "decreased",
    # TPMT
    "*3A": "nonfunctional",
    "*3B": "nonfunctional",
    "*3C": "nonfunctional",
    "*2":  "nonfunctional",
    # DPYD
    "*2A": "nonfunctional",
    "*13": "nonfunctional",
}

def get_allele_function(star: str) -> str:
    return STAR_ALLELE_FUNCTION.get(star, "normal")

# ─── DIPLOTYPE → PHENOTYPE LOGIC ─────────────────────────────────────────────
def diplotype_to_phenotype(gene: str, allele1_func: str, allele2_func: str) -> str:
    funcs = sorted([allele1_func, allele2_func])

    if gene in ("CYP2D6", "CYP2C19", "CYP2C9", "TPMT", "DPYD"):
        if funcs == ["nonfunctional", "nonfunctional"]:
            return "PM"   # Poor Metabolizer
        elif "nonfunctional" in funcs and "decreased" in funcs:
            return "PM"
        elif "nonfunctional" in funcs and "normal" in funcs:
            return "IM"   # Intermediate Metabolizer
        elif funcs == ["decreased", "decreased"]:
            return "IM"
        elif "decreased" in funcs and "normal" in funcs:
            return "IM"
        elif funcs == ["normal", "normal"]:
            return "NM"   # Normal Metabolizer
        elif "increased" in funcs:
            return "URM"  # Ultra-Rapid Metabolizer
        else:
            return "NM"
    elif gene == "SLCO1B1":
        if "nonfunctional" in funcs or funcs == ["decreased", "decreased"]:
            return "PM"
        elif "decreased" in funcs:
            return "IM"
        else:
            return "NM"
    return "Unknown"

# ─── PHENOTYPE → RISK RULES ───────────────────────────────────────────────────
RISK_RULES = {
    "CODEINE": {
        "PM":  ("Ineffective", 0.91, "moderate", "Codeine is a prodrug requiring CYP2D6 to convert to morphine. PMs cannot activate it."),
        "IM":  ("Adjust Dosage", 0.78, "low",      "Reduced conversion to morphine; consider dose adjustment or alternative analgesic."),
        "NM":  ("Safe", 0.95, "none",              "Normal CYP2D6 activity; standard codeine dosing appropriate."),
        "URM": ("Toxic", 0.97, "critical",         "Ultra-rapid conversion to morphine; risk of life-threatening respiratory depression."),
        "Unknown": ("Unknown", 0.50, "moderate",   "Phenotype undetermined; exercise caution."),
    },
    "WARFARIN": {
        "PM":  ("Adjust Dosage", 0.93, "high",     "Reduced CYP2C9 metabolism; warfarin accumulates causing serious bleeding risk."),
        "IM":  ("Adjust Dosage", 0.82, "moderate", "Intermediate metabolism; start with reduced dose and monitor INR closely."),
        "NM":  ("Safe", 0.94, "none",              "Normal CYP2C9 activity; standard warfarin dosing appropriate."),
        "URM": ("Safe", 0.72, "low",               "Slightly faster metabolism; standard or slightly higher dose may be needed."),
        "Unknown": ("Unknown", 0.50, "moderate",   "Phenotype undetermined; start low and titrate with INR monitoring."),
    },
    "CLOPIDOGREL": {
        "PM":  ("Ineffective", 0.96, "critical",   "CYP2C19 PMs cannot convert clopidogrel to active form; high risk of stent thrombosis."),
        "IM":  ("Adjust Dosage", 0.80, "high",     "Reduced activation; consider prasugrel or ticagrelor as alternative antiplatelet."),
        "NM":  ("Safe", 0.93, "none",              "Normal CYP2C19 activation of clopidogrel; standard dosing appropriate."),
        "URM": ("Adjust Dosage", 0.70, "low",      "Possibly enhanced platelet inhibition; monitor for bleeding."),
        "Unknown": ("Unknown", 0.50, "high",       "Phenotype undetermined; consider alternative antiplatelet therapy."),
    },
    "SIMVASTATIN": {
        "PM":  ("Toxic", 0.92, "high",             "SLCO1B1 deficiency causes simvastatin accumulation; high myopathy/rhabdomyolysis risk."),
        "IM":  ("Adjust Dosage", 0.84, "moderate", "Reduced hepatic uptake; use lower simvastatin dose or switch to pravastatin/rosuvastatin."),
        "NM":  ("Safe", 0.95, "none",              "Normal SLCO1B1 transport; standard simvastatin dosing appropriate."),
        "URM": ("Safe", 0.88, "none",              "Normal to enhanced transport; standard dosing appropriate."),
        "Unknown": ("Unknown", 0.50, "moderate",   "Transport function undetermined; monitor for muscle symptoms."),
    },
    "AZATHIOPRINE": {
        "PM":  ("Toxic", 0.98, "critical",         "TPMT-deficient patients accumulate toxic thioguanine nucleotides; risk of severe myelosuppression."),
        "IM":  ("Adjust Dosage", 0.87, "high",     "Reduced TPMT activity; start at 30-70% of standard dose with CBC monitoring."),
        "NM":  ("Safe", 0.94, "none",              "Normal TPMT activity; standard azathioprine dosing appropriate."),
        "URM": ("Safe", 0.80, "low",               "High TPMT activity; may need higher doses for therapeutic effect."),
        "Unknown": ("Unknown", 0.50, "high",       "TPMT status unknown; start low and monitor CBC weekly."),
    },
    "FLUOROURACIL": {
        "PM":  ("Toxic", 0.99, "critical",         "DPYD deficiency causes 5-FU accumulation; risk of life-threatening toxicity including neutropenia, mucositis, neurotoxicity."),
        "IM":  ("Adjust Dosage", 0.90, "high",     "Partial DPYD deficiency; reduce 5-FU dose by 25-50% and monitor toxicity closely."),
        "NM":  ("Safe", 0.93, "none",              "Normal DPYD activity; standard 5-FU dosing appropriate."),
        "URM": ("Safe", 0.85, "none",              "Normal DPYD activity; standard dosing appropriate."),
        "Unknown": ("Unknown", 0.50, "high",       "DPYD status unknown; consider upfront genotyping before starting therapy."),
    },
}

# ─── CLINICAL RECOMMENDATIONS ─────────────────────────────────────────────────
CLINICAL_RECS = {
    ("CODEINE", "PM"): {
        "action": "Avoid Codeine",
        "dosing_guidance": "Codeine is contraindicated. Switch to non-opioid analgesic (e.g. NSAIDs, acetaminophen) or titrate with tramadol cautiously.",
        "alternative_drugs": ["Acetaminophen", "NSAIDs", "Tramadol (with caution)", "Morphine (direct)"],
        "monitoring_required": False,
        "cpic_guideline": "CPIC Guideline for Codeine and CYP2D6 — DOI: 10.1002/cpt.1132",
    },
    ("CODEINE", "URM"): {
        "action": "Contraindicated — Toxicity Risk",
        "dosing_guidance": "Codeine is contraindicated in ultra-rapid metabolizers. Morphine forms at dangerous rates causing respiratory depression.",
        "alternative_drugs": ["Acetaminophen", "NSAIDs", "Hydromorphone"],
        "monitoring_required": True,
        "cpic_guideline": "CPIC Guideline for Codeine and CYP2D6 — DOI: 10.1002/cpt.1132",
    },
    ("CODEINE", "IM"): {
        "action": "Use with Caution / Reduce Dose",
        "dosing_guidance": "Consider 75% of standard dose. Monitor for inadequate analgesia. Prefer non-opioid first line.",
        "alternative_drugs": ["Acetaminophen", "NSAIDs"],
        "monitoring_required": True,
        "cpic_guideline": "CPIC Guideline for Codeine and CYP2D6 — DOI: 10.1002/cpt.1132",
    },
    ("WARFARIN", "PM"): {
        "action": "Reduce Initial Dose Significantly",
        "dosing_guidance": "Start at 50% of standard initial dose. Target INR 2.0–3.0. Weekly INR monitoring for first month.",
        "alternative_drugs": ["Apixaban", "Rivaroxaban", "Dabigatran"],
        "monitoring_required": True,
        "cpic_guideline": "CPIC Guideline for Warfarin — DOI: 10.1038/clpt.2011.10",
    },
    ("CLOPIDOGREL", "PM"): {
        "action": "Switch to Alternative Antiplatelet",
        "dosing_guidance": "Clopidogrel cannot be adequately activated. Switch to prasugrel 10mg or ticagrelor 90mg BID.",
        "alternative_drugs": ["Prasugrel", "Ticagrelor"],
        "monitoring_required": False,
        "cpic_guideline": "CPIC Guideline for Clopidogrel and CYP2C19 — DOI: 10.1002/cpt.1559",
    },
    ("SIMVASTATIN", "PM"): {
        "action": "Switch Statin",
        "dosing_guidance": "Use pravastatin, rosuvastatin, or fluvastatin which are not SLCO1B1-dependent. Avoid simvastatin.",
        "alternative_drugs": ["Pravastatin", "Rosuvastatin", "Fluvastatin"],
        "monitoring_required": True,
        "cpic_guideline": "CPIC Guideline for Simvastatin and SLCO1B1 — DOI: 10.1002/cpt.205",
    },
    ("AZATHIOPRINE", "PM"): {
        "action": "Contraindicated — Use Alternative",
        "dosing_guidance": "Start with 10% of standard dose OR switch to mycophenolate mofetil. Monitor CBC twice weekly.",
        "alternative_drugs": ["Mycophenolate Mofetil", "Cyclosporine"],
        "monitoring_required": True,
        "cpic_guideline": "CPIC Guideline for Thiopurines and TPMT/NUDT15 — DOI: 10.1002/cpt.1681",
    },
    ("FLUOROURACIL", "PM"): {
        "action": "Contraindicated — Life-Threatening Toxicity",
        "dosing_guidance": "Avoid 5-FU and capecitabine. If no alternatives, reduce dose by ≥50% with intensive monitoring.",
        "alternative_drugs": ["Irinotecan (if applicable)", "Oxaliplatin-based regimen"],
        "monitoring_required": True,
        "cpic_guideline": "CPIC Guideline for Fluoropyrimidines and DPYD — DOI: 10.1002/cpt.1930",
    },
}

def get_clinical_rec(drug: str, phenotype: str) -> dict:
    key = (drug, phenotype)
    default = {
        "action": "Standard Dosing",
        "dosing_guidance": "No dose adjustment required based on current pharmacogenomic profile.",
        "alternative_drugs": [],
        "monitoring_required": False,
        "cpic_guideline": f"See CPIC guidelines at cpicpgx.org for {drug}",
    }
    return CLINICAL_RECS.get(key, default)

# ─── BIOLOGICAL MECHANISM EXPLANATIONS ───────────────────────────────────────
MECHANISMS = {
    "CYP2D6": "CYP2D6 is a cytochrome P450 enzyme in the liver responsible for metabolizing ~25% of all clinical drugs. It oxidizes opioids (codeine→morphine), antidepressants, and beta-blockers.",
    "CYP2C19": "CYP2C19 catalyzes the bioactivation of clopidogrel to its active thiol metabolite, which irreversibly inhibits platelet P2Y12 receptors. Loss of function abolishes antiplatelet effect.",
    "CYP2C9": "CYP2C9 is the primary enzyme metabolizing S-warfarin, the more potent enantiomer. Reduced activity causes warfarin accumulation and dramatically elevated bleeding risk.",
    "SLCO1B1": "SLCO1B1 encodes OATP1B1, a hepatic uptake transporter. Variants (especially *5) reduce simvastatin clearance from blood into liver, causing plasma accumulation and myotoxicity.",
    "TPMT": "Thiopurine methyltransferase inactivates 6-mercaptopurine (azathioprine metabolite). TPMT-deficient patients shunt drug toward toxic thioguanine nucleotides that cause myelosuppression.",
    "DPYD": "Dihydropyrimidine dehydrogenase degrades 80-85% of administered fluorouracil. DPYD deficiency causes catastrophic drug accumulation leading to neutropenia, mucositis, and neurotoxicity.",
}
