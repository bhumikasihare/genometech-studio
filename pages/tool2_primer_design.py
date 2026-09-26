import streamlit as st
import pandas as pd
import numpy as np
import math
import urllib.parse

# 1. Page Configuration (Isolated Single-Tool View)
st.set_page_config(
    page_title="Automated Primer Design | OmicsExpress",
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
    <span class="gts-badge">⚡ Tool #2: Automated Primer Design</span>
</div>
""", unsafe_allow_html=True)

if "is_unlocked_t2" not in st.session_state:
    st.session_state["is_unlocked_t2"] = False
if "locked_mode_t2" not in st.session_state:
    st.session_state["locked_mode_t2"] = None

def reset_on_mode_change_t2():
    st.session_state["is_unlocked_t2"] = False
    st.session_state.pop("primer_df_t2", None)
    st.session_state.pop("order_df_t2", None)
    st.session_state.pop("fasta_str_t2", None)
    st.session_state.pop("stats_t2", None)

st.markdown("## Automated Batch Primer Designer")
st.markdown(
    "Design high-specificity Forward and Reverse primers across multi-sequence FASTA or tabular files. "
    "Automatically computes **exact base-pair binding coordinates, total valid sites per sample, numeric $T_m$/GC%, "
    "3' end $\Delta G$ stability (kcal/mol), Molecular Weight (Da), predicted qPCR Amplicon Melt $T_m$, and optimum thermal cycler protocols**."
)

with st.expander("📋 Required File Format & Complete Wet-Lab Deliverables (.fasta, .fa, .txt, or .csv)", expanded=True):
    st.markdown("""
    * **Accepted File Formats:** Multi-sequence FASTA (`.fasta`, `.fa`, `.txt`) or tabular `.csv` containing a Sequence ID column and a Nucleotide Sequence column (`A, T, G, C`).
    * **Complete Wet-Lab & qPCR Columns Included:**
      1. **Binding Coordinates & Site Counts:** `Valid_Pairs_In_Sample`, `Fwd_Binding_Site (bp)`, `Rev_Binding_Site (bp)`, `Amplicon_Size (bp)`.
      2. **Numeric Excel-Sortable Columns:** `Fwd_Len (bp)`, `Rev_Len (bp)`, `Fwd_Tm (°C)`, `Rev_Tm (°C)`, `Delta_Tm (°C)`, `Fwd_GC (%)`, `Rev_GC (%)`.
      3. **Biophysical & Resuspension Metrics:** `3'_End_DeltaG (kcal/mol)`, `3'_GC_Clamp`, and `Fwd_MW / Rev_MW (Da)`.
      4. **SYBR Green Melt-Curve & Product Verification:** `Amplicon_GC (%)`, `Predicted_Amplicon_Melt_Tm (°C)`, and full `Amplicon_Sequence (5'->3')`.
    * **💻 Cross-Platform File Compatibility (Windows & Apple macOS):** All exported `.csv` tables use universal `UTF-8-BOM` encoding—double-click to open directly in **Microsoft Excel (Windows/Mac)**, **Apple Numbers**, **Google Sheets**, or load into **R / Python**. Sequence (`.fasta`) and vector figure (`.svg` / `.html`) outputs open natively in any text editor (**Notepad / Mac TextEdit**) or web browser (**Safari / Chrome / Edge**).
    * **Single-Mode License Note:** Each checkout unlocks your selected **Application Mode** (`qPCR`, `Standard PCR`, `Sanger Sequencing`, or `Custom`). Adjusting thermodynamic sliders within your unlocked mode is free; switching the Application Mode starts a new run.
    """)

# ==========================================
# HELPER FUNCTIONS FOR PRIMER BIOPHYSICS
# ==========================================
def rev_comp(seq):
    trans = str.maketrans("ATGCRYSWKMBDHVNatgcryswkmbdhvn", "TACGYRSWMKVHDBNtacgyrswmkvhdbn")
    return seq.translate(trans)[::-1].upper()

def calc_gc(seq):
    if not seq:
        return 0.0
    gc = sum(1 for b in seq.upper() if b in ("G", "C"))
    return round((gc / len(seq)) * 100.0, 1)

def calc_tm(seq, na_mm=50.0):
    seq = seq.upper()
    n = len(seq)
    if n == 0:
        return 0.0
    gc_count = sum(1 for b in seq if b in ("G", "C"))
    salt_corr = 16.6 * math.log10(na_mm / 1000.0)
    if n < 14:
        tm = 2 * (n - gc_count) + 4 * gc_count
    else:
        tm = 81.5 + salt_corr + 0.41 * ((gc_count / n) * 100.0) - (675.0 / n)
    return round(tm, 2)

def calc_amplicon_melt_tm(amp_seq, na_mm=50.0):
    # Wet-lab Baldino/Marmur formula for dsDNA PCR product melt curve peak in SYBR Green
    n = len(amp_seq)
    if n == 0:
        return 0.0
    gc_pct = calc_gc(amp_seq)
    salt_corr = 16.6 * math.log10(na_mm / 1000.0)
    tm_prod = 81.5 + salt_corr + 0.41 * gc_pct - (500.0 / n)
    return round(tm_prod, 1)

def calc_oligo_mw(seq):
    # Anhydrous ssDNA molecular weight in Daltons (g/mol)
    s = seq.upper()
    mw = (s.count("A") * 313.21) + (s.count("T") * 304.20) + (s.count("G") * 329.21) + (s.count("C") * 289.18) - 61.96
    return round(max(0.0, mw), 1)

def calc_3prime_dg(seq):
    # Nearest-neighbor 3' pentamer ΔG approximation (kcal/mol at 37°C)
    nn_dg = {
        "AA": -1.00, "TT": -1.00, "AT": -0.88, "TA": -0.58,
        "CA": -1.45, "TG": -1.45, "GT": -1.44, "AC": -1.44,
        "CT": -1.28, "AG": -1.28, "GA": -1.30, "TC": -1.30,
        "CG": -2.17, "GC": -2.24, "GG": -1.84, "CC": -1.84
    }
    tail = seq[-5:].upper()
    dg = sum(nn_dg.get(tail[i:i+2], -1.2) for i in range(len(tail) - 1))
    return round(dg, 2)

def has_homopolymer(seq, max_repeat=4):
    for base in "ATGC":
        if (base * max_repeat) in seq.upper():
            return True
    return False

def check_3prime_clamp(seq, min_gc=1, max_gc=3):
    tail = seq[-5:].upper()
    gc_tail = sum(1 for b in tail if b in ("G", "C"))
    return (min_gc <= gc_tail <= max_gc), gc_tail

def has_3prime_dimer(seq1, seq2, match_len=4):
    tail1 = seq1[-match_len:].upper()
    rc_tail2 = rev_comp(seq2[-match_len:].upper())
    return tail1 == rc_tail2

def parse_fasta_text(raw_text):
    records = []
    curr_id = None
    curr_seq = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if curr_id is not None and curr_seq:
                records.append({"Sample_ID": curr_id, "Sequence": "".join(curr_seq).upper()})
            curr_id = line[1:].strip().split()[0]
            curr_seq = []
        else:
            clean_line = "".join(c for c in line.upper() if c in "ATGC")
            curr_seq.append(clean_line)
    if curr_id is not None and curr_seq:
        records.append({"Sample_ID": curr_id, "Sequence": "".join(curr_seq).upper()})
    elif not records and curr_seq:
        records.append({"Sample_ID": "Sample_Seq_1", "Sequence": "".join(curr_seq).upper()})
    return pd.DataFrame(records)

# ==========================================
# STEP 2: SEQUENCE INPUT & DEMO DATA
# ==========================================
col_up, col_demo = st.columns([3, 1])
with col_up:
    uploaded_file = st.file_uploader(
        "Drop your FASTA or Sequence Table (.fasta, .fa, .txt, .csv)",
        type=["fasta", "fa", "txt", "csv"],
        on_change=reset_on_mode_change_t2
    )
with col_demo:
    st.write("")
    st.write("")
    use_sample = st.checkbox("🧪 Load Demo Multi-Gene Dataset", value=False, on_change=reset_on_mode_change_t2)

paste_seq = st.text_area(
    "Or paste FASTA / Raw DNA Sequences directly (optional):",
    height=90,
    placeholder=">Gene_Target_1\nATGCGTACGTAGCTAGCTAGCT...",
    on_change=reset_on_mode_change_t2
)

df_seqs = None
if uploaded_file is not None:
    try:
        fname = uploaded_file.name.lower()
        if fname.endswith(".csv"):
            raw_df = pd.read_csv(uploaded_file)
            sc1, sc2 = st.columns(2)
            id_col = sc1.selectbox("Select Sample/Gene ID Column:", raw_df.columns, index=0)
            sq_col = sc2.selectbox("Select Nucleotide Sequence Column:", raw_df.columns, index=1 if len(raw_df.columns) > 1 else 0)
            df_seqs = pd.DataFrame({
                "Sample_ID": raw_df[id_col].astype(str),
                "Sequence": raw_df[sq_col].astype(str).str.upper().str.replace(r"[^ATGC]", "", regex=True)
            })
        else:
            content = uploaded_file.read().decode("utf-8", errors="ignore")
            df_seqs = parse_fasta_text(content)
    except Exception as e:
        st.error(f"Error reading uploaded file: {e}")
elif paste_seq.strip():
    df_seqs = parse_fasta_text(paste_seq)
elif use_sample:
    df_seqs = pd.DataFrame([
        {
            "Sample_ID": "TP53_Exon5_Human",
            "Sequence": (
                "TGTTCACTTGTGCCCTGACTTTCAACTCTGTCTCCTTCCTCTTCCTACAGTACTCCCCTGCCCTCAACAAGATGTTTTGCCAACTGGCCAAGACCTGCCCTGTGCAGCTGTGGGTTGATTCCACACCCCCGCCCGGCACCCGCGTCCGCGCCATGGCCATCTACAAGCAGTCACAGCACATGACGGAGGTTGTGAGGCGCTGCCCCCACCATGAGCGCTGCTCAGATAGCGATGGTCTGGCCCCTCCTCAG"
                "CATCTTATCCGAGTGGAAGGAAATTTGCGTGTGGAGTATTTGGATGACAGAAACACTTTTCGACATAGTGTGGTGGTGCCCTATGAGCCGCCTGAGGTTGGCTCTGACTGTACCACCATCCACTACAACTACATGTGTAACAGTTCCTGCATGGGCGGCATGAACCGGAGGCCCATCCTCACCATCATCACACTGGAAGACTCCAGTGGTAATCTACTGGGACGGAACAGCTTTGAGGTGCGTGTTTGTGC"
            )
        },
        {
            "Sample_ID": "BRCA1_CDS_Region",
            "Sequence": (
                "ATGGATTTATCTGCTCTTCGCGTTGAAGAAGTACAAAATGTCATTAATGCTATGCAGAAAATCTTAGAGTGTCCCATCTGTCTGGAGTTGATCAAGGAACCTGTCTCCACAAAGTGTGACCACATATTTTGCAAATTTTGCATGCTGAAACTTCTCAACCAGAAGAAAGGGCCTTCACAGTGTCCTTTATGTAAGAATGATATAACCAAAAGGAGCCTACAAGAAAGTACGAGATTTAGTCAACTTGTTGA"
                "AGAGCTATTGAAAATCATTTGTGCTTTTCAGCTTGACACAGGTTTGGAGTATGCAAACAGCTATAATTTTGCAAAAAAGGAAAATAACTCTCCTGAACATCTAAAAGATGAAGTTTCTATCATCCAAAGTATGGGCTACAGAAACCGTGCCAAAAGACTTCTACAGAGTGAACCCGAAAATCCTTCCTTGCAGGAAACCAGTCTCAGTGTCCAACTCTCTAACCTTGGAACTGTGAGAACTCTGAGGAC"
            )
        },
        {
            "Sample_ID": "EGFR_Kinase_Domain",
            "Sequence": (
                "GGAAGCCTACGTGATGGCCAGCGTGGACAACCCCCACGTGTGCCGCCTGCTGGGCATCTGCCTCACCTCCACCGTGCAGCTCATCACGCAGCTCATGCCCTTCGGCTGCCTCCTGGACTATGTCCGGGAACACAAAGACAATATTGGCTCCCAGTACCTGCTCAACTGGTGTGTGCAGATCGCAAAGGGCATGAACTACTTGGAGGACCGTCGCTTGGTGCACCGCGACCTGGCAGCCAGGAACGTACTGG"
                "TGAAAACACCGCAGCATGTCAAGATCACAGATTTTGGGCTGGCCAAACTGCTGGGTGCGGAAGAGAAAGAATACCATGCAGAAGGAGGCAAAGTGCCTATCAAGTGGATGGCATTGGAATCAATTTTACACAGAATCTATACCCACCAGAGTGATGTCTGGAGCTACGGGGTGACTGTTTGGGAGTTGATGACCTTTGGATCCAAGCCATATGACGGAATCCCTGCCAGCGAGATCTCCTCCATCCTGG"
            )
        },
        {
            "Sample_ID": "ACTB_Housekeeping_Control",
            "Sequence": (
                "ACCGAGCGCGGCTACAGCTTCACCACCACGGCCGAGCGGGAAATCGTGCGTGACATTAAGGAGAAGCTGTGCTACGTCGCCCTGGACTTCGAGCAAGAGATGGCCACGGCTGCTTCCAGCTCCTCCCTGGAGAAGAGCTACGAGCTGCCTGACGGCCAGGTCATCACCATTGGCAATGAGCGGTTCCGCTGCCCTGAGGCACTCTTCCAGCCTTCCTTCCTGGGCATGGAGTCCTGTGGCATCCACGAAAC"
                "TACCTTCAACTCCATCATGAAGTGTGACGTGGACATCCGCAAAGACCTGTACGCCAACACAGTGCTGTCTGGCGGCACCACCATGTACCCTGGCATTGCCGACAGGATGCAGAAGGAGATCACTGCCCTGGCACCCAGCACAATGAAGATCAAGATCATTGCTCCTCCTGAGCGCAAGTACTCCGTGTGGATCGGCGGCTCCATCCTGGCCTCGCTGTCCACCTTCCAGCAGATGTGGATCAGCAAGCAG"
            )
        }
    ])

# ==========================================
# STEP 3: CUSTOM FIXING CONDITIONS & OPTIMUMS
# ==========================================
if df_seqs is not None and not df_seqs.empty:
    st.markdown("### ⚙️ Custom Fixing Conditions & Thermodynamic Optimums")
    
    preset = st.selectbox(
        "Application Mode Preset (Switching application mode starts a new pipeline run):",
        [
            "qPCR / RT-qPCR (SYBR Green: 80–180 bp Amplicon)",
            "Standard Endpoint PCR (150–400 bp Amplicon)",
            "Sanger Sequencing (400–800 bp Amplicon)",
            "Custom User-Defined Conditions"
        ],
        on_change=reset_on_mode_change_t2
    )
    if "qPCR" in preset:
        default_amp_min, default_amp_max = 80, 180
    elif "Sanger" in preset:
        default_amp_min, default_amp_max = 400, 800
    else:
        default_amp_min, default_amp_max = 150, 400

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**1. Primer Length & Amplicon Span**")
        len_range = st.slider("Primer Length Range (bp):", 16, 30, (18, 22))
        opt_len = st.number_input("Optimum Primer Length (bp):", min_value=16, max_value=30, value=20)
        amp_range = st.slider("Target Amplicon Size (bp):", 60, 1000, (default_amp_min, default_amp_max))

    with c2:
        st.markdown("**2. Melting Temp ($T_m$) & GC% Optimums**")
        tm_range = st.slider("Allowed Tm Range (°C):", 50.0, 72.0, (57.0, 63.0), 0.5)
        opt_tm = st.number_input("Optimum Target Tm (°C):", min_value=50.0, max_value=72.0, value=60.0, step=0.5)
        max_delta_tm = st.slider("Max ΔTm Between Fwd & Rev (°C):", 0.5, 5.0, 1.5, 0.25)
        gc_range = st.slider("Allowed GC Content (%):", 30, 75, (40, 60))
        opt_gc = st.number_input("Optimum Target GC (%):", min_value=30, max_value=75, value=50)

    with c3:
        st.markdown("**3. Structural Fixing Conditions**")
        enforce_clamp = st.checkbox("Enforce 3' GC Clamp (1–3 G/C in last 5 bp)", value=True)
        filter_poly = st.checkbox("Reject Homopolymer Repeats (≥4 identical bases)", value=True)
        filter_dimer = st.checkbox("Screen Against 3' Self/Cross Dimerization", value=True)
        pairs_per_seq = st.selectbox(
            "Backup Primer Pairs per Gene (Ranked #1 to #3):",
            [1, 2, 3],
            index=1,
            help="Outputs the #1 Best Optimum Primer Pair plus up to 2 backup non-overlapping primer pairs per gene."
        )
        fwd_tag = st.text_input("Optional 5' Overhang / Restriction Tag (Forward):", placeholder="e.g. GAATTC")
        rev_tag = st.text_input("Optional 5' Overhang / Restriction Tag (Reverse):", placeholder="e.g. AAGCTT")

    current_file_sig = uploaded_file.name if uploaded_file is not None else ("pasted" if paste_seq.strip() else "demo")
    current_mode_sig = f"{current_file_sig}|{preset}"

    # ==========================================
    # STEP 4: RUN PRIMER DESIGN ENGINE
    # ==========================================
    if st.button("🚀 Run Automated Primer Design"):
        if st.session_state["locked_mode_t2"] is not None and st.session_state["locked_mode_t2"] != current_mode_sig:
            st.session_state["is_unlocked_t2"] = False
        st.session_state["locked_mode_t2"] = current_mode_sig

        with st.spinner("Scanning template coordinates, evaluating thermodynamic ΔG stability, and predicting qPCR amplicon melt peaks..."):
            designed_rows = []
            total_valid_sites_across_all = 0

            for _, row in df_seqs.iterrows():
                sample_id = row["Sample_ID"]
                seq = row["Sequence"]
                seq_len = len(seq)

                fwd_candidates = []
                rev_candidates = []

                step_size = 2 if seq_len <= 1200 else 5
                for l in range(len_range[0], len_range[1] + 1):
                    for pos in range(0, seq_len - l + 1, step_size):
                        sub = seq[pos:pos + l]
                        if len(sub) < l:
                            continue

                        if not (filter_poly and has_homopolymer(sub)):
                            gc_val = calc_gc(sub)
                            if gc_range[0] <= gc_val <= gc_range[1]:
                                tm_val = calc_tm(sub)
                                if tm_range[0] <= tm_val <= tm_range[1]:
                                    clamp_ok, clamp_cnt = check_3prime_clamp(sub)
                                    if (not enforce_clamp) or clamp_ok:
                                        if not (filter_dimer and has_3prime_dimer(sub, sub)):
                                            fwd_candidates.append({
                                                "seq": sub,
                                                "start": pos + 1,
                                                "end": pos + l,
                                                "len": l,
                                                "tm": tm_val,
                                                "gc": gc_val,
                                                "clamp": f"{clamp_cnt}/5 GC",
                                                "dg3": calc_3prime_dg(sub),
                                                "mw": calc_oligo_mw(sub)
                                            })

                        rc_sub = rev_comp(sub)
                        if not (filter_poly and has_homopolymer(rc_sub)):
                            gc_rc = calc_gc(rc_sub)
                            if gc_range[0] <= gc_rc <= gc_range[1]:
                                tm_rc = calc_tm(rc_sub)
                                if tm_range[0] <= tm_rc <= tm_range[1]:
                                    clamp_ok_r, clamp_cnt_r = check_3prime_clamp(rc_sub)
                                    if (not enforce_clamp) or clamp_ok_r:
                                        if not (filter_dimer and has_3prime_dimer(rc_sub, rc_sub)):
                                            rev_candidates.append({
                                                "seq": rc_sub,
                                                "start": pos + 1,
                                                "end": pos + l,
                                                "len": l,
                                                "tm": tm_rc,
                                                "gc": gc_rc,
                                                "clamp": f"{clamp_cnt_r}/5 GC",
                                                "dg3": calc_3prime_dg(rc_sub),
                                                "mw": calc_oligo_mw(rc_sub)
                                            })

                valid_pairs = []
                for f in fwd_candidates:
                    for r in rev_candidates:
                        amp_size = r["end"] - f["start"] + 1
                        if amp_range[0] <= amp_size <= amp_range[1]:
                            delta_tm = abs(f["tm"] - r["tm"])
                            if delta_tm <= max_delta_tm:
                                if filter_dimer and has_3prime_dimer(f["seq"], r["seq"]):
                                    continue

                                tm_pen = abs(f["tm"] - opt_tm) + abs(r["tm"] - opt_tm) + (delta_tm * 1.5)
                                gc_pen = (abs(f["gc"] - opt_gc) + abs(r["gc"] - opt_gc)) * 0.15
                                len_pen = (abs(f["len"] - opt_len) + abs(r["len"] - opt_len)) * 0.5
                                total_pen = tm_pen + gc_pen + len_pen
                                opt_match_rate = max(65.0, round(100.0 - (total_pen * 2.2), 1))

                                valid_pairs.append({
                                    "f": f,
                                    "r": r,
                                    "amp_size": amp_size,
                                    "delta_tm": round(delta_tm, 2),
                                    "opt_rate": opt_match_rate
                                })

                total_valid_in_seq = len(valid_pairs)
                total_valid_sites_across_all += total_valid_in_seq

                valid_pairs.sort(key=lambda x: x["opt_rate"], reverse=True)

                selected = []
                used_starts = []
                for vp in valid_pairs:
                    if all(abs(vp["f"]["start"] - us) > 12 for us in used_starts):
                        selected.append(vp)
                        used_starts.append(vp["f"]["start"])
                    if len(selected) >= pairs_per_seq:
                        break

                if not selected:
                    designed_rows.append({
                        "Sample_ID": sample_id,
                        "Template_Length (bp)": seq_len,
                        "Valid_Pairs_In_Sample": 0,
                        "Pair_Rank": "No Match",
                        "Forward_Primer (5'->3')": "Relax Tm/GC/Amplicon sliders",
                        "Fwd_Binding_Site (bp)": "N/A",
                        "Fwd_Len (bp)": 0,
                        "Fwd_Tm (°C)": 0.0,
                        "Fwd_GC (%)": 0.0,
                        "Reverse_Primer (5'->3')": "Relax Tm/GC/Amplicon sliders",
                        "Rev_Binding_Site (bp)": "N/A",
                        "Rev_Len (bp)": 0,
                        "Rev_Tm (°C)": 0.0,
                        "Rev_GC (%)": 0.0,
                        "Delta_Tm (°C)": 0.0,
                        "Amplicon_Size (bp)": 0,
                        "Amplicon_GC (%)": 0.0,
                        "Predicted_Amplicon_Melt_Tm (°C)": 0.0,
                        "3'_GC_Clamp (Fwd/Rev)": "N/A",
                        "3'_End_DeltaG_kcal_mol (Fwd/Rev)": "N/A",
                        "Oligo_MW_Da (Fwd/Rev)": "N/A",
                        "Optimum_Match_Rate (%)": 0.0,
                        "Optimum_Annealing_Ta (°C)": 0.0,
                        "Recommended_Cycle_Run": "Adjust thresholds",
                        "Amplicon_Sequence (5'->3')": "N/A"
                    })
                else:
                    for rank_idx, item in enumerate(selected, start=1):
                        f = item["f"]
                        r = item["r"]
                        final_f_seq = (fwd_tag.strip().upper() + f["seq"]) if fwd_tag.strip() else f["seq"]
                        final_r_seq = (rev_tag.strip().upper() + r["seq"]) if rev_tag.strip() else r["seq"]
                        
                        amp_seq = seq[f["start"] - 1 : r["end"]]
                        amp_gc = calc_gc(amp_seq)
                        amp_melt_tm = calc_amplicon_melt_tm(amp_seq)

                        opt_ta = round(min(f["tm"], r["tm"]) - 5.0, 1)
                        ext_sec = max(15, int(round((item["amp_size"] / 1000.0) * 60.0)))
                        cycle_protocol = f"Ta: {opt_ta}°C (20s) | Ext: 72°C ({ext_sec}s) | 35 Cycles"

                        designed_rows.append({
                            "Sample_ID": sample_id,
                            "Template_Length (bp)": seq_len,
                            "Valid_Pairs_In_Sample": total_valid_in_seq,
                            "Pair_Rank": f"Rank #{rank_idx}",
                            "Forward_Primer (5'->3')": final_f_seq,
                            "Fwd_Binding_Site (bp)": f"{f['start']} - {f['end']} bp",
                            "Fwd_Len (bp)": len(final_f_seq),
                            "Fwd_Tm (°C)": f["tm"],
                            "Fwd_GC (%)": f["gc"],
                            "Reverse_Primer (5'->3')": final_r_seq,
                            "Rev_Binding_Site (bp)": f"{r['start']} - {r['end']} bp (Comp)",
                            "Rev_Len (bp)": len(final_r_seq),
                            "Rev_Tm (°C)": r["tm"],
                            "Rev_GC (%)": r["gc"],
                            "Delta_Tm (°C)": item["delta_tm"],
                            "Amplicon_Size (bp)": item["amp_size"],
                            "Amplicon_GC (%)": amp_gc,
                            "Predicted_Amplicon_Melt_Tm (°C)": amp_melt_tm,
                            "3'_GC_Clamp (Fwd/Rev)": f"{f['clamp']} | {r['clamp']}",
                            "3'_End_DeltaG_kcal_mol (Fwd/Rev)": f"{f['dg3']} / {r['dg3']}",
                            "Oligo_MW_Da (Fwd/Rev)": f"{f['mw']} / {r['mw']} Da",
                            "Optimum_Match_Rate (%)": item["opt_rate"],
                            "Optimum_Annealing_Ta (°C)": opt_ta,
                            "Recommended_Cycle_Run": cycle_protocol,
                            "Amplicon_Sequence (5'->3')": amp_seq
                        })

            df_out = pd.DataFrame(designed_rows)

            order_rows = []
            fasta_lines = []
            for _, r_row in df_out[df_out["Pair_Rank"] != "No Match"].iterrows():
                base_name = f"{r_row['Sample_ID']}_{r_row['Pair_Rank'].replace(' ', '').replace('#', '')}"
                f_seq = r_row["Forward_Primer (5'->3')"]
                r_seq = r_row["Reverse_Primer (5'->3')"]
                f_pos = r_row["Fwd_Binding_Site (bp)"]
                r_pos = r_row["Rev_Binding_Site (bp)"]

                order_rows.append({
                    "Oligo_Name": f"{base_name}_F",
                    "Sequence_5_to_3": f_seq,
                    "Length_bp": r_row["Fwd_Len (bp)"],
                    "Tm_C": r_row["Fwd_Tm (°C)"],
                    "Binding_Site_bp": f_pos,
                    "Synthesis_Scale": "25 nm",
                    "Purification": "Standard Desalted"
                })
                order_rows.append({
                    "Oligo_Name": f"{base_name}_R",
                    "Sequence_5_to_3": r_seq,
                    "Length_bp": r_row["Rev_Len (bp)"],
                    "Tm_C": r_row["Rev_Tm (°C)"],
                    "Binding_Site_bp": r_pos,
                    "Synthesis_Scale": "25 nm",
                    "Purification": "Standard Desalted"
                })

                fasta_lines.append(f">{base_name}_Forward | Binding:{f_pos} | Tm:{r_row['Fwd_Tm (°C)']}C | Amplicon:{r_row['Amplicon_Size (bp)']}bp")
                fasta_lines.append(f_seq)
                fasta_lines.append(f">{base_name}_Reverse | Binding:{r_pos} | Tm:{r_row['Rev_Tm (°C)']}C | Amplicon:{r_row['Amplicon_Size (bp)']}bp")
                fasta_lines.append(r_seq)

            df_order = pd.DataFrame(order_rows)
            fasta_str = "\n".join(fasta_lines)

            st.session_state["primer_df_t2"] = df_out
            st.session_state["order_df_t2"] = df_order
            st.session_state["fasta_str_t2"] = fasta_str
            st.session_state["stats_t2"] = {
                "samples": len(df_seqs),
                "total_sites": total_valid_sites_across_all,
                "designed_pairs": len(df_out[df_out["Pair_Rank"] != "No Match"]),
                "mean_opt_rate": round(df_out[df_out["Pair_Rank"] != "No Match"]["Optimum_Match_Rate (%)"].mean(), 1) if len(df_out[df_out["Pair_Rank"] != "No Match"]) > 0 else 0.0,
                "mode": preset
            }

# ==========================================
# DISPLAY TABULAR RESULTS, PAYWALL & REMARKS
# ==========================================
if "primer_df_t2" in st.session_state:
    res_df = st.session_state["primer_df_t2"]
    order_df = st.session_state["order_df_t2"]
    fasta_out = st.session_state.get("fasta_str_t2", "")
    stats = st.session_state["stats_t2"]

    st.markdown("---")
    st.markdown("### 📊 Primer Design Coordinate Table & Optimum Run Summary")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Samples Processed", f"{stats['samples']}")
    m2.metric("Total Valid Sites Found", f"{stats['total_sites']:,}")
    m3.metric("Top Primer Pairs Ranked", f"{stats['designed_pairs']}")
    m4.metric("Mean Optimum Run Rate", f"{stats['mean_opt_rate']}%")

    if st.session_state["is_unlocked_t2"]:
        st.success(f"✅ **Payment Verified for [{stats['mode']}]!** You may freely adjust thermodynamic sliders ($T_m$, GC%, length) and re-run within this application mode. Switching the Application Mode preset starts a new session.")
        st.dataframe(res_df, use_container_width=True)

        d1, d2, d3 = st.columns(3)
        with d1:
            st.download_button(
                "⬇️ 1. Full Primer Coordinate & Run Table (.csv)",
                data=res_df.to_csv(index=False).encode("utf-8-sig"),
                file_name="GenomeTech_Primer_Design_Report.csv",
                mime="text/csv"
            )
        with d2:
            st.download_button(
                "⬇️ 2. Vendor Bulk-Order Sheet (.csv)",
                data=order_df.to_csv(index=False).encode("utf-8-sig"),
                file_name="GenomeTech_Vendor_Oligo_Order.csv",
                mime="text/csv"
            )
        with d3:
            st.download_button(
                "⬇️ 3. Primer Sequences for BLAST / Browser (.fasta)",
                data=fasta_out.encode("utf-8-sig"),
                file_name="GenomeTech_Designed_Primers.fasta",
                mime="text/plain"
            )
    else:
        st.markdown("**Live Preview (First 3 Designed Primer Pairs with Coordinates & Run Rates):**")
        st.dataframe(res_df.head(3), use_container_width=True)

        blurred_preview = res_df.iloc[3:10] if len(res_df) > 3 else res_df
        st.markdown('<div class="blurred-table">', unsafe_allow_html=True)
        st.table(blurred_preview)
        st.markdown('</div>', unsafe_allow_html=True)

        razorpay_link = "https://rzp.io/rzp/UVDck3w"
        st.markdown(f"""
        <div class="paywall-overlay">
            <h3 style="color: #e9d5ff !important; margin-top: 0;">🔒 Unlock All {stats['designed_pairs']} Primer Pairs, Vendor Sheet & BLAST FASTA</h3>
            <p style="color: #cbd5e1 !important; font-size: 0.95rem;">
                Your top preview rows are verified above. Complete the $40 OmicsExpress checkout to unlock all designed primer coordinates, qPCR melt-curve predictions, optimum thermal cycler protocols, vendor synthesis sheet, and multi-FASTA file.
            </p>
            <div style="background:rgba(56,189,248,0.14);border:1px solid rgba(56,189,248,0.45);color:#e0f2fe !important;padding:8px 14px;border-radius:8px;font-size:0.88rem;font-weight:600;margin:10px auto 6px auto;max-width:520px;">🔥 <span style="color:#38bdf8 !important;font-weight:800;">FOUNDING LAB LAUNCH OFFER:</span> <s style="color:#94a3b8 !important;">$100 USD</s> <b style="color:#ffffff !important;">$40 USD</b> — Special Early-Access Rate for Our First 20 Research Clients</div><a href="{razorpay_link}" target="_blank" style="background: linear-gradient(90deg, #9333ea 0%, #2563eb 100%); color: white !important; padding: 14px 32px; text-decoration: none; border-radius: 10px; font-weight: 700; font-size: 1.05rem; display: inline-block; margin: 12px 0; border: 1px solid #c084fc; box-shadow: 0 4px 20px rgba(147, 51, 234, 0.5);">
                💳 Pay $40 via Razorpay to Unlock All 3 Files
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
                    st.session_state["is_unlocked_t2"] = True
                    st.rerun()
                else:
                    st.error("Invalid Payment ID. Please paste the 'pay_...' ID shown on your Razorpay payment confirmation screen.")

    st.markdown("---")
    st.markdown("### 📝 Automated Thermodynamic Remarks & Direct Support")

    st.info(
        f"**Automated Primer Design Diagnostics:**\n"
        f"* **Application Pipeline:** {stats['mode']}\n"
        f"* **Candidate Site Density:** Scanned **{stats['samples']}** template sequences and identified **{stats['total_sites']:,}** total valid primer pairs meeting all thermodynamic and structural fixing rules.\n"
        f"* **Biophysical & Melt-Curve Metrics:** Includes 3' pentamer Gibbs Free Energy ($\Delta G$), Oligo Molecular Weight (Da), full amplified product sequences, and predicted SYBR Green amplicon melt-curve temperatures.\n"
        f"* **Optimum Run Rate & Thermal Protocol:** Selected primer pairs achieved a mean optimum match rate of **{stats['mean_opt_rate']}%**. Recommended thermal cycler annealing temperatures ($T_a = T_{{m,\\text{{min}}}} - 5^\\circ\\text{{C}}$) and extension times are listed per pair."
    )

    with st.expander("💬 Send Remarks or Questions Directly to GenomeTech Team (via Email)"):
        client_email = st.text_input("Your Lab / Institutional Email:")
        client_remark = st.text_area("Your Remarks or Questions about this Primer Design Run:")
        if st.button("Prepare Direct Email"):
            subject = urllib.parse.quote(f"OmicsExpress Tool #2 Remark - {client_email}")
            body = urllib.parse.quote(
                f"Client Email: {client_email}\n"
                f"Tool Used: Tool #2 - Automated Batch Primer Designer\n"
                f"Application Mode: {stats['mode']}\n"
                f"Samples Processed: {stats['samples']}\n"
                f"Total Valid Sites Found: {stats['total_sites']}\n"
                f"Mean Optimum Match Rate: {stats['mean_opt_rate']}%\n\n"
                f"Client Remarks:\n{client_remark}"
            )
            mailto_url = f"mailto:bhumikasihare555@gmail.com?subject={subject}&body={body}"
            st.success("✅ Your remark and primer diagnostics are ready! Click below to send directly from your email client:")
            st.markdown(f'👉 <a href="https://mail.google.com/mail/?view=cm&fs=1&to=bhumikasihare555@gmail.com&su={subject}&body={body}" target="_blank" style="color:#38bdf8;font-weight:700;text-decoration:underline;">Click Here to Send via Gmail (Browser)</a> &nbsp;|&nbsp; <a href="{mailto_url}" style="color:#c4b5fd;font-weight:600;text-decoration:underline;">Open in Default Mail App (Outlook/Mac)</a>', unsafe_allow_html=True)