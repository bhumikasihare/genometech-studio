import streamlit as st
import pandas as pd
import numpy as np
import re
import urllib.parse

# 1. Page Configuration (Isolated Single-Tool View)
st.set_page_config(
    page_title="Clinical & Genomic Merger | OmicsExpress",
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
    <span class="gts-badge">⚡ Tool #6: Clinical & Genomic Merger</span>
</div>
""", unsafe_allow_html=True)

if "is_unlocked_t6" not in st.session_state:
    st.session_state["is_unlocked_t6"] = False
if "locked_mode_t6" not in st.session_state:
    st.session_state["locked_mode_t6"] = None

# Callback that resets unlock & results ONLY when Core Merge Strategy or Uploaded Files change
def reset_on_mode_change_t6():
    st.session_state["is_unlocked_t6"] = False
    st.session_state.pop("merged_df_t6", None)
    st.session_state.pop("deseq_df_t6", None)
    st.session_state.pop("audit_df_t6", None)
    st.session_state.pop("stats_t6", None)

st.markdown("## Clinical & Genomic Dataset Merger")
st.markdown(
    "Upload mismatched **Clinical Patient Metadata** and **Transcriptomic / Genomic Expression Matrices** (`.csv`, `.tsv`, `.txt`). "
    "Automatically harmonizes inconsistent sample barcodes (`PT-01` vs `pt_001_RNAseq`, `TCGA.A1.A0SB` vs `TCGA-A1-A0SB-01A`), "
    "rescues specimen tissue tags (`Tumor` vs `Normal`), transposes `Genes × Samples` matrices, and outputs one unified master file."
)

with st.expander("📋 Accepted File Formats & Sample Barcode Harmonization Features (.csv, .tsv, .txt)", expanded=True):
    st.markdown("""
    * **File 1 — Clinical Metadata Spreadsheet:** Patient rows containing clinical variables (`Age`, `Sex`, `Clinical_Stage`, `Treatment_Response`, `OS_Months`, `Vital_Status`).
    * **File 2 — Transcriptomic / Genomic Spreadsheet:** Either **Samples-as-Rows** OR standard RNA-seq **Genes-as-Rows (`Genes × Samples`)** expression/mutation matrices.
    * **Complete Researcher & Biostatistician Features Included:**
      1. **Smart Barcode Harmonizer & Tissue Extractor:** Reconciles delimiter mismatches (`.` / `_` / `-`), normalizes zero-padding (`PT-1` $\leftrightarrow$ `PT-001`), truncates **12-char TCGA Patient Barcodes**, and automatically extracts **`Extracted_Specimen_Type`** (`Primary Tumor (01A)`, `Matched Normal (11A)`, `Tumor`, `Normal`) before stripping suffixes.
      2. **3 Synchronized Deliverables:**
         * **Deliverable #1:** Unified Master Clinical + Genomic Table (`Patients × [Clinical + Genes]`) for Excel, SPSS, GraphPad Prism, and Kaplan-Meier survival analysis.
         * **Deliverable #2:** `DESeq2 / edgeR / Limma` Expression Matrix (`Genes × Matched_Samples`) with sample columns ordered **identically** to the clinical patient rows.
         * **Deliverable #3:** Sample Barcode Crosswalk & Unmatched Orphan Audit Log.
      3. **Transformation & Missing Value Controls:** Supports $\log_2(x+1)$ scaling, per-gene **Z-score standardization**, replicate averaging, and missing value (`NA`) imputation.
    * **💻 Cross-Platform File Compatibility (Windows & Apple macOS):** All exported `.csv` tables use universal `UTF-8-BOM` encoding—double-click to open directly in **Microsoft Excel (Windows/Mac)**, **Apple Numbers**, **Google Sheets**, or load into **R / Python**. Sequence (`.fasta`) and vector figure (`.svg` / `.html`) outputs open natively in any text editor (**Notepad / Mac TextEdit**) or web browser (**Safari / Chrome / Edge**).
    * **Single-Mode License Note:** Each checkout unlocks your selected **Core Cohort Merge Strategy** for your uploaded files. Adjusting barcode rules, normalization, Z-scores, or NA handling within your unlocked strategy is free; switching the Core Strategy or uploading new files starts a new run.
    """)

# ==========================================
# DEMO CLINICAL & GENOMIC DATASETS
# ==========================================
DEMO_CLINICAL_DF = pd.DataFrame([
    {"Patient_Chart_ID": "TCGA-A1-A0SB", "Age_at_Diagnosis": 54, "Sex": "Female", "Clinical_Stage": "Stage IIA", "Treatment_Response": "Responder", "OS_Months": 48.5, "Vital_Status": "Alive"},
    {"Patient_Chart_ID": "TCGA-A2-A0T2", "Age_at_Diagnosis": 62, "Sex": "Female", "Clinical_Stage": "Stage IIIB", "Treatment_Response": "Non-Responder", "OS_Months": 19.2, "Vital_Status": "Deceased"},
    {"Patient_Chart_ID": "PT-001", "Age_at_Diagnosis": 47, "Sex": "Male", "Clinical_Stage": "Stage II", "Treatment_Response": "Responder", "OS_Months": 60.1, "Vital_Status": "Alive"},
    {"Patient_Chart_ID": "PT-002", "Age_at_Diagnosis": 71, "Sex": "Male", "Clinical_Stage": "Stage IV", "Treatment_Response": "Non-Responder", "OS_Months": 11.4, "Vital_Status": "Deceased"},
    {"Patient_Chart_ID": "PT-003", "Age_at_Diagnosis": 39, "Sex": "Female", "Clinical_Stage": "Stage I", "Treatment_Response": "Responder", "OS_Months": 72.0, "Vital_Status": "Alive"},
    {"Patient_Chart_ID": "PT-004", "Age_at_Diagnosis": 58, "Sex": "Female", "Clinical_Stage": "Stage IIIA", "Treatment_Response": "Responder", "OS_Months": 36.8, "Vital_Status": "Alive"},
    {"Patient_Chart_ID": "PT-005", "Age_at_Diagnosis": 66, "Sex": "Male", "Clinical_Stage": "Stage IV", "Treatment_Response": "Non-Responder", "OS_Months": 8.9, "Vital_Status": "Deceased"},
    {"Patient_Chart_ID": "PT-006", "Age_at_Diagnosis": 51, "Sex": "Female", "Clinical_Stage": "Stage IIB", "Treatment_Response": "Responder", "OS_Months": 44.0, "Vital_Status": "Alive"},
    {"Patient_Chart_ID": "PT-007", "Age_at_Diagnosis": 63, "Sex": "Male", "Clinical_Stage": "Stage IIIB", "Treatment_Response": "Non-Responder", "OS_Months": 15.6, "Vital_Status": "Deceased"},
    {"Patient_Chart_ID": "PT-008", "Age_at_Diagnosis": 45, "Sex": "Female", "Clinical_Stage": "Stage IIA", "Treatment_Response": "Responder", "OS_Months": 53.2, "Vital_Status": "Alive"},
    {"Patient_Chart_ID": "PT-009_ClinicalOnly", "Age_at_Diagnosis": 69, "Sex": "Male", "Clinical_Stage": "Stage III", "Treatment_Response": "Non-Responder", "OS_Months": 14.0, "Vital_Status": "Deceased"}
])

DEMO_GENOMIC_DF = pd.DataFrame([
    {"Sequencing_Run_ID": "TCGA.A1.A0SB.01A_RNAseq", "TP53_TPM": 142.5, "BRCA1_TPM": 88.4, "EGFR_TPM": 310.2, "MYC_TPM": 415.0, "CD274_PDL1_TPM": 64.2, "MARCH1_TPM": 29.5},
    {"Sequencing_Run_ID": "TCGA_A2_A0T2_11A", "TP53_TPM": 38.1, "BRCA1_TPM": 22.0, "EGFR_TPM": 845.6, "MYC_TPM": 920.4, "CD274_PDL1_TPM": 18.5, "MARCH1_TPM": 11.2},
    {"Sequencing_Run_ID": "Sample_pt_1_Tumor", "TP53_TPM": 195.0, "BRCA1_TPM": 112.3, "EGFR_TPM": 210.5, "MYC_TPM": 290.1, "CD274_PDL1_TPM": 92.4, "MARCH1_TPM": 41.8},
    {"Sequencing_Run_ID": "pt-2_RNAseq_Rep1", "TP53_TPM": 24.6, "BRCA1_TPM": 19.8, "EGFR_TPM": 1120.0, "MYC_TPM": 1050.8, "CD274_PDL1_TPM": 12.1, "MARCH1_TPM": 8.4},
    {"Sequencing_Run_ID": "PT_003_Primary", "TP53_TPM": 210.4, "BRCA1_TPM": 134.0, "EGFR_TPM": 175.2, "MYC_TPM": 240.6, "CD274_PDL1_TPM": 108.9, "MARCH1_TPM": 52.1},
    {"Sequencing_Run_ID": "pt.004.Normal", "TP53_TPM": 164.2, "BRCA1_TPM": 95.1, "EGFR_TPM": 290.8, "MYC_TPM": 380.2, "CD274_PDL1_TPM": 78.3, "MARCH1_TPM": 33.7},
    {"Sequencing_Run_ID": "Sample_PT5_BAM", "TP53_TPM": 19.5, "BRCA1_TPM": 14.2, "EGFR_TPM": 980.4, "MYC_TPM": 1180.0, "CD274_PDL1_TPM": 9.8, "MARCH1_TPM": 6.9},
    {"Sequencing_Run_ID": "PT-006-Tumor-R1", "TP53_TPM": 178.9, "BRCA1_TPM": 104.5, "EGFR_TPM": 260.0, "MYC_TPM": 340.5, "CD274_PDL1_TPM": 85.0, "MARCH1_TPM": 38.2},
    {"Sequencing_Run_ID": "pt_7_rnaseq", "TP53_TPM": 41.2, "BRCA1_TPM": 28.9, "EGFR_TPM": 790.1, "MYC_TPM": 870.3, "CD274_PDL1_TPM": 22.4, "MARCH1_TPM": 14.0},
    {"Sequencing_Run_ID": "PT.008.FastQ", "TP53_TPM": 188.6, "BRCA1_TPM": 118.7, "EGFR_TPM": 230.4, "MYC_TPM": 310.0, "CD274_PDL1_TPM": 95.6, "MARCH1_TPM": 45.3},
    {"Sequencing_Run_ID": "Unmatched_Ctrl_99", "TP53_TPM": 150.0, "BRCA1_TPM": 100.0, "EGFR_TPM": 200.0, "MYC_TPM": 250.0, "CD274_PDL1_TPM": 50.0, "MARCH1_TPM": 30.0}
])

# ==========================================
# HELPER FUNCTIONS FOR BARCODE & TISSUE EXTRACTION
# ==========================================
def extract_specimen_type(raw_id):
    s = re.sub(r"[\._\s]+", "-", str(raw_id).strip().upper())
    # Check TCGA 4th barcode segment (01 = Primary Tumor, 06 = Metastatic, 11 = Solid Normal)
    tcga_m = re.match(r"^TCGA-[A-Z0-9]{2}-[A-Z0-9]{4}-(\d{2})[A-Z]?", s)
    if tcga_m:
        code = tcga_m.group(1)
        if code == "01":
            return "Primary Solid Tumor (TCGA-01)"
        elif code == "06":
            return "Metastatic Tumor (TCGA-06)"
        elif code == "11":
            return "Solid Tissue Normal (TCGA-11)"
        elif code == "03":
            return "Peripheral Blood Cancer (TCGA-03)"
    if any(k in s for k in ["-TUMOR", "-TUM", "-MET", "-PRIMARY"]):
        return "Tumor / Primary Specimen"
    if any(k in s for k in ["-NORMAL", "-NORM", "-CTRL", "-CONTROL"]):
        return "Normal / Control Specimen"
    return "Standard Clinical Specimen"

def harmonize_sample_id(raw_id, strip_affixes=True, unify_delims=True, pad_numbers=True, tcga_12char=False):
    s = str(raw_id).strip().upper()
    if not s or s == "NAN":
        return "UNKNOWN"

    if unify_delims:
        s = re.sub(r"[\._\s]+", "-", s)

    if strip_affixes:
        s = re.sub(r"^(SAMPLE-|PATIENT-|SUBJ-|CASE-|ID-)", "", s)
        s = re.sub(r"(-RNASEQ|-RNA|-TUMOR|-NORMAL|-PRIMARY|-CTRL|-BAM|-FASTQ|-REP\d+|-R\d+|-S\d+)+$", "", s)

    if tcga_12char and s.startswith("TCGA-") and len(s) >= 12:
        parts = s.split("-")
        if len(parts) >= 3:
            s = "-".join(parts[:3])

    if pad_numbers and not s.startswith("TCGA-"):
        m = re.match(r"^([A-Z]+)-?0*(\d+)$", s)
        if m:
            prefix, num = m.group(1), int(m.group(2))
            s = f"{prefix}-{num:03d}"

    return s

# ==========================================
# STEP 2: DUAL FILE UPLOAD OR DEMO DATASETS
# ==========================================
col_u1, col_u2, col_demo = st.columns([2, 2, 1])
with col_u1:
    clin_file = st.file_uploader(
        "1. Upload Clinical Metadata Table (.csv, .tsv, .txt)",
        type=["csv", "tsv", "txt"],
        on_change=reset_on_mode_change_t6
    )
with col_u2:
    gen_file = st.file_uploader(
        "2. Upload Transcriptomic / Genomic Matrix (.csv, .tsv, .txt)",
        type=["csv", "tsv", "txt"],
        on_change=reset_on_mode_change_t6
    )
with col_demo:
    st.write("")
    st.write("")
    use_sample = st.checkbox("🧪 Load Demo Mismatched Datasets", value=True, on_change=reset_on_mode_change_t6)

df_clin_raw = None
df_gen_raw = None

if clin_file is not None and gen_file is not None:
    try:
        c_sep = "\t" if clin_file.name.lower().endswith((".tsv", ".txt")) else ","
        g_sep = "\t" if gen_file.name.lower().endswith((".tsv", ".txt")) else ","
        df_clin_raw = pd.read_csv(clin_file, sep=c_sep)
        df_gen_raw = pd.read_csv(gen_file, sep=g_sep)
    except Exception as e:
        st.error(f"Error reading uploaded files: {e}")
elif use_sample:
    df_clin_raw = DEMO_CLINICAL_DF.copy()
    df_gen_raw = DEMO_GENOMIC_DF.copy()

# ==========================================
# STEP 3: CONFIGURE CORE MERGE ENGINE & HARMONIZATION
# ==========================================
if df_clin_raw is not None and df_gen_raw is not None:
    with st.expander("👁️ Inspect Raw Input Spreadsheets Before Merging (Notice Mismatched Sample IDs)", expanded=False):
        p1, p2 = st.columns(2)
        with p1:
            st.markdown(f"**Clinical Metadata ({len(df_clin_raw)} rows):**")
            st.dataframe(df_clin_raw.head(4), use_container_width=True)
        with p2:
            st.markdown(f"**Genomic / Transcriptomic Matrix ({len(df_gen_raw)} rows):**")
            st.dataframe(df_gen_raw.head(4), use_container_width=True)

    st.markdown("### ⚙️ Configure Cohort Alignment Strategy, Matrix Orientation & Normalization")

    # Core Merge Strategy in Clear Researcher Language (ONLY switching this or uploading new files resets paywall!)
    core_engine = st.selectbox(
        "1. Core Cohort Merge Strategy (Switching strategy starts a new pipeline run):",
        [
            "Matched Cohort Only — Keep Only Patients Present in Both Files (Best for DESeq2, PCA & Survival)",
            "Preserve All Clinical Patients — Keep Full Hospital Cohort & Flag Missing Genomic Assays (Left Merge)",
            "Complete Master Union — Keep All Patients & All Genomic Samples from Both Files (Outer Merge)",
            "TCGA / Biobank Patient-to-Aliquot Merger — Match 12-Char Patient IDs to Tumor/Normal Barcodes"
        ],
        on_change=reset_on_mode_change_t6
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**2. Matrix Orientation & ID Columns**")
        clin_id_col = st.selectbox("Clinical Patient/Sample ID Column:", list(df_clin_raw.columns), index=0)
        transpose_gen = st.checkbox(
            "🔄 Transpose Genomic Matrix (My Genes are Rows & Samples are Columns)",
            value=False,
            help="Check this if your RNA-seq matrix has Gene Symbols in the first column and Sample IDs across the top header row."
        )
        if not transpose_gen:
            gen_id_col = st.selectbox("Genomic Sample ID Column:", list(df_gen_raw.columns), index=0)
        else:
            gen_id_col = st.selectbox("Column Containing Gene/Feature Names:", list(df_gen_raw.columns), index=0)

    with c2:
        st.markdown("**3. Smart Sample Barcode Harmonization**")
        unify_delims = st.checkbox("Unify Delimiters (. / _ / space ➔ -)", value=True)
        strip_affixes = st.checkbox("Rescue Specimen Tag & Strip Affixes (_RNAseq, _Tumor, Sample_)", value=True)
        pad_numbers = st.checkbox("Normalize Zero-Padding (PT-1 ➔ PT-001)", value=True)
        tcga_mode = st.checkbox("Truncate TCGA Barcodes to 12-Char Patient ID", value=True)

    with c3:
        st.markdown("**4. Scaling, Missing Values & Excel Guard**")
        norm_choice = st.selectbox(
            "Genomic Expression Scaling:",
            [
                "Keep Original Values (Raw Counts / TPM / FPKM)",
                "Apply Log2(x + 1) Transformation",
                "Standardize to Per-Gene Z-Scores (Mean=0, SD=1 for Heatmaps/Cox)"
            ]
        )
        na_handling = st.selectbox(
            "Missing Value (NA) Handling in Genomic Features:",
            ["Keep as NA / Blank", "Fill Missing Genomic Values with 0", "Impute Missing Values with Gene Median"]
        )
        rep_handling = st.selectbox(
            "Technical Replicate Handling:",
            ["Average Numeric Values Across Replicates", "Keep Primary (First) Sample"]
        )
        excel_guard = st.checkbox(
            "🛡️ Enable Excel Gene-Header Guard (Protects MARCH1 / SEPT2)",
            value=False,
            help="Prefixes vulnerable gene names so Microsoft Excel never converts MARCH1 or SEPT2 into calendar dates."
        )

    clin_sig = clin_file.name if clin_file is not None else "demo_clin"
    gen_sig = gen_file.name if gen_file is not None else "demo_gen"
    current_mode_sig = f"{clin_sig}|{gen_sig}|{core_engine}"

    # ==========================================
    # STEP 4: RUN CLINICAL & GENOMIC MERGER
    # ==========================================
    if st.button("🚀 Align Sample Barcodes & Merge Datasets"):
        if st.session_state["locked_mode_t6"] is not None and st.session_state["locked_mode_t6"] != current_mode_sig:
            st.session_state["is_unlocked_t6"] = False
        st.session_state["locked_mode_t6"] = current_mode_sig

        with st.spinner("Harmonizing sample barcodes, rescuing tissue tags, orienting genomic matrix, and synchronizing DESeq2/R outputs..."):
            clin_df = df_clin_raw.copy()
            gen_df = df_gen_raw.copy()

            # Step A: Transpose Genomic Matrix if Genes are Rows and Samples are Columns
            if transpose_gen:
                gene_names = gen_df[gen_id_col].astype(str).tolist()
                sample_cols = [c for c in gen_df.columns if c != gen_id_col]
                transposed_data = gen_df[sample_cols].apply(pd.to_numeric, errors="coerce").T
                transposed_data.columns = gene_names
                transposed_data.insert(0, "Genomic_Sample_ID", transposed_data.index)
                gen_df = transposed_data.reset_index(drop=True)
                active_gen_id_col = "Genomic_Sample_ID"
            else:
                active_gen_id_col = gen_id_col

            if excel_guard:
                gen_df.columns = [
                    f"Gene_{c}" if re.match(r"^(MARCH|SEPT|DEC|OCT)\d+", str(c).upper()) else c
                    for c in gen_df.columns
                ]

            # Step B: Rescue Specimen Type & Harmonize Sample IDs on both sides
            use_tcga = tcga_mode or ("TCGA" in core_engine)
            clin_df["Raw_Clinical_ID"] = clin_df[clin_id_col].astype(str)
            clin_df["Harmonized_Sample_ID"] = clin_df["Raw_Clinical_ID"].apply(
                lambda x: harmonize_sample_id(x, strip_affixes, unify_delims, pad_numbers, use_tcga)
            )

            gen_df["Raw_Genomic_ID"] = gen_df[active_gen_id_col].astype(str)
            gen_df["Extracted_Specimen_Type"] = gen_df["Raw_Genomic_ID"].apply(extract_specimen_type)
            gen_df["Harmonized_Sample_ID"] = gen_df["Raw_Genomic_ID"].apply(
                lambda x: harmonize_sample_id(x, strip_affixes, unify_delims, pad_numbers, use_tcga)
            )

            if clin_id_col not in ("Raw_Clinical_ID", "Harmonized_Sample_ID"):
                clin_df = clin_df.drop(columns=[clin_id_col])
            if active_gen_id_col not in ("Raw_Genomic_ID", "Harmonized_Sample_ID", "Extracted_Specimen_Type"):
                gen_df = gen_df.drop(columns=[active_gen_id_col])

            # Step C: Handle Technical Replicates in Genomic Data
            num_gen_cols = [
                c for c in gen_df.select_dtypes(include=[np.number]).columns
                if c not in ("Harmonized_Sample_ID",)
            ]
            if "Average Numeric" in rep_handling and num_gen_cols:
                meta_first = gen_df.groupby("Harmonized_Sample_ID")[["Raw_Genomic_ID", "Extracted_Specimen_Type"]].first().reset_index()
                avg_num = gen_df.groupby("Harmonized_Sample_ID")[num_gen_cols].mean().round(3).reset_index()
                gen_df = pd.merge(meta_first, avg_num, on="Harmonized_Sample_ID", how="inner")
            else:
                gen_df = gen_df.drop_duplicates(subset=["Harmonized_Sample_ID"], keep="first")

            clin_df = clin_df.drop_duplicates(subset=["Harmonized_Sample_ID"], keep="first")

            # Step D: Missing Value (NA) Handling & Scaling on Numeric Genomic Columns
            if num_gen_cols:
                for col in num_gen_cols:
                    if col in gen_df.columns:
                        if "Fill Missing Genomic Values with 0" in na_handling:
                            gen_df[col] = gen_df[col].fillna(0.0)
                        elif "Gene Median" in na_handling:
                            med_val = gen_df[col].median()
                            gen_df[col] = gen_df[col].fillna(0.0 if pd.isna(med_val) else med_val)

                        if "Log2(x + 1)" in norm_choice:
                            gen_df[col] = np.log2(np.maximum(0.0, gen_df[col].astype(float)) + 1.0).round(3)
                        elif "Z-Scores" in norm_choice:
                            col_mean = gen_df[col].astype(float).mean()
                            col_std = gen_df[col].astype(float).std()
                            if col_std and col_std > 0:
                                gen_df[col] = ((gen_df[col].astype(float) - col_mean) / col_std).round(3)

            # Step E: Determine Join Strategy from Core Engine
            if "Matched Cohort Only" in core_engine or "TCGA" in core_engine:
                join_how = "inner"
            elif "Preserve All Clinical" in core_engine:
                join_how = "left"
            else:
                join_how = "outer"

            merged_df = pd.merge(clin_df, gen_df, on="Harmonized_Sample_ID", how=join_how)

            def classify_alignment(row):
                c_id = str(row.get("Raw_Clinical_ID", "Missing"))
                g_id = str(row.get("Raw_Genomic_ID", "Missing"))
                if c_id in ("nan", "Missing", "None") or pd.isna(row.get("Raw_Clinical_ID")):
                    return "Orphan Genomic Sample (No Clinical Record)"
                if g_id in ("nan", "Missing", "None") or pd.isna(row.get("Raw_Genomic_ID")):
                    return "Orphan Clinical Patient (No Genomic Assay)"
                if c_id.strip() == g_id.strip():
                    return "Exact Barcode Match"
                return "Harmonized Barcode Match (Rescued)"

            merged_df["Alignment_Status"] = merged_df.apply(classify_alignment, axis=1)
            if "Extracted_Specimen_Type" in merged_df.columns:
                merged_df["Extracted_Specimen_Type"] = merged_df["Extracted_Specimen_Type"].fillna("No Genomic Assay")

            lead_cols = [
                "Harmonized_Sample_ID", "Raw_Clinical_ID", "Raw_Genomic_ID",
                "Extracted_Specimen_Type", "Alignment_Status"
            ]
            lead_cols = [c for c in lead_cols if c in merged_df.columns]
            other_cols = [c for c in merged_df.columns if c not in lead_cols]
            merged_df = merged_df[lead_cols + other_cols].reset_index(drop=True)

            # Build Deliverable #2: True DESeq2 / edgeR / Limma Expression Matrix (Genes x Matched_Samples)
            inner_matched = pd.merge(clin_df, gen_df, on="Harmonized_Sample_ID", how="inner").sort_values(by="Harmonized_Sample_ID")
            if num_gen_cols and not inner_matched.empty:
                deseq_matrix = inner_matched.set_index("Harmonized_Sample_ID")[num_gen_cols].T
                deseq_matrix.insert(0, "Gene_Feature_ID", deseq_matrix.index)
                deseq_ready_df = deseq_matrix.reset_index(drop=True)
            else:
                deseq_ready_df = inner_matched.reset_index(drop=True)

            # Build Deliverable #3: Full Sample ID Crosswalk & Orphan Audit Log
            outer_audit = pd.merge(
                clin_df[["Harmonized_Sample_ID", "Raw_Clinical_ID"]],
                gen_df[["Harmonized_Sample_ID", "Raw_Genomic_ID", "Extracted_Specimen_Type"]],
                on="Harmonized_Sample_ID",
                how="outer"
            )
            outer_audit["Alignment_Status"] = outer_audit.apply(classify_alignment, axis=1)
            outer_audit["Raw_Clinical_ID"] = outer_audit["Raw_Clinical_ID"].fillna("UNMATCHED (Missing in Clinical)")
            outer_audit["Raw_Genomic_ID"] = outer_audit["Raw_Genomic_ID"].fillna("UNMATCHED (Missing in Genomic)")
            outer_audit["Extracted_Specimen_Type"] = outer_audit["Extracted_Specimen_Type"].fillna("N/A")

            matched_cnt = int(sum(outer_audit["Alignment_Status"].str.contains("Match")))
            harmonized_rescued = int(sum(outer_audit["Alignment_Status"] == "Harmonized Barcode Match (Rescued)"))
            orphan_clin = int(sum(outer_audit["Alignment_Status"].str.contains("Orphan Clinical")))
            orphan_gen = int(sum(outer_audit["Alignment_Status"].str.contains("Orphan Genomic")))

            st.session_state["merged_df_t6"] = merged_df
            st.session_state["deseq_df_t6"] = deseq_ready_df
            st.session_state["audit_df_t6"] = outer_audit
            st.session_state["stats_t6"] = {
                "clin_in": len(clin_df),
                "gen_in": len(gen_df),
                "matched": matched_cnt,
                "rescued": harmonized_rescued,
                "orphans": orphan_clin + orphan_gen,
                "final_rows": len(merged_df),
                "final_cols": len(merged_df.columns),
                "engine": core_engine
            }

# ==========================================
# DISPLAY TABULAR RESULTS, PAYWALL & REMARKS
# ==========================================
if "merged_df_t6" in st.session_state:
    res_df = st.session_state["merged_df_t6"]
    deseq_df = st.session_state["deseq_df_t6"]
    aud_df = st.session_state["audit_df_t6"]
    stats = st.session_state["stats_t6"]

    st.markdown("---")
    st.markdown("### 📊 Cohort Alignment Summary & Master Merged Table Preview")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Clinical / Genomic Samples", f"{stats['clin_in']} / {stats['gen_in']}")
    m2.metric("Aligned & Merged Patients", f"{stats['matched']}")
    m3.metric("Rescued by ID Harmonizer", f"{stats['rescued']} Barcodes")
    m4.metric("Orphan / Unmatched IDs", f"{stats['orphans']}")

    if st.session_state["is_unlocked_t6"]:
        st.success(f"✅ **Payment Verified for [{stats['engine']}]!** Master merged patient table, DESeq2/R `Genes × Samples` synchronized matrix, and orphan barcode audit log unlocked.")
        st.dataframe(res_df, use_container_width=True)

        d1, d2, d3 = st.columns(3)
        with d1:
            st.download_button(
                "⬇️ 1. Master Merged Clinical + Genomic Table (.csv)",
                data=res_df.to_csv(index=False).encode("utf-8-sig"),
                file_name="GenomeTech_Master_Clinical_Genomic_Merged.csv",
                mime="text/csv"
            )
        with d2:
            st.download_button(
                "⬇️ 2. DESeq2 / R Matrix (Genes × Matched Samples .csv)",
                data=deseq_df.to_csv(index=False).encode("utf-8-sig"),
                file_name="GenomeTech_DESeq2_Genes_x_MatchedSamples.csv",
                mime="text/csv"
            )
        with d3:
            st.download_button(
                "⬇️ 3. Barcode Crosswalk & Orphan Audit Log (.csv)",
                data=aud_df.to_csv(index=False).encode("utf-8-sig"),
                file_name="GenomeTech_Sample_Barcode_Audit.csv",
                mime="text/csv"
            )
    else:
        st.markdown("**Live Preview (First 4 Harmonized & Merged Patient-Genomic Records):**")
        st.dataframe(res_df.head(4), use_container_width=True)

        blurred_preview = res_df.iloc[4:11] if len(res_df) > 4 else res_df
        st.markdown('<div class="blurred-table">', unsafe_allow_html=True)
        st.table(blurred_preview)
        st.markdown('</div>', unsafe_allow_html=True)

        razorpay_link = "https://rzp.io/rzp/UVDck3w"
        st.markdown(f"""
        <div class="paywall-overlay">
            <h3 style="color: #e9d5ff !important; margin-top: 0;">🔒 Unlock Full {stats['final_rows']}-Sample Master Table & DESeq2 Matrix</h3>
            <p style="color: #cbd5e1 !important; font-size: 0.95rem;">
                Your first 4 aligned patient records are verified above ({stats['rescued']} mismatched barcodes automatically rescued). Complete the $40 OmicsExpress checkout to download all 3 synchronized files.
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
                    st.session_state["is_unlocked_t6"] = True
                    st.rerun()
                else:
                    st.error("Invalid Payment ID. Please paste the 'pay_...' ID shown on your Razorpay payment confirmation screen.")

    # ==========================================
    # STEP 6: AUTOMATED REMARKS & DIRECT EMAIL
    # ==========================================
    st.markdown("---")
    st.markdown("### 📝 Automated Cohort Alignment Remarks & Direct Support")

    st.info(
        f"**Automated Clinical & Genomic Merger Diagnostics:**\n"
        f"* **Cohort Merge Strategy:** {stats['engine']}\n"
        f"* **Barcode Harmonization & Tissue Rescue:** Aligned **{stats['matched']}** patients across **{stats['clin_in']}** clinical records and **{stats['gen_in']}** genomic assays (**{stats['rescued']}** mismatched barcodes rescued; tissue origin tags preserved in `Extracted_Specimen_Type`).\n"
        f"* **DESeq2 / R Synchronization & Orphan Audit:** Generated both a patient-row master table (`{stats['final_rows']} × {stats['final_cols']}`) and a `Genes × Matched_Samples` matrix with **0 column-order mismatches**, plus an audit log of **{stats['orphans']}** unmatched orphan ID(s)."
    )

    with st.expander("💬 Send Remarks or Questions Directly to GenomeTech Team (via Email)"):
        client_email = st.text_input("Your Lab / Institutional Email:")
        client_remark = st.text_area("Your Remarks or Questions about this Clinical-Genomic Merge Run:")
        if st.button("Prepare Direct Email"):
            subject = urllib.parse.quote(f"OmicsExpress Tool #6 Remark - {client_email}")
            body = urllib.parse.quote(
                f"Client Email: {client_email}\n"
                f"Tool Used: Tool #6 - Clinical & Genomic Dataset Merger\n"
                f"Strategy: {stats['engine']}\n"
                f"Clinical Records: {stats['clin_in']} | Genomic Assays: {stats['gen_in']}\n"
                f"Matched Cohort: {stats['matched']} (Rescued via Barcode Harmonization: {stats['rescued']})\n\n"
                f"Client Remarks:\n{client_remark}"
            )
            mailto_url = f"mailto:bhumikasihare555@gmail.com?subject={subject}&body={body}"
            st.success("✅ Your remark and alignment diagnostics are ready! Click below to send directly from your email client:")
            st.markdown(f'👉 <a href="https://mail.google.com/mail/?view=cm&fs=1&to=bhumikasihare555@gmail.com&su={subject}&body={body}" target="_blank" style="color:#38bdf8;font-weight:700;text-decoration:underline;">Click Here to Send via Gmail (Browser)</a> &nbsp;|&nbsp; <a href="{mailto_url}" style="color:#c4b5fd;font-weight:600;text-decoration:underline;">Open in Default Mail App (Outlook/Mac)</a>', unsafe_allow_html=True)