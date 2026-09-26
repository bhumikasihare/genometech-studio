import streamlit as st

# 1. Page Configuration
st.set_page_config(
    page_title="OmicsExpress Automated Suite | GenomeTech Studio",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Instant URL Query-Parameter Router (?tool=1 to ?tool=8)
TOOL_ROUTES = {
    "1": "pages/tool1_gene_translator.py",
    "gene_translator": "pages/tool1_gene_translator.py",
    "2": "pages/tool2_primer_design.py",
    "primer_design": "pages/tool2_primer_design.py",
    "3": "pages/tool3_vcf_to_csv.py",
    "vcf_to_csv": "pages/tool3_vcf_to_csv.py",
    "4": "pages/tool4_variant_susceptibility.py",
    "variant_susceptibility": "pages/tool4_variant_susceptibility.py",
    "5": "pages/tool5_bulk_fasta_fetcher.py",
    "fasta_fetcher": "pages/tool5_bulk_fasta_fetcher.py",
    "6": "pages/tool6_clinical_genomic_merger.py",
    "clinical_merger": "pages/tool6_clinical_genomic_merger.py",
    "7": "pages/tool7_anova_posthoc.py",
    "anova_posthoc": "pages/tool7_anova_posthoc.py",
    "8": "pages/tool8_kaplan_meier.py",
    "kaplan_meier": "pages/tool8_kaplan_meier.py"
}

query_params = st.query_params
if "tool" in query_params:
    target_key = str(query_params["tool"]).strip().lower()
    if target_key in TOOL_ROUTES:
        st.switch_page(TOOL_ROUTES[target_key])

# 3. Deep Cosmic Indigo & Purple Theme CSS
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="collapsedControl"] {display: none;}
    section[data-testid="stSidebar"] {display: none;}

    .stApp {
        background: radial-gradient(circle at top right, #2e1065 0%, #1e1b4b 40%, #0f172a 80%, #090d16 100%);
        color: #f1f5f9 !important;
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3, h4, p, span, label, li {
        color: #f1f5f9 !important;
    }

    .gts-navbar {
        background: linear-gradient(90deg, #1e1b4b 0%, #4c1d95 50%, #1e3a8a 100%);
        padding: 1.4rem 2.2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid rgba(168, 85, 247, 0.45);
        box-shadow: 0 10px 30px rgba(124, 58, 237, 0.3);
    }
    .gts-brand {
        font-size: 1.65rem;
        font-weight: 800;
        letter-spacing: 0.5px;
        color: #ffffff !important;
    }
    .gts-sub {
        color: #38bdf8 !important;
        margin-left: 12px;
        font-size: 1rem;
        font-weight: 600;
    }
    .gts-badge {
        background: linear-gradient(135deg, #7c3aed, #2563eb);
        border: 1px solid #c084fc;
        color: #ffffff !important;
        padding: 7px 18px;
        border-radius: 999px;
        font-size: 0.88rem;
        font-weight: 700;
        box-shadow: 0 0 15px rgba(168, 85, 247, 0.5);
    }

    .tool-card {
        background: rgba(30, 27, 75, 0.65);
        border: 1px solid rgba(139, 92, 246, 0.4);
        border-radius: 14px;
        padding: 1.4rem;
        margin-bottom: 0.8rem;
        min-height: 185px;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
    }
    .tool-tag {
        display: inline-block;
        background: rgba(56, 189, 248, 0.15);
        border: 1px solid rgba(56, 189, 248, 0.45);
        color: #38bdf8 !important;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 999px;
        margin-bottom: 8px;
    }

    .stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #7c3aed 0%, #2563eb 100%) !important;
        color: white !important;
        border: 1px solid #a855f7 !important;
        border-radius: 9px !important;
        font-weight: 700 !important;
        padding: 0.6rem 1.2rem !important;
        margin-bottom: 1.4rem !important;
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.35) !important;
    }
    .stButton > button:hover {
        box-shadow: 0 6px 22px rgba(168, 85, 247, 0.65) !important;
        transform: translateY(-1px);
    }
</style>

<div class="gts-navbar">
    <div>
        <span class="gts-brand">🧬 GenomeTech Studio</span>
        <span class="gts-sub">| OmicsExpress Automated Bioinformatics Suite</span>
    </div>
    <span class="gts-badge">🔥 Founding Lab Offer: <s>$100</s> $40 USD (First 20 Clients)</span>
</div>
""", unsafe_allow_html=True)

st.markdown("### 🚀 Select an Automated Micro-Tool Pipeline to Launch")
st.markdown(
    "All 8 tools include **live dataset previews**, **built-in demo datasets**, **cross-platform Windows & macOS Excel compatibility (`UTF-8-BOM`)**, "
    "and **instant self-serve unlock**."
)

TOOLS_META = [
    ("Tool #1 • Nomenclature & Annotation", "🧬 Universal Gene ID Translator",
     "Convert up to 50,000 Ensembl, Symbol, or Entrez IDs across model organisms with genomic coordinates, UniProt links & Excel date-corruption guard.",
     "pages/tool1_gene_translator.py", "Launch Tool #1: Gene ID Translator"),
    ("Tool #2 • Wet-Lab PCR & qPCR", "🧪 Automated Batch Primer Designer",
     "Design ranked Forward & Reverse primer pairs with binding coordinates, 3' ΔG stability, SYBR Green amplicon melt Tm, and vendor synthesis sheets.",
     "pages/tool2_primer_design.py", "Launch Tool #2: Batch Primer Designer"),
    ("Tool #3 • NGS Variant Calling", "📄 VCF to Clinical CSV Converter",
     "Unpack complex multi-sample .vcf files into clean Excel tables with Genotype, Read Depth (DP), VAF %, SnpEff/VEP impact, and ClinVar calls.",
     "pages/tool3_vcf_to_csv.py", "Launch Tool #3: VCF to Clinical CSV"),
    ("Tool #4 • Clinical Genetics & ACMG", "🛡️ Variant Susceptibility & Pathogenicity",
     "Screen candidate variants against ClinVar, ACMG SF v3.2, OncoKB & CPIC to flag Tier 1 high-risk markers, ACMG codes, and surveillance protocols.",
     "pages/tool4_variant_susceptibility.py", "Launch Tool #4: Variant Susceptibility"),
    ("Tool #5 • Sequence Retrieval & QC", "📥 Bulk NCBI & Ensembl FASTA Fetcher",
     "Retrieve compiled multi-FASTA nucleotide or protein sequences from RefSeq & Ensembl IDs with ORF start/stop audits and cloning restriction screens.",
     "pages/tool5_bulk_fasta_fetcher.py", "Launch Tool #5: Bulk FASTA Fetcher"),
    ("Tool #6 • Translational Data Curation", "🔗 Clinical & Genomic Dataset Merger",
     "Harmonize mismatched patient chart IDs and RNA-seq sample barcodes, rescue tumor/normal specimen tags, and output DESeq2-synchronized matrices.",
     "pages/tool6_clinical_genomic_merger.py", "Launch Tool #6: Clinical & Genomic Merger"),
    ("Tool #7 • Biostatistics & Figures", "📊 Automated ANOVA, Post-Hoc & 4-Plot Suite",
     "Run One-Way ANOVA, Welch's, or Kruskal-Wallis with Tukey/Games-Howell/Dunn Post-Hoc tests, Shapiro-Wilk/Levene audits & 4 vector SVG figures.",
     "pages/tool7_anova_posthoc.py", "Launch Tool #7: ANOVA & Post-Hoc Suite"),
    ("Tool #8 • Clinical Survival Oncology", "📈 Kaplan-Meier Survival & HR Suite",
     "Generate annotated survival curves with 95% CI ribbons, Number-at-Risk tables, Mantel-Cox Log-Rank P-values, RMST, and batch Hazard Ratio screens.",
     "pages/tool8_kaplan_meier.py", "Launch Tool #8: Kaplan-Meier Plotter")
]

for row_idx in range(0, 8, 2):
    cols = st.columns(2)
    for col_idx in range(2):
        tag, title, desc, page_path, btn_label = TOOLS_META[row_idx + col_idx]
        with cols[col_idx]:
            st.markdown(f"""
            <div class="tool-card">
                <span class="tool-tag">{tag}</span>
                <h4 style="margin: 4px 0 8px 0; color: #ffffff !important;">{title}</h4>
                <p style="font-size: 0.9rem; color: #cbd5e1 !important; margin: 0;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(btn_label, key=f"btn_{row_idx + col_idx}"):
                st.switch_page(page_path)