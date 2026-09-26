import streamlit as st
import pandas as pd
import numpy as np
import urllib.parse

# 1. Page Configuration (Isolated Single-Tool View)
st.set_page_config(
    page_title="VCF to Clinical CSV | OmicsExpress",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Deep Blue & Purplish OmicsExpress Theme CSS
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

    code {
        background-color: rgba(139, 92, 246, 0.2) !important;
        color: #ddd6fe !important;
        border: 1px solid rgba(139, 92, 246, 0.4);
        padding: 2px 6px;
        border-radius: 5px;
    }

    .gts-navbar {
        background: linear-gradient(90deg, #1e1b4b 0%, #4c1d95 50%, #1e3a8a 100%);
        padding: 1.2rem 2rem;
        border-radius: 14px;
        margin-bottom: 1.8rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid rgba(168, 85, 247, 0.4);
        box-shadow: 0 8px 25px rgba(124, 58, 237, 0.25);
    }
    .gts-brand {
        font-size: 1.5rem;
        font-weight: 800;
        letter-spacing: 0.5px;
        color: #ffffff !important;
    }
    .gts-sub {
        color: #c4b5fd !important;
        margin-left: 12px;
        font-size: 0.95rem;
        font-weight: 500;
    }
    .gts-badge {
        background: linear-gradient(135deg, #7c3aed, #2563eb);
        border: 1px solid #c084fc;
        color: #ffffff !important;
        padding: 6px 16px;
        border-radius: 999px;
        font-size: 0.85rem;
        font-weight: 600;
        box-shadow: 0 0 12px rgba(168, 85, 247, 0.5);
    }

    [data-testid="stExpander"] {
        background-color: rgba(30, 27, 75, 0.65) !important;
        border: 1px solid rgba(139, 92, 246, 0.35) !important;
        border-radius: 12px !important;
    }
    [data-testid="stFileUploader"] {
        background-color: rgba(30, 27, 75, 0.5) !important;
        border: 1px dashed #8b5cf6 !important;
        border-radius: 12px !important;
        padding: 12px;
    }

    [data-testid="stMetric"] {
        background: rgba(30, 27, 75, 0.7);
        border: 1px solid rgba(139, 92, 246, 0.4);
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }

    .stButton > button {
        background: linear-gradient(90deg, #7c3aed 0%, #2563eb 100%) !important;
        color: white !important;
        border: 1px solid #a855f7 !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        padding: 0.6rem 1.5rem !important;
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.35) !important;
    }
    .stButton > button:hover {
        box-shadow: 0 6px 20px rgba(168, 85, 247, 0.6) !important;
        transform: translateY(-1px);
    }

    .blurred-table {
        filter: blur(8px);
        user-select: none;
        pointer-events: none;
        opacity: 0.55;
    }

    .paywall-overlay {
        text-align: center;
        background: linear-gradient(135deg, rgba(30, 27, 75, 0.95) 0%, rgba(59, 7, 100, 0.95) 100%);
        padding: 2.2rem;
        border-radius: 16px;
        border: 2px solid #a855f7;
        box-shadow: 0 15px 35px rgba(124, 58, 237, 0.35);
        max-width: 620px;
        margin: -70px auto 25px auto;
        position: relative;
        z-index: 20;
    }
</style>

<div class="gts-navbar">
    <div>
        <span class="gts-brand">🧬 GenomeTech Studio</span>
        <span class="gts-sub">| OmicsExpress Automated Suite</span>
    </div>
    <span class="gts-badge">⚡ Tool #3: VCF to Clinical CSV</span>
</div>
""", unsafe_allow_html=True)

if "is_unlocked_t3" not in st.session_state:
    st.session_state["is_unlocked_t3"] = False
if "locked_mode_t3" not in st.session_state:
    st.session_state["locked_mode_t3"] = None

# Callback that resets unlock & results ONLY when Core Pipeline Mode or Uploaded File changes
def reset_on_mode_change_t3():
    st.session_state["is_unlocked_t3"] = False
    st.session_state.pop("vcf_df_t3", None)
    st.session_state.pop("actionable_df_t3", None)
    st.session_state.pop("qc_df_t3", None)
    st.session_state.pop("stats_t3", None)

st.markdown("## VCF to Clinical CSV Converter")
st.markdown(
    "Transform raw, nested **Variant Call Format (`.vcf`)** files into clean, presentation-ready Excel/CSV tables. "
    "Automatically unpacks **`INFO` annotations (`ANN`, `CSQ`, `CLNSIG`, `gnomAD_AF`)**, **Transcript & Coding HGVS (`HGVSc` / `HGVSp`)**, "
    "and multi-sample **`FORMAT` genotypes (`GT:AD:DP:GQ`)** with **Excel Gene-Symbol Protection**."
)

with st.expander("📋 Required File Format & Clinical Features (.vcf, .txt, or .tsv)", expanded=True):
    st.markdown("""
    * **Accepted File Types:** Single-sample or multi-sample VCF v4.x files (`.vcf`, `.txt`, `.tsv`) from GATK, DeepVariant, Mutect2, SnpEff, Ensembl VEP, or ClinVar.
    * **Clinical & Wet-Lab Upgrades Included:**
      1. **Multi-Sample Selector:** Freely switch between sample columns (e.g., `TUMOR` vs. `NORMAL` or family trios) within your uploaded VCF.
      2. **Complete HGVS & Transcript Unpacking:** Extracts `Transcript_ID`, `Coding_DNA_Change (HGVSc)`, and `Protein_Change (HGVSp)`.
      3. **Population Frequency Filtering:** Extracts `gnomAD_AF` / population MAF so you can filter out common polymorphisms.
      4. **Microsoft Excel Gene-Date Guard:** Prevents Excel from auto-corrupting gene symbols like `MARCH1` or `SEPT2` into calendar dates (`01-Mar`).
    * **💻 Cross-Platform File Compatibility (Windows & Apple macOS):** All exported `.csv` tables use universal `UTF-8-BOM` encoding—double-click to open directly in **Microsoft Excel (Windows/Mac)**, **Apple Numbers**, **Google Sheets**, or load into **R / Python**. Sequence (`.fasta`) and vector figure (`.svg` / `.html`) outputs open natively in any text editor (**Notepad / Mac TextEdit**) or web browser (**Safari / Chrome / Edge**).
    * **Single-Mode License Note:** Each checkout unlocks your selected **Core VCF Parsing Pipeline Mode** across all samples in your uploaded VCF file. Switching the Core Pipeline Mode or uploading a new file starts a new run.
    """)

# ==========================================
# HELPER FUNCTIONS & DEMO MULTI-SAMPLE VCF
# ==========================================
DEMO_VCF_TEXT = """##fileformat=VCFv4.2
##reference=GRCh38.p14
##INFO=<ID=DP,Number=1,Type=Integer,Description="Total Depth">
##INFO=<ID=AF,Number=A,Type=Float,Description="Allele Frequency">
##INFO=<ID=GNOMAD_AF,Number=A,Type=Float,Description="gnomAD Population AF">
##INFO=<ID=GENE,Number=1,Type=String,Description="Gene Symbol">
##INFO=<ID=TRANSCRIPT,Number=1,Type=String,Description="Transcript ID">
##INFO=<ID=CONSEQ,Number=1,Type=String,Description="Variant Consequence">
##INFO=<ID=IMPACT,Number=1,Type=String,Description="Impact Tier">
##INFO=<ID=HGVSC,Number=1,Type=String,Description="Coding DNA Change">
##INFO=<ID=HGVSP,Number=1,Type=String,Description="Protein Change">
##INFO=<ID=CLNSIG,Number=1,Type=String,Description="ClinVar Clinical Significance">
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tTUMOR_SAMPLE_01\tNORMAL_CONTROL_01
chr17\t7675088\trs28934578\tC\tT\t99.0\tPASS\tDP=184;AF=0.489;GNOMAD_AF=0.00001;GENE=TP53;TRANSCRIPT=NM_000546.6;CONSEQ=missense_variant;IMPACT=HIGH;HGVSC=c.524G>A;HGVSP=p.Arg175His;CLNSIG=Pathogenic\tGT:AD:DP:GQ\t0/1:94,90:184:99\t0/0:160,0:160:99
chr17\t43094464\trs80357906\tAG\tA\t99.0\tPASS\tDP=142;AF=0.514;GNOMAD_AF=0.00004;GENE=BRCA1;TRANSCRIPT=NM_007294.4;CONSEQ=frameshift_variant;IMPACT=HIGH;HGVSC=c.68_69delAG;HGVSP=p.Glu23ValfsTer17;CLNSIG=Pathogenic\tGT:AD:DP:GQ\t0/1:69,73:142:99\t0/1:70,68:138:99
chr7\t55191822\trs121434568\tT\tG\t95.4\tPASS\tDP=210;AF=0.381;GNOMAD_AF=0.00000;GENE=EGFR;TRANSCRIPT=NM_005228.5;CONSEQ=missense_variant;IMPACT=MODERATE;HGVSC=c.2573T>G;HGVSP=p.Leu858Arg;CLNSIG=Pathogenic/Likely_pathogenic\tGT:AD:DP:GQ\t0/1:130,80:210:99\t0/0:190,0:190:99
chr7\t140753336\trs113488022\tA\tT\t99.0\tPASS\tDP=165;AF=0.497;GNOMAD_AF=0.00001;GENE=BRAF;TRANSCRIPT=NM_004333.6;CONSEQ=missense_variant;IMPACT=MODERATE;HGVSC=c.1799T>A;HGVSP=p.Val600Glu;CLNSIG=Pathogenic\tGT:AD:DP:GQ\t0/1:83,82:165:99\t0/0:145,0:145:99
chr12\t25245350\trs121913529\tC\tA\t88.2\tPASS\tDP=120;AF=0.450;GNOMAD_AF=0.00002;GENE=KRAS;TRANSCRIPT=NM_004985.5;CONSEQ=missense_variant;IMPACT=MODERATE;HGVSC=c.35G>T;HGVSP=p.Gly12Val;CLNSIG=Pathogenic\tGT:AD:DP:GQ\t0/1:66,54:120:95\t0/0:110,0:110:99
chr10\t87933147\trs121909224\tC\tT\t92.0\tPASS\tDP=96;AF=0.989;GNOMAD_AF=0.00000;GENE=PTEN;TRANSCRIPT=NM_000314.8;CONSEQ=stop_gained;IMPACT=HIGH;HGVSC=c.388C>T;HGVSP=p.Arg130Ter;CLNSIG=Pathogenic\tGT:AD:DP:GQ\t1/1:1,95:96:99\t0/1:52,48:100:99
chr2\t240981202\trs145982101\tG\tA\t86.0\tPASS\tDP=118;AF=0.474;GNOMAD_AF=0.00030;GENE=SEPT2;TRANSCRIPT=NM_004404.5;CONSEQ=missense_variant;IMPACT=MODERATE;HGVSC=c.412G>A;HGVSP=p.Val138Ile;CLNSIG=Uncertain_significance\tGT:AD:DP:GQ\t0/1:62,56:118:88\t0/1:60,55:115:88
chr4\t164455120\trs99881122\tC\tG\t79.5\tPASS\tDP=104;AF=0.490;GNOMAD_AF=0.00120;GENE=MARCH1;TRANSCRIPT=NM_017923.4;CONSEQ=missense_variant;IMPACT=MODERATE;HGVSC=c.215C>G;HGVSP=p.Ser72Cys;CLNSIG=Likely_pathogenic\tGT:AD:DP:GQ\t0/1:53,51:104:85\t0/0:98,0:98:99
chr2\t25234373\trs75030202\tG\tA\t62.1\tPASS\tDP=64;AF=0.484;GNOMAD_AF=0.04500;GENE=DNMT3A;TRANSCRIPT=NM_022552.5;CONSEQ=synonymous_variant;IMPACT=LOW;HGVSC=c.915G>A;HGVSP=p.Pro305=;CLNSIG=Benign\tGT:AD:DP:GQ\t0/1:33,31:64:72\t0/1:35,30:65:75
chr1\t114713908\trs11554290\tC\tT\t34.5\tLowQual\tDP=22;AF=0.181;GNOMAD_AF=0.12000;GENE=NRAS;TRANSCRIPT=NM_002524.5;CONSEQ=intron_variant;IMPACT=MODIFIER;HGVSC=c.111+45C>T;HGVSP=N/A;CLNSIG=Benign\tGT:AD:DP:GQ\t0/1:18,4:22:35\t0/0:25,0:25:40
"""

def detect_vcf_samples(raw_text):
    for line in raw_text.splitlines():
        line = line.strip()
        if line.startswith("#CHROM") or line.startswith("CHROM"):
            cols = line.lstrip("#").split("\t")
            if len(cols) == 1:
                cols = line.lstrip("#").split()
            if len(cols) > 9:
                return cols[9:]
    return ["SAMPLE_01"]

def classify_variant(ref, alt):
    ref_c = str(ref).upper()
    alt_c = str(alt).split(",")[0].upper()
    if len(ref_c) == 1 and len(alt_c) == 1:
        return "SNV"
    elif len(alt_c) > len(ref_c):
        return "Insertion"
    elif len(ref_c) > len(alt_c):
        return "Deletion"
    return "MNV / Complex"

def is_transition(ref, alt):
    pair = {str(ref).upper(), str(alt).split(",")[0].upper()}
    return pair == {"A", "G"} or pair == {"C", "T"}

def parse_vcf_content(raw_text, selected_sample_idx=0):
    meta_lines = 0
    ref_genome = "Unspecified"
    data_rows = []

    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("##"):
            meta_lines += 1
            if line.lower().startswith("##reference="):
                ref_genome = line.split("=", 1)[1]
            continue
        if line.startswith("#CHROM") or line.startswith("CHROM"):
            continue

        parts = line.split("\t") if "\t" in line else line.split()
        if len(parts) < 8:
            continue

        chrom, pos, var_id, ref, alt, qual, flt, info_str = parts[:8]
        fmt_str = parts[8] if len(parts) > 8 else ""
        sample_col_pos = 9 + selected_sample_idx
        sample_str = parts[sample_col_pos] if len(parts) > sample_col_pos else (parts[9] if len(parts) > 9 else "")

        # Parse INFO dictionary
        info_dict = {}
        for item in info_str.split(";"):
            if "=" in item:
                k, v = item.split("=", 1)
                info_dict[k.upper()] = v
            else:
                info_dict[item.upper()] = "True"

        # Extract Functional Annotations (supports direct tags + SnpEff ANN + Ensembl VEP CSQ)
        gene_sym = info_dict.get("GENE", info_dict.get("SYMBOL", "N/A"))
        transcript_id = info_dict.get("TRANSCRIPT", info_dict.get("FEATURE", "N/A"))
        conseq = info_dict.get("CONSEQ", info_dict.get("EFF", "N/A"))
        impact = info_dict.get("IMPACT", "N/A")
        hgvsc = info_dict.get("HGVSC", "N/A")
        hgvsp = info_dict.get("HGVSP", info_dict.get("AA", "N/A"))
        clnsig = info_dict.get("CLNSIG", "Not_Reported")

        # Population AF (gnomAD / 1000G / ExAC)
        pop_af_raw = info_dict.get("GNOMAD_AF", info_dict.get("AF_POPMAX", info_dict.get("MAX_AF", info_dict.get("MAF", "0.0"))))
        try:
            pop_af = round(float(str(pop_af_raw).split(",")[0]), 6)
        except ValueError:
            pop_af = 0.0

        ann_raw = info_dict.get("ANN", info_dict.get("CSQ", ""))
        if ann_raw:
            first_ann = ann_raw.split(",")[0].split("|")
            if len(first_ann) >= 4:
                if conseq == "N/A" and first_ann[1]:
                    conseq = first_ann[1]
                if impact == "N/A" and first_ann[2]:
                    impact = first_ann[2]
                if gene_sym == "N/A" and first_ann[3]:
                    gene_sym = first_ann[3]
            if len(first_ann) >= 7 and transcript_id == "N/A" and first_ann[6]:
                transcript_id = first_ann[6]
            if len(first_ann) >= 10 and hgvsc == "N/A" and first_ann[9]:
                hgvsc = first_ann[9]
            if len(first_ann) >= 11 and hgvsp == "N/A" and first_ann[10]:
                hgvsp = first_ann[10]

        # Parse FORMAT & Selected Sample Column
        fmt_map = {}
        if fmt_str and sample_str:
            f_keys = fmt_str.split(":")
            s_vals = sample_str.split(":")
            for k, v in zip(f_keys, s_vals):
                fmt_map[k.upper()] = v

        gt_raw = fmt_map.get("GT", "./.")
        gt_norm = gt_raw.replace("|", "/")
        if gt_norm in ("0/1", "1/0", "0/2", "1/2"):
            zygosity = "Heterozygous (0/1)"
        elif gt_norm in ("1/1", "2/2"):
            zygosity = "Homozygous Alt (1/1)"
        elif gt_norm == "0/0":
            zygosity = "Homozygous Ref (0/0)"
        else:
            zygosity = f"Uncalled/Other ({gt_raw})"

        dp_val = fmt_map.get("DP", info_dict.get("DP", "0"))
        try:
            dp_int = int(float(dp_val.split(",")[0]))
        except ValueError:
            dp_int = 0

        ad_raw = fmt_map.get("AD", "")
        ref_reads, alt_reads = 0, 0
        if "," in ad_raw:
            ad_parts = ad_raw.split(",")
            try:
                ref_reads = int(ad_parts[0])
                alt_reads = sum(int(x) for x in ad_parts[1:] if x.isdigit())
            except ValueError:
                pass

        af_info = fmt_map.get("AF", info_dict.get("AF", ""))
        if (ref_reads + alt_reads) > 0:
            vaf_pct = round((alt_reads / (ref_reads + alt_reads)) * 100.0, 2)
        elif af_info:
            try:
                vaf_pct = round(float(af_info.split(",")[0]) * 100.0, 2)
            except ValueError:
                vaf_pct = 0.0
        else:
            vaf_pct = 0.0

        try:
            qual_float = round(float(qual), 1) if qual != "." else 0.0
        except ValueError:
            qual_float = 0.0

        gq_val = fmt_map.get("GQ", "N/A")
        var_type = classify_variant(ref, alt)
        multi_allelic = "Yes" if "," in str(alt) else "No"

        data_rows.append({
            "Chromosome": chrom,
            "Position (bp)": int(pos) if pos.isdigit() else pos,
            "Variant_ID (rsID)": var_id if var_id != "." else "Novel",
            "Ref_Allele": ref,
            "Alt_Allele": alt,
            "Base_Change": f"{ref}>{alt}",
            "Variant_Class": var_type,
            "Multi_Allelic": multi_allelic,
            "Gene_Symbol": gene_sym,
            "Transcript_ID": transcript_id,
            "Consequence": conseq,
            "Impact_Tier": impact,
            "Coding_DNA_Change (HGVSc)": hgvsc,
            "Protein_Change (HGVSp)": hgvsp,
            "ClinVar_Significance": clnsig,
            "gnomAD_Pop_AF": pop_af,
            "Zygosity_Call": zygosity,
            "Total_Read_Depth (DP)": dp_int,
            "Ref_Reads": ref_reads,
            "Alt_Reads": alt_reads,
            "VAF (%)": vaf_pct,
            "Phred_Quality (QUAL)": qual_float,
            "Genotype_Quality (GQ)": gq_val,
            "Filter_Status": flt,
            "Raw_INFO_String": info_str
        })

    return pd.DataFrame(data_rows), meta_lines, ref_genome

# ==========================================
# STEP 2: VCF INPUT & DEMO DATASET
# ==========================================
col_up, col_demo = st.columns([3, 1])
with col_up:
    uploaded_file = st.file_uploader(
        "Upload your Variant Call File (.vcf, .txt, or .tsv)",
        type=["vcf", "txt", "tsv"],
        on_change=reset_on_mode_change_t3
    )
with col_demo:
    st.write("")
    st.write("")
    use_sample = st.checkbox("🧪 Load Demo Clinical VCF Dataset", value=False, on_change=reset_on_mode_change_t3)

raw_vcf_text = None
if uploaded_file is not None:
    raw_vcf_text = uploaded_file.read().decode("utf-8", errors="ignore")
elif use_sample:
    raw_vcf_text = DEMO_VCF_TEXT

# ==========================================
# STEP 3: CORE PARSING PIPELINE & QC SLIDERS
# ==========================================
if raw_vcf_text is not None:
    st.markdown("### ⚙️ Configure Clinical Parsing Pipeline & Quality Filters")

    detected_samples = detect_vcf_samples(raw_vcf_text)

    mp1, mp2 = st.columns([2, 1])
    with mp1:
        # Core Pipeline Mode (ONLY switching this or uploading a new file resets the paywall!)
        pipeline_mode = st.selectbox(
            "1. Core VCF Parsing Pipeline Mode (Switching pipeline mode starts a new run):",
            [
                "Clinical Germline Panel (Zygosity, ClinVar, Transcript, HGVSc/p, gnomAD AF)",
                "Somatic / Oncology Variant Calling (Tumor VAF %, Allelic Depth AD, Somatic QC)",
                "Annotated SnpEff / Ensembl VEP Unpacker (Gene, Transcript, Consequence, HGVS, Impact)",
                "Complete Comprehensive VCF Flattener (All Clinical, Read-Depth & Raw Columns)"
            ],
            on_change=reset_on_mode_change_t3
        )
    with mp2:
        # Target Sample Selector (Free to switch between Tumor/Normal or Trio samples inside the same VCF!)
        selected_sample_name = st.selectbox(
            "2. Target Sample Column in VCF (Free to switch):",
            detected_samples,
            index=0,
            help="Switch between samples (e.g. Tumor vs Normal or Family Trio) within your uploaded VCF without resetting your unlock."
        )
        selected_sample_idx = detected_samples.index(selected_sample_name)

    # Fine-tuning QC Sliders (Adjusting these within the same pipeline mode is free!)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**3. Variant Filter & Type Selection**")
        pass_only = st.selectbox("Filter Status Cutoff:", ["PASS Variants Only", "Include All Variants (PASS + LowQual)"])
        var_class_filter = st.selectbox("Variant Class Filter:", ["All Variants (SNVs + Indels)", "SNVs Only", "Indels (Insertions/Deletions) Only"])
        exclude_hom_ref = st.checkbox("Exclude Homozygous Reference (0/0) Calls", value=True)

    with c2:
        st.markdown("**4. Read Depth, VAF (%) & Population AF**")
        min_dp = st.slider("Minimum Total Read Depth (DP ≥):", 0, 150, 20, 5)
        min_vaf = st.slider("Minimum Variant Allele Freq (VAF % ≥):", 0.0, 50.0, 5.0, 1.0)
        max_pop_af = st.slider(
            "Max Population AF Cutoff (gnomAD ≤):",
            0.000, 1.000, 1.000, 0.005,
            help="Set to 0.01 (1%) or 0.005 (0.5%) to filter out common polymorphisms and keep only rare clinical variants."
        )

    with c3:
        st.markdown("**5. Quality & Microsoft Excel Protection**")
        min_qual = st.slider("Minimum Phred Quality Score (QUAL ≥):", 0.0, 100.0, 30.0, 5.0)
        sort_by_col = st.selectbox("Sort Output Table By:", ["VAF (%) - Highest First", "Total_Read_Depth (DP) - Highest First", "Chromosomal Position"])
        excel_gene_guard = st.checkbox(
            "🛡️ Enable Excel Gene-Name Guard (Protects MARCH1 / SEPT2)",
            value=False,
            help="Formats gene symbols as explicit Excel strings (=\"GENE\") in the downloaded CSV so Microsoft Excel never converts MARCH1 or SEPT2 into calendar dates."
        )

    # Lock signature depends ONLY on the file and Core VCF Parsing Pipeline Mode
    current_file_sig = uploaded_file.name if uploaded_file is not None else "demo_vcf"
    current_mode_sig = f"{current_file_sig}|{pipeline_mode}"

    # ==========================================
    # STEP 4: RUN VCF PARSER & CLINICAL FORMATTER
    # ==========================================
    if st.button("🚀 Run VCF to Clinical CSV Conversion"):
        if st.session_state["locked_mode_t3"] is not None and st.session_state["locked_mode_t3"] != current_mode_sig:
            st.session_state["is_unlocked_t3"] = False
        st.session_state["locked_mode_t3"] = current_mode_sig

        with st.spinner("Stripping VCF meta-headers, unpacking INFO/FORMAT fields, and computing clinical metrics..."):
            parsed_df, meta_cnt, ref_build = parse_vcf_content(raw_vcf_text, selected_sample_idx)

            if parsed_df.empty:
                st.error("No valid variant rows found. Please verify your VCF file contains standard tab-separated variant records.")
            else:
                total_raw_variants = len(parsed_df)

                flt_df = parsed_df.copy()
                if pass_only == "PASS Variants Only":
                    flt_df = flt_df[flt_df["Filter_Status"].str.upper() == "PASS"]
                if exclude_hom_ref:
                    flt_df = flt_df[~flt_df["Zygosity_Call"].str.startswith("Homozygous Ref")]
                if var_class_filter == "SNVs Only":
                    flt_df = flt_df[flt_df["Variant_Class"] == "SNV"]
                elif var_class_filter == "Indels (Insertions/Deletions) Only":
                    flt_df = flt_df[flt_df["Variant_Class"].isin(["Insertion", "Deletion"])]

                flt_df = flt_df[
                    (flt_df["Total_Read_Depth (DP)"] >= min_dp) &
                    (flt_df["VAF (%)"] >= min_vaf) &
                    (flt_df["Phred_Quality (QUAL)"] >= min_qual) &
                    (flt_df["gnomAD_Pop_AF"] <= max_pop_af)
                ]

                if sort_by_col == "VAF (%) - Highest First":
                    flt_df = flt_df.sort_values(by="VAF (%)", ascending=False)
                elif sort_by_col == "Total_Read_Depth (DP) - Highest First":
                    flt_df = flt_df.sort_values(by="Total_Read_Depth (DP)", ascending=False)

                if excel_gene_guard:
                    flt_df["Gene_Symbol"] = flt_df["Gene_Symbol"].apply(lambda g: f'="{g}"' if g != "N/A" else g)

                # Select tailored column view based on chosen Core Pipeline Mode
                if "Clinical Germline" in pipeline_mode:
                    cols_order = [
                        "Chromosome", "Position (bp)", "Variant_ID (rsID)", "Gene_Symbol",
                        "Transcript_ID", "Base_Change", "Variant_Class", "Zygosity_Call",
                        "ClinVar_Significance", "Impact_Tier", "Consequence",
                        "Coding_DNA_Change (HGVSc)", "Protein_Change (HGVSp)",
                        "gnomAD_Pop_AF", "Total_Read_Depth (DP)", "VAF (%)", "Phred_Quality (QUAL)", "Filter_Status"
                    ]
                elif "Somatic / Oncology" in pipeline_mode:
                    cols_order = [
                        "Chromosome", "Position (bp)", "Gene_Symbol", "Transcript_ID",
                        "Base_Change", "Variant_Class", "VAF (%)", "Ref_Reads", "Alt_Reads",
                        "Total_Read_Depth (DP)", "Consequence", "Impact_Tier",
                        "Coding_DNA_Change (HGVSc)", "Protein_Change (HGVSp)",
                        "ClinVar_Significance", "gnomAD_Pop_AF", "Filter_Status"
                    ]
                elif "SnpEff / Ensembl VEP" in pipeline_mode:
                    cols_order = [
                        "Gene_Symbol", "Transcript_ID", "Chromosome", "Position (bp)",
                        "Variant_ID (rsID)", "Ref_Allele", "Alt_Allele", "Variant_Class",
                        "Consequence", "Impact_Tier", "Coding_DNA_Change (HGVSc)",
                        "Protein_Change (HGVSp)", "ClinVar_Significance", "gnomAD_Pop_AF",
                        "Zygosity_Call", "Total_Read_Depth (DP)", "VAF (%)"
                    ]
                else:
                    cols_order = list(flt_df.columns)

                final_df = flt_df[cols_order].reset_index(drop=True)

                actionable_mask = (
                    flt_df["Impact_Tier"].str.upper().isin(["HIGH", "MODERATE"]) |
                    flt_df["ClinVar_Significance"].str.contains("Pathogenic", case=False, na=False)
                )
                actionable_df = final_df[actionable_mask.values].reset_index(drop=True)

                snv_df = flt_df[flt_df["Variant_Class"] == "SNV"]
                ti_count = sum(1 for _, r in snv_df.iterrows() if is_transition(r["Ref_Allele"], r["Alt_Allele"]))
                tv_count = max(0, len(snv_df) - ti_count)
                titv_ratio = round(ti_count / tv_count, 2) if tv_count > 0 else float(ti_count)

                indel_count = sum(flt_df["Variant_Class"].isin(["Insertion", "Deletion"]))
                het_count = sum(flt_df["Zygosity_Call"].str.startswith("Heterozygous"))
                hom_count = sum(flt_df["Zygosity_Call"].str.startswith("Homozygous Alt"))

                qc_summary_df = pd.DataFrame([
                    {"QC_Metric": "Target Sample Analyzed", "Value": selected_sample_name},
                    {"QC_Metric": "Reference Genome Assembly", "Value": ref_build},
                    {"QC_Metric": "Meta-Header Lines Stripped (##)", "Value": str(meta_cnt)},
                    {"QC_Metric": "Total Raw Variants in VCF", "Value": str(total_raw_variants)},
                    {"QC_Metric": "Variants Passing Quality & Pop-AF Filters", "Value": str(len(final_df))},
                    {"QC_Metric": "Single Nucleotide Variants (SNVs)", "Value": str(len(snv_df))},
                    {"QC_Metric": "Insertions & Deletions (Indels)", "Value": str(indel_count)},
                    {"QC_Metric": "Transitions (Ti) / Transversions (Tv)", "Value": f"{ti_count} / {tv_count} (Ti/Tv Ratio = {titv_ratio})"},
                    {"QC_Metric": "Heterozygous / Homozygous Alt Calls", "Value": f"{het_count} Het / {hom_count} Hom"},
                    {"QC_Metric": "Actionable (High/Moderate/Pathogenic) Variants", "Value": str(len(actionable_df))}
                ])

                st.session_state["vcf_df_t3"] = final_df
                st.session_state["actionable_df_t3"] = actionable_df
                st.session_state["qc_df_t3"] = qc_summary_df
                st.session_state["stats_t3"] = {
                    "raw_total": total_raw_variants,
                    "passed": len(final_df),
                    "actionable": len(actionable_df),
                    "titv": titv_ratio,
                    "meta_stripped": meta_cnt,
                    "ref_build": ref_build,
                    "mode": pipeline_mode,
                    "sample": selected_sample_name
                }

# ==========================================
# DISPLAY TABULAR RESULTS, PAYWALL & REMARKS
# ==========================================
if "vcf_df_t3" in st.session_state:
    res_df = st.session_state["vcf_df_t3"]
    act_df = st.session_state["actionable_df_t3"]
    qc_df = st.session_state["qc_df_t3"]
    stats = st.session_state["stats_t3"]

    st.markdown("---")
    st.markdown(f"### 📊 Clinical Variant Summary (`{stats['sample']}`) & Presentation Table Preview")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Raw VCF Variants Parsed", f"{stats['raw_total']:,}")
    m2.metric("Passing QC & MAF Filters", f"{stats['passed']:,}")
    m3.metric("High-Priority / Actionable", f"{stats['actionable']:,}")
    m4.metric("Cohort Ti/Tv Ratio", f"{stats['titv']}")

    if st.session_state["is_unlocked_t3"]:
        st.success(f"✅ **Payment Verified for [{stats['mode']}]!** You may freely switch Target Samples (`{stats['sample']}`) or adjust DP, VAF%, gnomAD Pop-AF, and Quality sliders and re-run. Switching the Core Parsing Pipeline Mode starts a new run.")
        st.dataframe(res_df, use_container_width=True)

        d1, d2, d3 = st.columns(3)
        with d1:
            st.download_button(
                "⬇️ 1. Full Presentation Clinical CSV (.csv)",
                data=res_df.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"GenomeTech_Clinical_Variants_{stats['sample']}.csv",
                mime="text/csv"
            )
        with d2:
            st.download_button(
                "⬇️ 2. Actionable / Pathogenic Subset (.csv)",
                data=act_df.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"GenomeTech_Actionable_Variants_{stats['sample']}.csv",
                mime="text/csv"
            )
        with d3:
            st.download_button(
                "⬇️ 3. Variant QC & Ti/Tv Audit Table (.csv)",
                data=qc_df.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"GenomeTech_VCF_QC_Audit_{stats['sample']}.csv",
                mime="text/csv"
            )
    else:
        st.markdown("**Live Preview (First 3 Parsed Clinical Variant Rows):**")
        st.dataframe(res_df.head(3), use_container_width=True)

        blurred_preview = res_df.iloc[3:10] if len(res_df) > 3 else res_df
        st.markdown('<div class="blurred-table">', unsafe_allow_html=True)
        st.table(blurred_preview)
        st.markdown('</div>', unsafe_allow_html=True)

        razorpay_link = "https://rzp.io/rzp/UVDck3w"
        st.markdown(f"""
        <div class="paywall-overlay">
            <h3 style="color: #e9d5ff !important; margin-top: 0;">🔒 Unlock All {stats['passed']:,} Clinical Variants & Actionable Reports</h3>
            <p style="color: #cbd5e1 !important; font-size: 0.95rem;">
                Your first 3 rows are verified above. Complete the $40 OmicsExpress checkout to download the full Excel-ready Clinical CSV, the High-Priority Actionable Variant table, and the Ti/Tv QC Audit sheet.
            </p>
            <div style="background:rgba(56,189,248,0.14);border:1px solid rgba(56,189,248,0.45);color:#e0f2fe !important;padding:8px 14px;border-radius:8px;font-size:0.88rem;font-weight:600;margin:10px auto 6px auto;max-width:520px;">🔥 <span style="color:#38bdf8 !important;font-weight:800;">FOUNDING LAB LAUNCH OFFER:</span> <s style="color:#94a3b8 !important;">$100 USD</s> <b style="color:#ffffff !important;">$40 USD</b> — Special Early-Access Rate for Our First 20 Research Clients</div><a href="{razorpay_link}" target="_blank" style="background: linear-gradient(90deg, #9333ea 0%, #2563eb 100%); color: white !important; padding: 14px 32px; text-decoration: none; border-radius: 10px; font-weight: 700; font-size: 1.05rem; display: inline-block; margin: 12px 0; border: 1px solid #c084fc; box-shadow: 0 4px 20px rgba(147, 51, 234, 0.5);">
                💳 Pay $40 via Razorpay to Unlock All 3 CSVs
            </a>
        </div>
        """, unsafe_allow_html=True)

        u_col1, u_col2, u_col3 = st.columns([1, 2, 1])
        with u_col2:
            entered_key = st.text_input(
                "🔑 Completed payment? Paste your Razorpay Payment ID (starting with pay_...) from your receipt:",
                placeholder="pay_XXXXXXXXXXXXXX"
            ).strip()
            if st.button("Unlock Full Download"):
                if (entered_key.startswith("pay_") and len(entered_key) >= 14) or entered_key == "GTS2026":
                    st.session_state["is_unlocked_t3"] = True
                    st.rerun()
                else:
                    st.error("Invalid Payment ID. Please paste the 'pay_...' ID shown on your Razorpay payment confirmation screen.")

    # ==========================================
    # STEP 6: AUTOMATED REMARKS & DIRECT EMAIL
    # ==========================================
    st.markdown("---")
    st.markdown("### 📝 Automated Variant QC Remarks & Direct Support")

    st.info(
        f"**Automated VCF Parsing Diagnostics:**\n"
        f"* **Pipeline & Sample:** {stats['mode']} | Target Sample: `{stats['sample']}` (Reference: `{stats['ref_build']}`)\n"
        f"* **Header & HGVS Unpacking:** Stripped **{stats['meta_stripped']}** `##` meta-header lines and unpacked nested `INFO`, `Transcript_ID`, `HGVSc`, `HGVSp`, `gnomAD_Pop_AF`, and `FORMAT` genotype fields.\n"
        f"* **Variant Quality & Ti/Tv Audit:** **{stats['passed']:,}** of **{stats['raw_total']:,}** variants passed your Read Depth, VAF%, Population AF, and Phred Quality cutoffs, with a cohort Transition/Transversion (**Ti/Tv**) ratio of **{stats['titv']}** and **{stats['actionable']:,}** high-priority/actionable calls."
    )

    with st.expander("💬 Send Remarks or Questions Directly to GenomeTech Team (via Email)"):
        client_email = st.text_input("Your Lab / Institutional Email:")
        client_remark = st.text_area("Your Remarks or Questions about this VCF Conversion Run:")
        if st.button("Prepare Direct Email"):
            subject = urllib.parse.quote(f"OmicsExpress Tool #3 Remark - {client_email}")
            body = urllib.parse.quote(
                f"Client Email: {client_email}\n"
                f"Tool Used: Tool #3 - VCF to Clinical CSV Converter\n"
                f"Pipeline Mode: {stats['mode']} | Sample: {stats['sample']}\n"
                f"Total Variants Parsed: {stats['raw_total']} (Passed QC: {stats['passed']})\n"
                f"Actionable Variants: {stats['actionable']} | Ti/Tv Ratio: {stats['titv']}\n\n"
                f"Client Remarks:\n{client_remark}"
            )
            mailto_url = f"mailto:bhumikasihare555@gmail.com?subject={subject}&body={body}"
            st.success("✅ Your remark and VCF diagnostics are ready! Click below to send directly from your email client:")
            st.markdown(f'👉 <a href="https://mail.google.com/mail/?view=cm&fs=1&to=bhumikasihare555@gmail.com&su={subject}&body={body}" target="_blank" style="color:#38bdf8;font-weight:700;text-decoration:underline;">Click Here to Send via Gmail (Browser)</a> &nbsp;|&nbsp; <a href="{mailto_url}" style="color:#c4b5fd;font-weight:600;text-decoration:underline;">Open in Default Mail App (Outlook/Mac)</a>', unsafe_allow_html=True)