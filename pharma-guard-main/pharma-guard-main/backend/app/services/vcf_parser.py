"""
VCF Parser — parses VCF 4.2 files and extracts pharmacogenomic variants.
"""
from typing import List, Dict, Tuple
import re
from app.models.schemas import DetectedVariant


def parse_vcf(content: str) -> Tuple[List[DetectedVariant], str, bool]:
    """
    Parse VCF file content and return (variants, patient_id, success).
    """
    variants: List[DetectedVariant] = []
    patient_id = "PATIENT_001"
    success = False

    lines = content.strip().splitlines()
    header_cols = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Extract patient ID from sample column header
        if line.startswith("#CHROM"):
            parts = line.split("\t")
            header_cols = parts
            if len(parts) > 9:
                patient_id = parts[9].strip()
            continue

        if line.startswith("#"):
            continue

        # Parse variant line
        parts = line.split("\t")
        if len(parts) < 9:
            continue

        chrom, pos, vid, ref, alt, qual, filt, info = parts[:8]
        fmt = parts[8] if len(parts) > 8 else "GT"
        sample = parts[9] if len(parts) > 9 else "0/0"

        # Parse FORMAT/sample for genotype
        fmt_fields = fmt.split(":")
        sample_fields = sample.split(":")
        genotype = "0/0"
        if "GT" in fmt_fields:
            gt_idx = fmt_fields.index("GT")
            if gt_idx < len(sample_fields):
                genotype = sample_fields[gt_idx]

        # Skip homozygous reference (not a variant of interest)
        if genotype in ("0/0", "0|0"):
            # Still include for known PGx positions even if ref
            pass

        # Parse INFO field
        info_dict: Dict[str, str] = {}
        for item in info.split(";"):
            if "=" in item:
                k, v = item.split("=", 1)
                info_dict[k.strip()] = v.strip()

        gene = info_dict.get("GENE", "")
        star = info_dict.get("STAR", "*1")
        rsid = info_dict.get("RS", vid if vid != "." else f"pos{pos}")

        if not gene:
            continue

        try:
            variant = DetectedVariant(
                rsid=rsid,
                gene=gene,
                star_allele=star,
                chromosome=chrom,
                position=int(pos),
                ref=ref,
                alt=alt,
                genotype=genotype,
            )
            variants.append(variant)
        except Exception:
            continue

    success = len(variants) > 0
    return variants, patient_id, success


def get_gene_variants(variants: List[DetectedVariant], gene: str) -> List[DetectedVariant]:
    return [v for v in variants if v.gene == gene]


def determine_diplotype(variants: List[DetectedVariant], gene: str) -> str:
    """
    Infer diplotype from detected variants for a given gene.
    Simplified: takes up to two star alleles (het = one of each, hom = both same).
    """
    gene_vars = get_gene_variants(variants, gene)
    if not gene_vars:
        return "*1/*1"  # Assume wildtype if no variants detected

    alleles = []
    for v in gene_vars:
        gt = v.genotype.replace("|", "/")
        parts = gt.split("/")
        # Heterozygous: one ref allele (*1) and one alt allele (star)
        if len(parts) == 2:
            if parts[0] == "0" and parts[1] == "1":
                alleles.append(("*1", v.star_allele))
            elif parts[0] == "1" and parts[1] == "1":
                alleles.append((v.star_allele, v.star_allele))
            elif parts[0] == "0" and parts[1] == "0":
                alleles.append(("*1", "*1"))
            else:
                alleles.append(("*1", v.star_allele))

    if not alleles:
        return "*1/*1"

    # Merge alleles: pick the highest-impact pair
    left_alleles = [a[0] for a in alleles]
    right_alleles = [a[1] for a in alleles]
    
    # Pick the most non-wildtype allele on each side
    def rank(a):
        from app.utils.knowledge_base import STAR_ALLELE_FUNCTION
        f = STAR_ALLELE_FUNCTION.get(a, "normal")
        return {"nonfunctional": 3, "decreased": 2, "increased": 1, "normal": 0}.get(f, 0)

    left = max(left_alleles, key=rank)
    right = max(right_alleles, key=rank)
    return f"{left}/{right}"
