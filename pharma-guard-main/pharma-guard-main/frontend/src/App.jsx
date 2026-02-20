import { useState, useCallback, useRef } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

const SUPPORTED_DRUGS = ["CODEINE", "WARFARIN", "CLOPIDOGREL", "SIMVASTATIN", "AZATHIOPRINE", "FLUOROURACIL"];

const RISK_COLORS = {
  "Safe":          { bg: "#dcfce7", border: "#16a34a", text: "#15803d", dot: "#22c55e" },
  "Adjust Dosage": { bg: "#fef9c3", border: "#ca8a04", text: "#a16207", dot: "#eab308" },
  "Toxic":         { bg: "#fee2e2", border: "#dc2626", text: "#b91c1c", dot: "#ef4444" },
  "Ineffective":   { bg: "#ffedd5", border: "#ea580c", text: "#c2410c", dot: "#f97316" },
  "Unknown":       { bg: "#f1f5f9", border: "#64748b", text: "#475569", dot: "#94a3b8" },
};

const SEVERITY_COLORS = {
  none:     "#22c55e",
  low:      "#84cc16",
  moderate: "#eab308",
  high:     "#f97316",
  critical: "#ef4444",
};

function RiskBadge({ label }) {
  const c = RISK_COLORS[label] || RISK_COLORS["Unknown"];
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 6,
      background: c.bg, border: `1.5px solid ${c.border}`,
      color: c.text, borderRadius: 8, padding: "4px 12px",
      fontSize: 13, fontWeight: 700, letterSpacing: "0.02em"
    }}>
      <span style={{ width: 8, height: 8, borderRadius: "50%", background: c.dot, display: "inline-block" }} />
      {label}
    </span>
  );
}

function ConfidenceBar({ score }) {
  const pct = Math.round(score * 100);
  const color = pct >= 90 ? "#22c55e" : pct >= 70 ? "#eab308" : "#f97316";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <div style={{ flex: 1, height: 8, background: "#e2e8f0", borderRadius: 4, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 4, transition: "width 1s ease" }} />
      </div>
      <span style={{ fontSize: 13, fontWeight: 700, color, minWidth: 36 }}>{pct}%</span>
    </div>
  );
}

function InfoCard({ title, children, accent = "#0d6e6e" }) {
  const [open, setOpen] = useState(true);
  return (
    <div style={{ border: `1px solid #e2e8f0`, borderRadius: 12, overflow: "hidden", marginBottom: 12 }}>
      <button onClick={() => setOpen(o => !o)} style={{
        width: "100%", padding: "14px 18px", background: "#f8fafc",
        border: "none", borderBottom: open ? "1px solid #e2e8f0" : "none",
        display: "flex", justifyContent: "space-between", alignItems: "center",
        cursor: "pointer", fontWeight: 700, fontSize: 14, color: "#1e293b"
      }}>
        <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ width: 3, height: 18, background: accent, borderRadius: 2, display: "inline-block" }} />
          {title}
        </span>
        <span style={{ color: "#94a3b8", fontSize: 18 }}>{open ? "▲" : "▼"}</span>
      </button>
      {open && <div style={{ padding: "16px 18px", background: "#fff" }}>{children}</div>}
    </div>
  );
}

function ResultCard({ result }) {
  const risk = result.risk_assessment;
  const profile = result.pharmacogenomic_profile;
  const rec = result.clinical_recommendation;
  const llm = result.llm_generated_explanation;
  const qm = result.quality_metrics;

  const sevColor = SEVERITY_COLORS[risk.severity] || "#94a3b8";

  return (
    <div style={{
      background: "#fff", borderRadius: 16, padding: 24,
      boxShadow: "0 2px 20px rgba(0,0,0,0.08)", marginBottom: 24,
      border: `2px solid ${RISK_COLORS[risk.risk_label]?.border || "#e2e8f0"}`
    }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20, flexWrap: "wrap", gap: 12 }}>
        <div>
          <div style={{ fontSize: 11, color: "#94a3b8", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 4 }}>Drug Analysis</div>
          <div style={{ fontSize: 26, fontWeight: 800, color: "#0f172a" }}>{result.drug}</div>
          <div style={{ fontSize: 13, color: "#64748b", marginTop: 2 }}>Patient: {result.patient_id}</div>
        </div>
        <div style={{ textAlign: "right" }}>
          <RiskBadge label={risk.risk_label} />
          <div style={{ marginTop: 8, fontSize: 12, color: "#64748b" }}>
            Severity: <span style={{ fontWeight: 700, color: sevColor }}>{risk.severity.toUpperCase()}</span>
          </div>
        </div>
      </div>

      {/* Confidence */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 12, color: "#64748b", marginBottom: 6, fontWeight: 600 }}>Confidence Score</div>
        <ConfidenceBar score={risk.confidence_score} />
      </div>

      {/* Genomic Profile */}
      <InfoCard title="Pharmacogenomic Profile" accent="#0d6e6e">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: 12, marginBottom: 14 }}>
          {[
            { label: "Primary Gene", value: profile.primary_gene },
            { label: "Diplotype", value: profile.diplotype },
            { label: "Phenotype", value: profile.phenotype },
          ].map(item => (
            <div key={item.label} style={{ background: "#f8fafc", borderRadius: 8, padding: "10px 14px" }}>
              <div style={{ fontSize: 11, color: "#94a3b8", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.05em" }}>{item.label}</div>
              <div style={{ fontSize: 15, fontWeight: 700, color: "#0f172a" }}>{item.value}</div>
            </div>
          ))}
        </div>
        {profile.detected_variants.length > 0 && (
          <>
            <div style={{ fontSize: 12, fontWeight: 700, color: "#475569", marginBottom: 8 }}>Detected Variants</div>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                <thead>
                  <tr style={{ background: "#f1f5f9" }}>
                    {["rsID", "Gene", "Star Allele", "Chrom", "Position", "Genotype"].map(h => (
                      <th key={h} style={{ padding: "8px 10px", textAlign: "left", color: "#64748b", fontWeight: 600, whiteSpace: "nowrap" }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {profile.detected_variants.map((v, i) => (
                    <tr key={i} style={{ borderTop: "1px solid #e2e8f0" }}>
                      <td style={{ padding: "8px 10px", fontFamily: "monospace", color: "#0d6e6e" }}>{v.rsid}</td>
                      <td style={{ padding: "8px 10px", fontWeight: 600 }}>{v.gene}</td>
                      <td style={{ padding: "8px 10px", fontFamily: "monospace" }}>{v.star_allele}</td>
                      <td style={{ padding: "8px 10px", color: "#64748b" }}>{v.chromosome}</td>
                      <td style={{ padding: "8px 10px", color: "#64748b" }}>{v.position.toLocaleString()}</td>
                      <td style={{ padding: "8px 10px", fontFamily: "monospace", fontWeight: 700 }}>{v.genotype}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </InfoCard>

      {/* Clinical Recommendation */}
      <InfoCard title="Clinical Recommendation" accent="#f0b429">
        <div style={{ background: "#fffbeb", border: "1px solid #fde68a", borderRadius: 8, padding: 14, marginBottom: 12 }}>
          <div style={{ fontSize: 12, color: "#92400e", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 4 }}>Action</div>
          <div style={{ fontSize: 15, fontWeight: 700, color: "#78350f" }}>{rec.action}</div>
        </div>
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: "#475569", marginBottom: 6 }}>Dosing Guidance</div>
          <p style={{ fontSize: 13, color: "#334155", lineHeight: 1.6, margin: 0 }}>{rec.dosing_guidance}</p>
        </div>
        {rec.alternative_drugs.length > 0 && (
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: "#475569", marginBottom: 6 }}>Alternative Drugs</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {rec.alternative_drugs.map(d => (
                <span key={d} style={{ background: "#dbeafe", color: "#1d4ed8", borderRadius: 6, padding: "3px 10px", fontSize: 12, fontWeight: 600 }}>{d}</span>
              ))}
            </div>
          </div>
        )}
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <span style={{
            fontSize: 12, padding: "4px 10px", borderRadius: 6, fontWeight: 600,
            background: rec.monitoring_required ? "#fef3c7" : "#dcfce7",
            color: rec.monitoring_required ? "#92400e" : "#15803d"
          }}>
            {rec.monitoring_required ? "⚠ Monitoring Required" : "✓ Routine Monitoring"}
          </span>
        </div>
        <div style={{ marginTop: 10, fontSize: 11, color: "#94a3b8" }}>📋 {rec.cpic_guideline}</div>
      </InfoCard>

      {/* AI Explanation */}
      <InfoCard title="AI-Generated Clinical Explanation" accent="#7c3aed">
        {[
          { label: "Summary", text: llm.summary },
          { label: "Biological Mechanism", text: llm.mechanism },
          { label: "Variant Impact", text: llm.variant_impact },
          { label: "Clinical Significance", text: llm.clinical_significance },
        ].map(item => (
          <div key={item.label} style={{ marginBottom: 14 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: "#6d28d9", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.05em" }}>{item.label}</div>
            <p style={{ fontSize: 13, color: "#334155", lineHeight: 1.7, margin: 0 }}>{item.text}</p>
          </div>
        ))}
      </InfoCard>

      {/* Quality Metrics */}
      <InfoCard title="Quality Metrics" accent="#0891b2">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 10 }}>
          {[
            { label: "VCF Parsed", value: qm.vcf_parsing_success ? "✓ Success" : "✗ Failed", ok: qm.vcf_parsing_success },
            { label: "Variants Found", value: qm.variants_detected },
            { label: "Genes Analyzed", value: qm.genes_analyzed.join(", ") || "—" },
          ].map(item => (
            <div key={item.label} style={{ background: "#f8fafc", borderRadius: 8, padding: "10px 14px" }}>
              <div style={{ fontSize: 11, color: "#94a3b8", marginBottom: 4, textTransform: "uppercase" }}>{item.label}</div>
              <div style={{ fontSize: 13, fontWeight: 700, color: item.ok === false ? "#dc2626" : item.ok === true ? "#16a34a" : "#0f172a" }}>{item.value}</div>
            </div>
          ))}
        </div>
        <div style={{ marginTop: 10, fontSize: 11, color: "#94a3b8" }}>Basis: {qm.confidence_basis}</div>
      </InfoCard>
    </div>
  );
}

export default function App() {
  const [vcfFile, setVcfFile] = useState(null);
  const [selectedDrugs, setSelectedDrugs] = useState([]);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [rawJson, setRawJson] = useState("");
  const [copied, setCopied] = useState(false);
  const fileRef = useRef();

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file?.name.endsWith(".vcf")) {
      setVcfFile(file);
      setError("");
    } else {
      setError("Please upload a .vcf file");
    }
  }, []);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file?.name.endsWith(".vcf")) {
      setVcfFile(file);
      setError("");
    } else {
      setError("Please upload a .vcf file");
    }
  };

  const toggleDrug = (drug) => {
    setSelectedDrugs(prev =>
      prev.includes(drug) ? prev.filter(d => d !== drug) : [...prev, drug]
    );
  };

  const handleAnalyze = async () => {
    if (!vcfFile) return setError("Please upload a VCF file first.");
    if (!selectedDrugs.length) return setError("Please select at least one drug.");

    setLoading(true);
    setError("");
    setResults([]);
    setRawJson("");

    const formData = new FormData();
    formData.append("vcf_file", vcfFile);
    formData.append("drugs", selectedDrugs.join(","));

    try {
      const res = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Server error" }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const data = await res.json();
      setResults(data);
      setRawJson(JSON.stringify(data, null, 2));
    } catch (e) {
      setError(`Analysis failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    const blob = new Blob([rawJson], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "pharma_guard_results.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(rawJson);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ minHeight: "100vh", background: "linear-gradient(135deg, #0a1628 0%, #0d4a4a 100%)", fontFamily: "'Inter', 'Segoe UI', sans-serif" }}>
      {/* Nav */}
      <nav style={{ background: "rgba(10,22,40,0.95)", backdropFilter: "blur(10px)", padding: "0 24px", position: "sticky", top: 0, zIndex: 50, borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
        <div style={{ maxWidth: 1100, margin: "0 auto", height: 64, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ width: 36, height: 36, background: "linear-gradient(135deg, #00b4a6, #0d6e6e)", borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18 }}>🧬</div>
            <div>
              <div style={{ color: "#fff", fontWeight: 800, fontSize: 18, letterSpacing: "-0.02em" }}>PharmaGuard</div>
              <div style={{ color: "#00b4a6", fontSize: 11, letterSpacing: "0.1em" }}>PHARMACOGENOMICS</div>
            </div>
          </div>
          <div style={{ color: "#64748b", fontSize: 13 }}>RIFT 2026 · HealthTech Track</div>
        </div>
      </nav>

      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "40px 24px 80px" }}>
        {/* Hero */}
        <div style={{ textAlign: "center", marginBottom: 48 }}>
          <div style={{ display: "inline-block", background: "rgba(0,180,166,0.15)", border: "1px solid rgba(0,180,166,0.3)", borderRadius: 20, padding: "4px 16px", fontSize: 12, color: "#00b4a6", letterSpacing: "0.1em", marginBottom: 16 }}>
            PRECISION MEDICINE · EXPLAINABLE AI
          </div>
          <h1 style={{ color: "#fff", fontSize: "clamp(28px, 5vw, 48px)", fontWeight: 900, letterSpacing: "-0.03em", margin: "0 0 16px", lineHeight: 1.1 }}>
            Pharmacogenomic<br /><span style={{ color: "#00b4a6" }}>Risk Prediction</span>
          </h1>
          <p style={{ color: "#94a3b8", fontSize: 16, maxWidth: 600, margin: "0 auto" }}>
            Upload patient VCF data to predict drug-specific risks based on genetic variants across 6 critical pharmacogenes.
          </p>
        </div>

        {/* Upload + Config Panel */}
        <div style={{ background: "#fff", borderRadius: 20, padding: 32, boxShadow: "0 4px 40px rgba(0,0,0,0.15)", marginBottom: 32 }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 32 }}>

            {/* VCF Upload */}
            <div>
              <h3 style={{ fontSize: 15, fontWeight: 700, color: "#0f172a", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ background: "#0d6e6e", color: "#fff", borderRadius: 6, width: 24, height: 24, display: "inline-flex", alignItems: "center", justifyContent: "center", fontSize: 13 }}>1</span>
                Upload VCF File
              </h3>
              <div
                onDrop={handleDrop}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onClick={() => fileRef.current.click()}
                style={{
                  border: `2px dashed ${dragOver ? "#0d6e6e" : vcfFile ? "#22c55e" : "#cbd5e1"}`,
                  borderRadius: 12, padding: "32px 20px",
                  textAlign: "center", cursor: "pointer",
                  background: dragOver ? "#f0fdf4" : vcfFile ? "#f0fdf4" : "#f8fafc",
                  transition: "all 0.2s ease"
                }}
              >
                <div style={{ fontSize: 36, marginBottom: 12 }}>{vcfFile ? "✅" : "📁"}</div>
                {vcfFile ? (
                  <>
                    <div style={{ fontWeight: 700, color: "#15803d", fontSize: 14 }}>{vcfFile.name}</div>
                    <div style={{ color: "#64748b", fontSize: 12, marginTop: 4 }}>{(vcfFile.size / 1024).toFixed(1)} KB — Click to change</div>
                  </>
                ) : (
                  <>
                    <div style={{ fontWeight: 600, color: "#374151", fontSize: 14 }}>Drag & drop VCF file here</div>
                    <div style={{ color: "#9ca3af", fontSize: 12, marginTop: 4 }}>or click to browse · Max 5MB · .vcf format</div>
                  </>
                )}
                <input ref={fileRef} type="file" accept=".vcf" onChange={handleFileChange} style={{ display: "none" }} />
              </div>
            </div>

            {/* Drug Selection */}
            <div>
              <h3 style={{ fontSize: 15, fontWeight: 700, color: "#0f172a", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ background: "#0d6e6e", color: "#fff", borderRadius: 6, width: 24, height: 24, display: "inline-flex", alignItems: "center", justifyContent: "center", fontSize: 13 }}>2</span>
                Select Drugs to Analyze
              </h3>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                {SUPPORTED_DRUGS.map(drug => {
                  const selected = selectedDrugs.includes(drug);
                  return (
                    <button
                      key={drug}
                      onClick={() => toggleDrug(drug)}
                      style={{
                        padding: "10px 12px", borderRadius: 10, border: `2px solid ${selected ? "#0d6e6e" : "#e2e8f0"}`,
                        background: selected ? "#0d6e6e" : "#f8fafc",
                        color: selected ? "#fff" : "#374151",
                        fontWeight: 600, fontSize: 12, cursor: "pointer",
                        transition: "all 0.15s ease", letterSpacing: "0.05em",
                        textAlign: "left"
                      }}
                    >
                      {selected ? "✓ " : ""}{drug}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div style={{ marginTop: 20, background: "#fee2e2", border: "1px solid #fca5a5", borderRadius: 10, padding: "12px 16px", color: "#b91c1c", fontSize: 13, fontWeight: 500 }}>
              ⚠ {error}
            </div>
          )}

          {/* Analyze Button */}
          <button
            onClick={handleAnalyze}
            disabled={loading || !vcfFile || !selectedDrugs.length}
            style={{
              marginTop: 24, width: "100%", padding: "16px", borderRadius: 12,
              background: loading || !vcfFile || !selectedDrugs.length
                ? "#e2e8f0"
                : "linear-gradient(135deg, #0d6e6e, #00b4a6)",
              color: loading || !vcfFile || !selectedDrugs.length ? "#94a3b8" : "#fff",
              border: "none", fontWeight: 800, fontSize: 16, cursor: loading ? "wait" : "pointer",
              transition: "all 0.2s ease", letterSpacing: "0.02em"
            }}
          >
            {loading ? (
              <span>⏳ Analyzing Pharmacogenomic Profile...</span>
            ) : (
              <span>🔬 Run PharmaGuard Analysis</span>
            )}
          </button>
        </div>

        {/* Results */}
        {results.length > 0 && (
          <div>
            {/* Results header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24, flexWrap: "wrap", gap: 12 }}>
              <div>
                <h2 style={{ color: "#fff", fontSize: 22, fontWeight: 800, margin: 0 }}>Analysis Results</h2>
                <p style={{ color: "#94a3b8", fontSize: 13, margin: "4px 0 0" }}>{results.length} drug{results.length > 1 ? "s" : ""} analyzed</p>
              </div>
              <div style={{ display: "flex", gap: 10 }}>
                <button onClick={handleCopy} style={{ padding: "10px 18px", borderRadius: 10, border: "1px solid rgba(255,255,255,0.2)", background: "rgba(255,255,255,0.1)", color: "#fff", cursor: "pointer", fontSize: 13, fontWeight: 600 }}>
                  {copied ? "✓ Copied!" : "📋 Copy JSON"}
                </button>
                <button onClick={handleDownload} style={{ padding: "10px 18px", borderRadius: 10, border: "none", background: "#00b4a6", color: "#fff", cursor: "pointer", fontSize: 13, fontWeight: 600 }}>
                  ⬇ Download JSON
                </button>
              </div>
            </div>

            {results.map((result, i) => (
              <ResultCard key={i} result={result} />
            ))}

            {/* Raw JSON */}
            <div style={{ background: "#0d1117", borderRadius: 16, padding: 24, marginTop: 8 }}>
              <div style={{ color: "#00b4a6", fontSize: 12, fontWeight: 700, letterSpacing: "0.1em", marginBottom: 12 }}>RAW JSON OUTPUT</div>
              <pre style={{ color: "#e2e8f0", fontSize: 11, lineHeight: 1.6, overflow: "auto", margin: 0, maxHeight: 400 }}>{rawJson}</pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
