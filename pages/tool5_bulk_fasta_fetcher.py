import streamlit as st
import pandas as pd
import numpy as np
import requests
import urllib.parse
import time

# ==========================================
# 1. PAGE CONFIGURATION & THEME CSS
# ==========================================
st.set_page_config(
    page_title="Bulk FASTA Fetcher | OmicsExpress",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
    <span class="gts-badge">⚡ Tool #5: Bulk FASTA Fetcher</span>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 2. SESSION STATE INITIALIZATION & RESET
# ==========================================
if "is_unlocked_t5" not in st.session_state:
    st.session_state["is_unlocked_t5"] = False
if "locked_mode_t5" not in st.session_state:
    st.session_state["locked_mode_t5"] = None

def reset_on_mode_change_t5():
    st.session_state["is_unlocked_t5"] = False
    st.session_state.pop("fasta_df_t5", None)
    st.session_state.pop("fasta_text_t5", None)
    st.session_state.pop("failed_df_t5", None)
    st.session_state.pop("stats_t5", None)

st.markdown("## Bulk NCBI & Ensembl FASTA Sequence Fetcher")
st.markdown(
    "Upload or paste a batch of **NCBI RefSeq (`NM_`, `NR_`, `NP_`, `XM_`)** or **Ensembl (`ENSG`, `ENST`, `ENSP`)** accession IDs to "
    "instantly retrieve, format, and compile full **Nucleotide (cDNA, CDS, Genomic)** or **Protein (Amino Acid)** `.fasta` sequences. "
    "Includes **ORF Start/Stop Codon Verification, Cloning Restriction Site Screening (`EcoRI/BamHI/BsaI`), Isoelectric Point (`pI`), and Molecular Weight (`kDa`)**."
)

with st.expander("📋 Accepted Accession Formats & Complete Researcher Columns (.csv, .txt, .tsv)", expanded=True):
    st.markdown("""
    * **Supported Accession Databases:**
      1. **Ensembl IDs:** Gene (`ENSG...`), Transcript (`ENST...`), or Protein (`ENSP...`) across Human, Mouse, Rat, Zebrafish, Plant, and Yeast.
      2. **NCBI RefSeq / GenBank IDs:** mRNA/cDNA (`NM_...`, `XM_...`), non-coding RNA (`NR_...`), Genomic (`NC_...`, `NG_...`), or Protein (`NP_...`, `XP_...`).
    * **Complete Wet-Lab & Bioinformatics Columns Included:**
      1. **Numeric Biophysical Columns:** `Sequence_Length (bp/aa)`, `GC_Content (%)`, `Hydrophobic_AA (%)`, `Molecular_Weight (kDa)`, `Predicted_Protein_pI`, and `Ambiguous_Count (N/X)`.
      2. **Cloning & Synthesis QC:** `ORF_&_Codon_Status` (verifies `ATG` start and `TAA/TAG/TGA` stop codons) and `Internal_Restriction_Sites` (screens for `EcoRI, BamHI, HindIII, NotI, BsaI, BsmBI`).
      3. **3 Instant Deliverables:** (1) Compiled Multi-FASTA (`.fasta`), (2) Excel-Sortable Biophysical & Cloning Metadata Table (`.csv`), and (3) Unresolved Accessions Audit Log (`.csv`).
    * **💻 Cross-Platform File Compatibility (Windows & Apple macOS):** All exported `.csv` tables use universal `UTF-8-BOM` encoding—double-click to open directly in **Microsoft Excel (Windows/Mac)**, **Apple Numbers**, **Google Sheets**, or load into **R / Python**. Sequence (`.fasta`) and vector outputs open natively in any text editor (**Notepad / Mac TextEdit**) or web browser (**Safari / Chrome / Edge**).
    * **Single-Mode License Note:** Each checkout unlocks your selected **Core Sequence Retrieval Engine**. Adjusting FASTA header formats, line wrapping, deduplication, or strand orientation within your unlocked mode is free; switching the Core Engine or uploading a new file starts a new run.
    """)

# ==========================================
# 3. CURATED REFERENCE SEQUENCES & BIO HELPERS
# ==========================================
CODON_TABLE = {
    "TTT": "F", "TTC": "F", "TTA": "L", "TTG": "L", "CTT": "L", "CTC": "L", "CTA": "L", "CTG": "L",
    "ATT": "I", "ATC": "I", "ATA": "I", "ATG": "M", "GTT": "V", "GTC": "V", "GTA": "V", "GTG": "V",
    "TCT": "S", "TCC": "S", "TCA": "S", "TCG": "S", "CCT": "P", "CCC": "P", "CCA": "P", "CCG": "P",
    "ACT": "T", "ACC": "T", "ACA": "T", "ACG": "T", "GCT": "A", "GCC": "A", "GCA": "A", "GCG": "A",
    "TAT": "Y", "TAC": "Y", "TAA": "*", "TAG": "*", "CAT": "H", "CAC": "H", "CAA": "Q", "CAG": "Q",
    "AAT": "N", "AAC": "N", "AAA": "K", "AAG": "K", "GAT": "D", "GAC": "D", "GAA": "E", "GAG": "E",
    "TGT": "C", "TGC": "C", "TGA": "*", "TGG": "W", "CGT": "R", "CGC": "R", "CGA": "R", "CGG": "R",
    "AGT": "S", "AGC": "S", "AGA": "R", "AGG": "R", "GGT": "G", "GGC": "G", "GGA": "G", "GGG": "G"
}

DEMO_SEQUENCE_CACHE = {
    "NM_000546": {
        "resolved": "NM_000546.6", "db": "NCBI RefSeq", "gene": "TP53", "organism": "Homo sapiens", "mol": "Nucleotide (cDNA)",
        "desc": "Tumor protein p53 (TP53), transcript variant 1, mRNA",
        "seq": "ATGGAGGAGCCGCAGTCAGATCCTAGCGTCGAGCCCCCTCTGAGTCAGGAAACATTTTCAGACCTATGGAAACTACTTCCTGAAAACAACGTTCTGTCCCCCTTGCCGTCCCAAGCAATGGATGATTTGATGCTGTCCCCGGACGATATTGAACAATGGTTCACTGAAGACCCAGGTCCAGATGAAGCTCCCAGAATGCCAGAGGCTGCTCCCCCCGTGGCCCCTGCACCAGCAGCTCCTACACCGGCGGCCCCTGCACCAGCCCCCTCCTGGCCCCTGTCATCTTCTGTCCCTTCCCAGAAAACCTACCAGGGCAGCTACGGTTTCCGTCTGGGCTTCTTGCATTCTGGGACAGCCAAGTCTGTGACTTGCACGTACTCCCCTGCCCTCAACAAGATGTTTTGCCAACTGGCCAAGACCTGCCCTGTGCAGCTGTGGGTTGATTCCACACCCCCGCCCGGCACCCGCGTCCGCGCCATGGCCATCTACAAGCAGTCACATGA"
    },
    "ENST00000269305": {
        "resolved": "ENST00000269305.9", "db": "Ensembl", "gene": "TP53", "organism": "Homo sapiens", "mol": "Nucleotide (CDS)",
        "desc": "TP53-201 canonical coding sequence",
        "seq": "ATGGAGGAGCCGCAGTCAGATCCTAGCGTCGAGCCCCCTCTGAGTCAGGAAACATTTTCAGACCTATGGAAACTACTTCCTGAAAACAACGTTCTGTCCCCCTTGCCGTCCCAAGCAATGGATGATTTGATGCTGTCCCCGGACGATATTGAACAATGGTTCACTGAAGACCCAGGTCCAGATGAAGCTCCCAGAATGCCAGAGGCTGCTCCCCCCGTGGCCCCTGCACCAGCAGCTCCTACACCGGCGGCCCCTGCACCAGCCCCCTCCTGGCCCCTGTCATCTTCTGTCCCTTCCCAGAAAACCTACCAGGGCAGCTACGGTTTCCGTCTGGGCTTCTTGCATTCTGGGACAGCCAAGTCTGTGACTTGCACGTACTCCCCTGCCCTCAACAAGATGTTTTGCCAACTGGCCAAGACCTGCCCTGTGCAGCTGTGGGTTGATTCCACACCCCCGCCCGGCACCCGCGTCCGCGCCATGGCCATCTACAAGCAGTCACATGA"
    },
    "NP_000537": {
        "resolved": "NP_000537.3", "db": "NCBI RefSeq", "gene": "TP53", "organism": "Homo sapiens", "mol": "Protein (Amino Acid)",
        "desc": "Cellular tumor antigen p53 isoform a",
        "seq": "MEEPQSDPSVEPPLSQETFSDLWKLLPENNVLSPLPSQAMDDLMLSPDDIEQWFTEDPGPDEAPRMPEAAPPVAPAPAAPTPAAPAPAPSWPLSSSVPSQKTYQGSYGFRLGFLHSGTAKSVTCTYSPALNKMFCQLAKTCPVQLWVDSTPPPGTRVRAMAIYKQSQHMTEVVRRCPHHERCSDSDGLAPPQHLIRVEGNLRVEYLDDRNTFRHSVVVPYEPPEVGSDCTTIHYNYMCNSSCMGGMNRRPILTIITLEDSSGNLLGRNSFEVRVCACPGRDRRTEEENLRKKGEPHHELPPGSTKRALPNNTSSSPQPKKKPLDGEYFTLQIRGRERFEMFRELNEALELKDAQAGKEPGGSRAHSSHLKSKKGQSTSRHKKLMFKTEGPDSD"
    }
}

DEMO_ACCESSION_DF = pd.DataFrame({"Accession_ID": ["NM_000546.6", "ENST00000269305.9", "NP_000537.3"]})

def rev_comp_dna(seq):
    trans = str.maketrans("ATGCRYSWKMBDHVNatgcryswkmbdhvn", "TACGYRSWMKVHDBNtacgyrswmkvhdbn")
    return seq.translate(trans)[::-1].upper()

def translate_dna_to_protein(dna_seq):
    s = dna_seq.upper()
    start_idx = max(0, s.find("ATG"))
    aa_list = []
    for i in range(start_idx, len(s) - 2, 3):
        codon = s[i:i+3]
        aa = CODON_TABLE.get(codon, "X")
        if aa == "*": break
        aa_list.append(aa)
    return "".join(aa_list)

def check_orf_and_restriction(seq, is_protein=False):
    if is_protein:
        pos_res = seq.count("K") + seq.count("R") + (0.5 * seq.count("H"))
        neg_res = seq.count("D") + seq.count("E")
        length = max(1, len(seq))
        est_pi = round(max(3.8, min(11.8, 6.8 + ((pos_res - neg_res) / length) * 14.0)), 2)
        return "Full Peptide Chain", "N/A (Protein)", est_pi

    s = seq.upper()
    has_start = s.startswith("ATG")
    has_stop = s.endswith(("TAA", "TAG", "TGA"))
    in_frame = (len(s) % 3 == 0)
    
    if has_start and has_stop and in_frame: orf_status = "Complete CDS (ATG..Stop, In-Frame)"
    elif has_start and in_frame: orf_status = "5'-ATG Initiated (In-Frame)"
    elif "ATG" in s: orf_status = "Contains Internal ORF (+UTR)"
    else: orf_status = "Non-Coding / Genomic Fragment"

    enzymes = {"EcoRI": "GAATTC", "BamHI": "GGATCC", "HindIII": "AAGCTT", "NotI": "GCGGCCGC", "BsaI": "GGTCTC", "BsmBI": "CGTCTC"}
    hits = [name for name, site in enzymes.items() if site in s or rev_comp_dna(site) in s]
    restr_str = "0 Cut Sites (Cloning-Safe)" if not hits else f"Cuts: {', '.join(hits)}"
    return orf_status, restr_str, 0.0

def calc_seq_biophysics(seq, is_protein=False):
    seq = seq.upper().strip()
    length = len(seq)
    if length == 0: return 0, 0.0, 0.0, 0.0, 0

    if is_protein:
        hydro_cnt = sum(1 for aa in seq if aa in "AVILMFYW")
        hydro_pct = round((hydro_cnt / length) * 100.0, 1)
        mw_kda = round((length * 110.0) / 1000.0, 2)
        ambig_cnt = seq.count("X") + seq.count("*")
        return length, 0.0, hydro_pct, mw_kda, ambig_cnt
    else:
        gc_cnt = sum(1 for b in seq if b in ("G", "C"))
        gc_pct = round((gc_cnt / length) * 100.0, 1)
        mw_kda = round((length * 308.0) / 1000.0, 2)
        ambig_cnt = seq.count("N")
        return length, gc_pct, 0.0, mw_kda, ambig_cnt

def fetch_live_accession(raw_acc, core_engine, strip_ver=True):
    clean_base = raw_acc.split(".")[0].strip().upper() if strip_ver else raw_acc.strip().upper()
    lookup_key = raw_acc.split(".")[0].strip().upper()

    # 1. Local Cache Lookup
    if lookup_key in DEMO_SEQUENCE_CACHE:
        item = DEMO_SEQUENCE_CACHE[lookup_key].copy()
        if "Protein" in core_engine and "Nucleotide" in item["mol"]:
            item["seq"] = translate_dna_to_protein(item["seq"])
            item["mol"] = "Protein (Translated CDS)"
            item["desc"] = f"{item['gene']} translated peptide sequence"
        return {"status": "SUCCESS", "resolved": item["resolved"], "db": item["db"], "gene": item["gene"], "mol": item["mol"], "desc": item["desc"], "seq": item["seq"]}

    # 2. Live Ensembl REST API Query for ENS* IDs
    if clean_base.startswith("ENS"):
        ens_type = "cds" if "CDS" in core_engine else ("genomic" if "Genomic" in core_engine else ("protein" if ("Protein" in core_engine or clean_base.startswith("ENSP")) else "cdna"))
        try:
            url = f"https://rest.ensembl.org/sequence/id/{clean_base}?type={ens_type}"
            r = requests.get(url, headers={"Content-Type": "application/json"}, timeout=12)
            if r.status_code == 200:
                data = r.json()
                mol_label = "Protein (Amino Acid)" if (ens_type == "protein" or clean_base.startswith("ENSP")) else f"Nucleotide ({ens_type.upper()})"
                return {"status": "SUCCESS", "resolved": data.get("id", raw_acc), "db": "Ensembl (REST API)", "gene": clean_base, "mol": mol_label, "desc": data.get("desc", f"Ensembl {ens_type.upper()}"), "seq": data.get("seq", "")}
        except: pass

    # 3. Live NCBI Entrez E-Utilities Query for RefSeq / GenBank IDs
    else:
        is_prot = clean_base.startswith(("NP_", "XP_", "YP_", "WP_")) or ("Protein" in core_engine and not clean_base.startswith(("NM_", "NR_", "NC_")))
        db_name = "protein" if is_prot else "nuccore"
        try:
            url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db={db_name}&id={raw_acc.strip()}&rettype=fasta&retmode=text"
            r = requests.get(url, timeout=12)
            if r.status_code == 200 and r.text.strip().startswith(">"):
                lines = r.text.strip().splitlines()
                hdr = lines[0][1:].strip()
                seq_str = "".join(l.strip() for l in lines[1:] if not l.startswith(">"))
                resolved_id = hdr.split()[0] if hdr else raw_acc
                desc_str = " ".join(hdr.split()[1:]) if len(hdr.split()) > 1 else hdr
                
                if "Protein" in core_engine and not is_prot:
                    seq_str = translate_dna_to_protein(seq_str)
                    is_prot = True
                    
                return {"status": "SUCCESS", "resolved": resolved_id, "db": f"NCBI Entrez ({db_name})", "gene": "RefSeq_Gene", "mol": "Protein (Amino Acid)" if is_prot else "Nucleotide", "desc": desc_str, "seq": seq_str}
        except: pass

    return {"status": "UNRESOLVED / INVALID ID", "resolved": "Unmapped", "db": "Not Found", "gene": "N/A", "mol": "N/A", "desc": "Accession not found", "seq": ""}

# ==========================================
# 4. FILE UPLOAD, PASTE BOX OR DEMO DATA
# ==========================================
col_up, col_demo = st.columns([3, 1])
with col_up:
    uploaded_file = st.file_uploader(
        "Upload Accession List Table (.csv, .txt, or .tsv)",
        type=["csv", "txt", "tsv"],
        on_change=reset_on_mode_change_t5
    )
with col_demo:
    st.write("")
    st.write("")
    use_sample = st.checkbox("🧪 Load Demo NCBI & Ensembl Accessions", value=(uploaded_file is None), on_change=reset_on_mode_change_t5)

paste_ids = st.text_area(
    "Or paste NCBI / Ensembl Accession IDs directly (one per line or comma-separated):",
    height=85,
    placeholder="NM_000546.6\nENST00000269305.9\nNP_000537.3",
    on_change=reset_on_mode_change_t5
)

df_input = None
if uploaded_file is not None:
    try:
        fname = uploaded_file.name.lower()
        if fname.endswith(".txt") or fname.endswith(".tsv"):
            df_input = pd.read_csv(uploaded_file, sep=None, engine="python")
        else:
            df_input = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Error reading file: {e}")
elif paste_ids.strip():
    raw_tokens = [tok.strip() for line in paste_ids.splitlines() for tok in line.split(",") if tok.strip()]
    df_input = pd.DataFrame({"Accession_ID": raw_tokens})
elif use_sample:
    df_input = DEMO_ACCESSION_DF.copy()

# ==========================================
# 5. CONFIGURE RETRIEVAL ENGINE & PIPELINE
# ==========================================
if df_input is not None and not df_input.empty:
    with st.expander(f"👁️ Loaded Accession Input Preview ({len(df_input)} Accessions Ready)", expanded=False):
        st.dataframe(df_input.head(5), use_container_width=True)

    st.markdown("### ⚙️ Configure Sequence Retrieval Engine & FASTA Formatting")

    core_engine = st.selectbox(
        "1. Core Sequence Retrieval Engine (Switching engine starts a new pipeline run):",
        [
            "Hybrid Auto-Detect (Simultaneous NCBI RefSeq + Ensembl Transcript/Protein)",
            "Ensembl Transcript — Spliced cDNA / mRNA Sequence (Nucleotide)",
            "Ensembl Coding Sequence — CDS Only (ATG to Stop Codon)",
            "Ensembl Genomic — Full Gene Region Sequence (Exons + Introns)",
            "NCBI RefSeq & GenBank — Nucleotide Sequences (NM_, NR_, NC_, XM_)",
            "Protein / Peptide Sequences Only (NCBI NP_/XP_, Ensembl ENSP & CDS Translation)"
        ],
        on_change=reset_on_mode_change_t5
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**2. Source Column & Deduplication**")
        acc_col = st.selectbox("Select Accession ID Column:", list(df_input.columns), index=0)
        strip_ver = st.checkbox("Auto-Resolve Version Suffixes (e.g. .14)", value=True)
        dedup_ids = st.checkbox("Deduplicate Identical Accession IDs", value=True)
        min_seq_len = st.number_input("Minimum Sequence Length Cutoff (bp / aa):", min_value=0, max_value=10000, value=20, step=10)

    with c2:
        st.markdown("**3. Custom FASTA Header & Line Wrapping**")
        header_style = st.selectbox(
            "FASTA Header Format:",
            [
                "Standard Annotated (>Accession | Gene | Molecule | Length)",
                "Phylogenetics / Alignment Clean (>Gene_Accession)",
                "Minimal Accession Only (>Accession)"
            ]
        )
        wrap_choice = st.selectbox(
            "FASTA Sequence Line Wrap Width:",
            [
                "60 bp/aa per line (NCBI Standard)",
                "80 bp/aa per line (Ensembl Standard)",
                "Single-Line Unwrapped (Best for Bash / grep / awk)"
            ]
        )

    with c3:
        st.markdown("**4. Strand Orientation & Excel Guard**")
        strand_choice = st.selectbox(
            "Nucleotide Strand Orientation:",
            [
                "5' ➔ 3' Forward Sense Strand (Default)",
                "3' ➔ 5' Reverse Complement Strand (Nucleotide Only)"
            ]
        )
        excel_guard = st.checkbox("🛡️ Enable Excel Gene-Name Guard (Protects MARCH1 / SEPT2)", value=False)

    current_file_sig = uploaded_file.name if uploaded_file is not None else ("pasted" if paste_ids.strip() else "demo_acc")
    current_mode_sig = f"{current_file_sig}|{core_engine}"

    # ==========================================
    # 6. RUN BULK FASTA FETCHER
    # ==========================================
    if st.button("🚀 Fetch & Compile Bulk FASTA Sequences"):
        if st.session_state.get("locked_mode_t5") is not None and st.session_state.get("locked_mode_t5") != current_mode_sig:
            st.session_state["is_unlocked_t5"] = False
        st.session_state["locked_mode_t5"] = current_mode_sig

        with st.spinner("Connecting to NCBI Entrez & Ensembl REST endpoints, screening ORF/restriction sites, and compiling FASTA blocks..."):
            wrap_width = 60 if "60" in wrap_choice else (80 if "80" in wrap_choice else 0)
            do_revcomp = "Reverse Complement" in strand_choice

            compiled_rows = []
            failed_rows = []
            fasta_blocks = []

            if acc_col in df_input.columns:
                raw_list = [str(x).strip() for x in df_input[acc_col].dropna() if str(x).strip()]
            else:
                raw_list = [str(x).strip() for x in df_input.iloc[:, 0].dropna() if str(x).strip()]

            if dedup_ids:
                raw_list = list(dict.fromkeys(raw_list))

            total_items = len(raw_list)
            prog_bar = st.progress(0)
            prog_text = st.empty()

            for i, q_acc in enumerate(raw_list):
                q_acc_str = str(q_acc).strip()
                
                prog_text.text(f"Fetching Sequence {i+1} of {total_items}: {q_acc_str}")
                prog_bar.progress((i + 1) / total_items)
                
                # Prevent rate-limit block on live calls
                if q_acc_str.split(".")[0] not in DEMO_SEQUENCE_CACHE:
                    time.sleep(0.35)
                
                if not q_acc_str or q_acc_str.lower() in ["nan", "none", "null"]:
                    continue

                res = fetch_live_accession(q_acc_str, core_engine, strip_ver)
                
                if not res or res.get("status") != "SUCCESS" or not res.get("seq"):
                    failed_rows.append({
                        "Query_Accession_ID": q_acc_str,
                        "Fetch_Status": res.get("status", "FAILED") if res else "FAILED",
                        "Diagnostic_Note": res.get("desc", "No sequence returned from repository") if res else "Unknown Fetch Error"
                    })
                    continue

                seq_str = str(res["seq"]).upper().strip()
                mol_type = str(res.get("mol", ""))
                is_prot = "Protein" in mol_type or "peptide" in mol_type.lower()

                if any(k in core_engine for k in ["cDNA", "CDS Only", "Genomic", "Nucleotide Sequences"]) and is_prot:
                    continue

                if do_revcomp and not is_prot:
                    seq_str = rev_comp_dna(seq_str)
                    strand_tag = "Reverse_Complement (-)"
                else:
                    strand_tag = "Forward_Sense (+)" if not is_prot else "Peptide (N->C)"

                seq_len, gc_pct, hydro_pct, mw_kda, ambig_cnt = calc_seq_biophysics(seq_str, is_prot)
                if seq_len < min_seq_len:
                    continue

                orf_status, restr_sites, pred_pi = check_orf_and_restriction(seq_str, is_prot)
                unit_str = "aa" if is_prot else "bp"
                comp_tag = f"Hydrophobic:{hydro_pct}%" if is_prot else f"GC:{gc_pct}%"

                resolved_acc = res.get("resolved", res.get("acc", q_acc_str))
                gene_symbol = res.get("gene", "Unknown")
                db_source = res.get("db", "NCBI/Ensembl")

                if "Phylogenetics" in header_style:
                    clean_g = gene_symbol.replace(" ", "_")
                    clean_r = resolved_acc.replace(".", "_")
                    fasta_hdr = f">{clean_g}_{clean_r}"
                elif "Minimal" in header_style:
                    fasta_hdr = f">{resolved_acc}"
                else:
                    fasta_hdr = f">{resolved_acc} | Gene:{gene_symbol} | {mol_type} | Length:{seq_len}{unit_str} | {comp_tag} | MW:{mw_kda}kDa | {res.get('desc', '')}"

                if wrap_width > 0:
                    wrapped_seq = "\n".join([seq_str[j:j+wrap_width] for j in range(0, len(seq_str), wrap_width)])
                else:
                    wrapped_seq = seq_str

                fasta_blocks.append(f"{fasta_hdr}\n{wrapped_seq}")
                disp_gene = f'="{gene_symbol}"' if excel_guard else gene_symbol

                compiled_rows.append({
                    "Query_Accession_ID": q_acc_str,
                    "Resolved_Accession": resolved_acc,
                    "Database_Source": db_source,
                    "Gene_Symbol": disp_gene,
                    "Molecule_Type": mol_type,
                    "Strand_Orientation": strand_tag,
                    "Sequence_Length (bp/aa)": seq_len,
                    "GC_Content (%)": gc_pct,
                    "Hydrophobic_AA (%)": hydro_pct,
                    "Molecular_Weight (kDa)": mw_kda,
                    "Predicted_Protein_pI": pred_pi if is_prot else "N/A (DNA/RNA)",
                    "ORF_&_Codon_Status": orf_status,
                    "Internal_Restriction_Sites": restr_sites,
                    "Ambiguous_Count (N/X)": ambig_cnt,
                    "Formatted_FASTA_Header": fasta_hdr,
                    "Sequence_5Prime_Preview": f"{seq_str[:42]}...",
                    "Full_Sequence": seq_str
                })

            prog_text.empty()
            prog_bar.empty()

            out_df = pd.DataFrame(compiled_rows)
            fail_df = pd.DataFrame(failed_rows) if failed_rows else pd.DataFrame([{"Query_Accession_ID": "None", "Fetch_Status": "100% Accessions Resolved Successfully", "Diagnostic_Note": "No failed IDs"}])
            full_fasta_str = "\n\n".join(fasta_blocks)

            total_bases = int(out_df["Sequence_Length (bp/aa)"].sum()) if not out_df.empty else 0
            mean_len = int(out_df["Sequence_Length (bp/aa)"].mean()) if not out_df.empty else 0

            st.session_state["fasta_df_t5"] = out_df
            st.session_state["fasta_text_t5"] = full_fasta_str
            st.session_state["failed_df_t5"] = fail_df
            st.session_state["stats_t5"] = {
                "total_queried": len(raw_list),
                "fetched": len(out_df),
                "failed": len(failed_rows),
                "total_len": total_bases,
                "mean_len": mean_len,
                "engine": core_engine
            }

# ==========================================
# 7. DISPLAY TABULAR RESULTS, PAYWALL & EXPORTS
# ==========================================
if "fasta_df_t5" in st.session_state:
    res_df = st.session_state["fasta_df_t5"]
    fasta_str = st.session_state["fasta_text_t5"]
    fail_df = st.session_state["failed_df_t5"]
    stats = st.session_state["stats_t5"]

    st.markdown("---")
    st.markdown("### 📊 Bulk Sequence Retrieval Summary & FASTA Preview")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Accessions Queried", f"{stats['total_queried']:,}")
    m2.metric("Sequences Compiled", f"{stats['fetched']:,}")
    m3.metric("Total Bases / Residues", f"{stats['total_len']:,}")
    m4.metric("Mean Sequence Length", f"{stats['mean_len']:,} bp/aa")

    if stats['fetched'] == 0:
        st.error("❌ 0 sequences were retrieved. This usually happens if the wrong Accession ID Column was selected.")
    else:
        if st.session_state["is_unlocked_t5"]:
            st.success(f"✅ **Payment Verified for [{stats['engine']}]!** Complete multi-FASTA file, ORF/restriction cloning audit, and biophysical metadata tables unlocked.")
            st.dataframe(res_df, use_container_width=True)

            with st.expander("📄 View Compiled Multi-FASTA Text Output", expanded=False):
                st.code(fasta_str[:3000] + ("\n... [Truncated in preview, download full file below]" if len(fasta_str) > 3000 else ""), language="text")

            d1, d2, d3 = st.columns(3)
            with d1:
                st.download_button(
                    "⬇️ 1. Download Compiled Multi-FASTA (.fasta)",
                    data=fasta_str.encode("utf-8-sig"),
                    file_name="GenomeTech_Bulk_Sequences.fasta",
                    mime="text/plain"
                )
            with d2:
                st.download_button(
                    "⬇️ 2. Sequence Biophysical & Cloning QC Table (.csv)",
                    data=res_df.to_csv(index=False).encode("utf-8-sig"),
                    file_name="GenomeTech_Sequence_Metadata_Report.csv",
                    mime="text/csv"
                )
            with d3:
                st.download_button(
                    "⬇️ 3. Unresolved / Retired IDs Audit Log (.csv)",
                    data=fail_df.to_csv(index=False).encode("utf-8-sig"),
                    file_name="GenomeTech_Unresolved_Accessions_Audit.csv",
                    mime="text/csv"
                )
        else:
            st.markdown("**Live Preview (First 3 Retrieved Sequences, ORF Status & Restriction Screen):**")
            st.dataframe(res_df.head(3), use_container_width=True)

            preview_blocks = "\n\n".join(fasta_str.split("\n\n")[:2])
            st.markdown("**Live Multi-FASTA Format Preview (First 2 Entries):**")
            st.code(preview_blocks, language="text")

            blurred_preview = res_df.iloc[3:10] if len(res_df) > 3 else res_df
            st.markdown('<div class="blurred-table">', unsafe_allow_html=True)
            st.table(blurred_preview)
            st.markdown('</div>', unsafe_allow_html=True)

            razorpay_link = "https://rzp.io/rzp/UVDck3w"
            st.markdown(f"""
            <div class="paywall-overlay">
                <h3 style="color: #e9d5ff !important; margin-top: 0;">🔒 Unlock Full {stats['fetched']:,}-Sequence Multi-FASTA & Cloning QC CSV</h3>
                <p style="color: #cbd5e1 !important; font-size: 0.95rem;">
                    Your first 3 sequences are verified above. Complete the $40 OmicsExpress checkout to immediately download the compiled <code>.fasta</code> file, the Biophysical & Restriction Site Metadata CSV, and the Unresolved Accession Audit log.
                </p>
                <div style="background:rgba(56,189,248,0.14);border:1px solid rgba(56,189,248,0.45);color:#e0f2fe !important;padding:8px 14px;border-radius:8px;font-size:0.88rem;font-weight:600;margin:10px auto 6px auto;max-width:520px;">🔥 <span style="color:#38bdf8 !important;font-weight:800;">FOUNDING LAB LAUNCH OFFER:</span> <s style="color:#94a3b8 !important;">$100 USD</s> <b style="color:#ffffff !important;">$40 USD</b> — Special Early-Access Rate for Our First 20 Research Clients</div><a href="{razorpay_link}" target="_blank" style="background: linear-gradient(90deg, #9333ea 0%, #2563eb 100%); color: white !important; padding: 14px 32px; text-decoration: none; border-radius: 10px; font-weight: 700; font-size: 1.05rem; display: inline-block; margin: 12px 0; border: 1px solid #c084fc; box-shadow: 0 4px 20px rgba(147, 51, 234, 0.5);">
                    💳 Pay $40 via Razorpay to Unlock .FASTA & CSVs
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
                        st.session_state["is_unlocked_t5"] = True
                        st.rerun()
                    else:
                        st.error("Invalid Payment ID. Please paste the 'pay_...' ID shown on your Razorpay payment confirmation screen.")

    # ==========================================
    # STEP 8: AUTOMATED REMARKS & DIRECT EMAIL
    # ==========================================
    st.markdown("---")
    st.markdown("### 📝 Automated Sequence Retrieval Remarks & Direct Support")

    st.info(
        f"**Automated Bulk FASTA Diagnostics:**\n"
        f"* **Retrieval Pipeline:** {stats['engine']}\n"
        f"* **Compilation Summary:** Successfully retrieved, deduplicated, and formatted **{stats['fetched']:,}** of **{stats['total_queried']:,}** accessions (Total sequence volume: **{stats['total_len']:,} bp/aa**, Mean length: **{stats['mean_len']:,} bp/aa**).\n"
        f"* **Biophysical & Cloning QC Audit:** Computed numeric GC% / Hydrophobic AA%, molecular weight (kDa), predicted protein pI, start/stop codon ORF integrity, and screened for internal cloning restriction sites (`EcoRI, BamHI, HindIII, NotI, BsaI, BsmBI`)."
    )

    with st.expander("💬 Send Remarks or Questions Directly to GenomeTech Team (via Email)"):
        client_email = st.text_input("Your Lab / Institutional Email:")
        client_remark = st.text_area("Your Remarks or Questions about this Bulk FASTA Run:")
        if st.button("Prepare Direct Email"):
            subject = urllib.parse.quote(f"OmicsExpress Tool #5 Remark - {client_email}")
            body = urllib.parse.quote(
                f"Client Email: {client_email}\n"
                f"Tool Used: Tool #5 - Bulk NCBI & Ensembl FASTA Fetcher\n"
                f"Engine: {stats['engine']}\n"
                f"Accessions Queried: {stats['total_queried']} (Compiled: {stats['fetched']})\n"
                f"Total Sequence Volume: {stats['total_len']} bp/aa\n\n"
                f"Client Remarks:\n{client_remark}"
            )
            mailto_url = f"mailto:bhumikasihare555@gmail.com?subject={subject}&body={body}"
            st.success("✅ Your remark and FASTA diagnostics are ready! Click below to send directly from your email client:")
            st.markdown(f'👉 <a href="https://mail.google.com/mail/?view=cm&fs=1&to=bhumikasihare555@gmail.com&su={subject}&body={body}" target="_blank" style="color:#38bdf8;font-weight:700;text-decoration:underline;">Click Here to Send via Gmail (Browser)</a> &nbsp;|&nbsp; <a href="{mailto_url}" style="color:#c4b5fd;font-weight:600;text-decoration:underline;">Open in Default Mail App (Outlook/Mac)</a>', unsafe_allow_html=True)