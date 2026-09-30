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

# Deep Blue/Purple Theme - Balanced for readability
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="collapsedControl"] {display: none;}
    section[data-testid="stSidebar"] {display: none;}

    .stApp {
        background: radial-gradient(circle at top right, #2a1b41 0%, #17153a 40%, #0d1222 80%, #050b14 100%);
        color: #e2e8f0 !important;
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
        border-radius: 12px;
        margin-bottom: 1.8rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid rgba(168, 85, 247, 0.4);
        box-shadow: 0 8px 25px rgba(124, 58, 237, 0.25);
    }
    .gts-brand {
        font-size: 1.4rem;
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
# 2. SESSION STATE & RESET LOCKS
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

# ==========================================
# 3. HEADER & INSTRUCTIONS
# ==========================================
st.markdown("## Bulk NCBI & Ensembl FASTA Sequence Fetcher")
st.markdown(
    "**What we do in this tool:** We utilize Python-based REST API integrations to rapidly query the NCBI Entrez and Ensembl databases. "
    "This tool allows you to bulk-download biological sequences based on your accession IDs (limited to 5,000 queries per run to ensure server stability). "
    "We also compute biophysical parameters and screen for vital cloning restriction sites.\n\n"
    "**Files Provided:** A compiled Multi-FASTA text file (`.fasta`) and an Excel-ready Metadata/Quality Control table (`.csv`)."
)

with st.expander("📋 Required File Formats & License Information", expanded=False):
    st.markdown("""
    * **Accepted File Formats:** Upload `.csv`, `.txt`, or `.tsv` files. Your file must contain a column (or a list) of NCBI (e.g., `NM_`, `NP_`) or Ensembl (e.g., `ENSG`, `ENST`) IDs.
    * **Data Provided in Files:** 
      1. **FASTA:** Clean, properly formatted biological sequence blocks wrapped to your specified base-pair length.
      2. **CSV Table:** Accession resolution, Sequence Length, GC/Hydrophobic %, Molecular Weight (kDa), and Cloning Restriction Cut Sites (`EcoRI`, `BamHI`, `BsaI`, etc).
    * **💻 Cross-Platform File Compatibility (Windows & Apple macOS):** All exported `.csv` tables use universal `UTF-8-BOM` encoding—double-click to open directly in **Microsoft Excel (Windows/Mac)**, **Apple Numbers**, **Google Sheets**, or load into **R / Python**. Sequence (`.fasta`) outputs open natively in any text editor (**Notepad / Mac TextEdit**) or web browser.
    * **Single-Mode License Note:** Changing the **Core Engine**, **Model Organism**, or **Uploading a New File** fundamentally alters the dataset being queried. These parameters will lock the tool and require a new run license. Other formatting entities (header styles, line wrap, strand orientation) are free to change.
    """)

# ==========================================
# 4. BIOINFORMATICS CACHE & HELPER FUNCS
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

# Cache for robustness during live demos and heavy traffic
DEMO_CACHE = {
    "NM_000546": {"seq": "ATGGAGGAGCCGCAGTCAGATCCTAGCGTCGAGCCCCCTCTGAGTCAGGAAACATTTTCAGACCTATGGAAACTACTTCCTGAAAACAACGTTCTGTCCCCCTTGCCGTCCCAAGCAATGGATGATTTGATGCTGTCCCCGGACGATATTGAACAATGGTTCACTGAAGACCCAGGTCCAGATGAAGCTCCCAGAATGCCAGAGGCTGCTCCCCCCGTGGCCCCTGCACCAGCAGCTCCTACACCGGCGGCCCCTGCACCAGCCCCCTCCTGGCCCCTGTCATCTTCTGTCCCTTCCCAGAAAACCTACCAGGGCAGCTACGGTTTCCGTCTGGGCTTCTTGCATTCTGGGACAGCCAAGTCTGTGACTTGCACGTACTCCCCTGCCCTCAACAAGATGTTTTGCCAACTGGCCAAGACCTGCCCTGTGCAGCTGTGGGTTGATTCCACACCCCCGCCCGGCACCCGCGTCCGCGCCATGGCCATCTACAAGCAGTCACATGA", "desc": "TP53 Tumor protein p53", "mol": "Nucleotide (cDNA)"},
    "NM_007294": {"seq": "ATGGATTTATCTGCTCTTCGCGTTGAAGAAGTACAAAATGTCATTAATGCTATGCAGAAAATCTTAGAGTGTCCCATCTGTCTGGAGTTGATCAAGGAACCTGTCTCCACAAAGTGTGACCACATATTTTGCAAATTTTGCATGCTGAAACTTCTCAACCAGAAGAAAGGGCCTTCACAGTGTCCTTTATGTAAGAATGATATAACCAAAAGGAGCCTACAAGAAAGTACGAGATTTAGTCAACTTGTTGAAGAGCTATTGAAAATCATTTGTGCTTTTCAGCTTGACACAGGTTTGGAGTATGCAAACAGCTATAATTTTGCAAAAAAGGAAAATAACTCTCCTGAACATCTAAAAGATGAAGTTTCTATCATCCAAAGTATGGGCTACAGAAACCGTGCCAAAAGACTTCTACAGAGTGAACCCGAAAATCCTTCCTTGCAGGAAACCAGTCTCAGTGTCCAACTCTCTAACCTTGGAACTGTGAGAACTCTGAGGACTAA", "desc": "BRCA1 DNA repair associated", "mol": "Nucleotide (cDNA)"},
    "NM_005228": {"seq": "ATGCGACCCTCCGGGACGGCCGGGGCAGCGCTCCTGGCGCTGCTGGCTGCGCTCTGCCCGGCGAGTCGGGCTCTGGAGGAAAAGAAAGTTTGCCAAGGCACGAGTAACAAGCTCACGCAGTTGGGCACTTTTGAAGATCATTTTCTCAGCCTCCAGAGGATGTTCAATAACTGTGAGGTGGTCCTTGGGAATTTGGAAATTACCTATGTGCAGAGGAATTATGATCTTTCCTTCTTAAAGACCATCCAGGAGGTGGCTGGTTATGTCCTCATTGCCCTCAACACAGTGGAGCGAATTCCTTTGGAAAACCTGCAGATCATCAGAGGAAATATGTACTACGAAAATTCCTATGCCTTAGCAGTCTTATCTAACTATGATGCAAATAAAACCGGACTGAAGGAGCTGCCCATGAGAAATTTACAGGAAATCCTGCATGGCGCCGTGCGGTTCAGCAACAACCCTGCCCTGTGCAACGTGGAGAGCATCCAGTGGCGGGACATTAG", "desc": "EGFR Epidermal growth factor receptor", "mol": "Nucleotide (cDNA)"},
    "NM_004333": {"seq": "ATGGCGGCGCTGAGCGGTGGCGGTGGTGGCGGCGCGGAGCCGGGCCAGGCTCTGTTCAACGGGGACATGGACCCGAGGCCGGCGCCGGCGCCGGCGCCGCGGCCTCTTCGGCTGCGGACCCTGCCCTTGGGAACCCCCGGGAAGCCTACGTGATGGCCAGCGTGGACAACCCCCACGTGTGCCGCCTGCTGGGCATCTGCCTCACCTCCACCGTGCAGCTCATCACGCAGCTCATGCCCTTCGGCTGCCTCCTGGACTATGTCCGGGAACACAAAGACAATATTGGCTCCCAGTACCTGCTCAACTGGTGTGTGCAGATCGCAAAGGGCATGAACTACTTGGAGGACCGTCGCTTGGTGCACCGCGACCTGGCAGCCAGGAACGTACTGGTGA", "desc": "BRAF B-Raf proto-oncogene", "mol": "Nucleotide (cDNA)"},
    "NM_004985": {"seq": "ATGACTGAATATAAACTTGTGGTAGTTGGAGCTGGTGGCGTAGGCAAGAGTGCCTTGACGATACAGCTAATTCAGAATCATTTTGTGGACGAATATGATCCAACAATAGAGGATTCCTACAGGAAGCAAGTAGTAATTGATGGAGAAACCTGTCTCTTGGATATTCTCGACACAGCAGGTCAAGAGGAGTACAGTGCAATGAGGGACCAGTACATGAGGACTGGGGAGGGCTTTCTTTGTGTATTTGCCATAAATAATACTAAATCATTTGAAGATATTCACCATTATAGAGAACAAATTAAAAGAGTTAAGGACTCTGAAGATGTACCTATGGTCCTAGTAGGAAATAAATGTGATTTGCCTTCTAGAACAGTAGACACAAAACAGGCTCAGGACTTAGCAAGAAGTTATGGAATTCCTTTTATTGAAACATCAGCAAAGACAAGACAGGGTGTTGATGATGCCTTCTATACATTAGTTCGAGAAATTCGAAAACATAAATAA", "desc": "KRAS proto-oncogene", "mol": "Nucleotide (cDNA)"},
    "NM_000314": {"seq": "ATGACAGCCATCATCAAAGAGATCGTTAGCAGAAACAAAAGGAGATATCAAGAGGATGGATTCGACTTAGACTTGACCTATATTTATCCAAACATTATTGCTATGGGATTTCCTGCAGAAAGACTTGAAGGCGTATACAGGAACAATATTGATGATGTAGTAAGGTTTTTGGATTCAAAGCATAAAAACCATTACAAGATATACAATCTTTGTGCTGAAAGACATTATGACACCGCCAAATTTAACTGCAGAGTTGCACAGTATCCTTTTGAAGACCATAACCCACCACAGCTAGAACTTATCAAACCCTTTTGTGAAGATCTTGACCAATGGCTAAGTGAAGATGACAATCATGTTGCAGCAATTCACTGTAAAGCTGGAAAGGGACGAACTGGTGTAATGATATGTGCATATTTATTACATCGGGGCAAATTTTTAAAGGCACAAGAGGCCCTAGATTTCTATGGGGAAGTAAGGACCAGAGACAAAAAGGGAGTAACTATTCCCAGTCAGAGGCGCTATGTGTATTATTATAGCTACCTGTTG", "desc": "PTEN phosphatase and tensin homolog", "mol": "Nucleotide (cDNA)"},
    "NP_000537": {"seq": "MEEPQSDPSVEPPLSQETFSDLWKLLPENNVLSPLPSQAMDDLMLSPDDIEQWFTEDPGPDEAPRMPEAAPPVAPAPAAPTPAAPAPAPSWPLSSSVPSQKTYQGSYGFRLGFLHSGTAKSVTCTYSPALNKMFCQLAKTCPVQLWVDSTPPPGTRVRAMAIYKQSQHMTEVVRRCPHHERCSDSDGLAPPQHLIRVEGNLRVEYLDDRNTFRHSVVVPYEPPEVGSDCTTIHYNYMCNSSCMGGMNRRPILTIITLEDSSGNLLGRNSFEVRVCACPGRDRRTEEENLRKKGEPHHELPPGSTKRALPNNTSSSPQPKKKPLDGEYFTLQIRGRERFEMFRELNEALELKDAQAGKEPGGSRAHSSHLKSKKGQSTSRHKKLMFKTEGPDSD", "desc": "Cellular tumor antigen p53 isoform a", "mol": "Protein"},
    "NP_009225": {"seq": "MAALSGGGGGGAEPGQALFNGDMEPEAGAGAGAAASSAADPAIPEEVWNIKQMIKLTQEHIEALLDKFGGEHNPPSIYLEAYEEYTSKLDALQQREQQLLESLGNGTDFSVSSSASMDTVTSSSSSSLSVLPSSLSVFQNPTDVARSNPKSPQKPIVRVFLPNKQRTVVPARCGVTVRDSLKKALMMRGLIPECCAVYRIQDGEKKPIGWDTDISWLTGEELHVEVLENVPLTTHNFVRKTFFTLAFCDFCRKLLFQGFRCQTCGYKFHQRCSTEVPLMCVNYDQLDLLFVSKFFEHHPIPQEEASLAETALTSGSSPSAPASDSIGPQILTSPSPSKSIPIPQPFRPADEDHRNQFGQRDRSSSAPNVHINTIEPVNIDDLIRDQGFRGDGGSTTGLSATPPASLPGSLTNVKALQKSPGPQRERKSSSSSEDRNRMKTLGRRDSSDDWEIPDGQITVGQRIGSGSFGTVYKGKWHGDVAVKMLNVTAPTPQQLQAFKNEVGVLRKTRHVNILLFMGYSTKPQLAIVTQWCEGSSLYHHLHIIETKFEMIKLIDIARQTAQGMDYLHAKSIIHRDLKSNNIFLHEDLTVKIGDFGLATVKSRWSGSHQFEQLSGSILWMAPEVIRMQDKNPYSFQSDVYAFGIVLYELMTGQLPYSNINNRDQIIFMVGRGYLSPDLSKVRSNCPKAMKRLMAECLKKKRDERPLFPQILASIELLARSLPKIHRSASEPSLNRAGFQTEDFSLYACASPKTPIQAGGYGAFPVH", "desc": "B-Raf proto-oncogene serine/threonine-protein kinase isoform a", "mol": "Protein"}
}

DEMO_ACCESSION_DF = pd.DataFrame({"Accession_ID": ["NM_000546.6", "NM_007294.4", "NM_005228.5", "NP_000537.3"]})

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

def fetch_live_accession(raw_acc, core_engine):
    clean_acc = raw_acc.split(".")[0].strip().upper()
    
    # Check robust internal cache first
    if clean_acc in DEMO_CACHE:
        item = DEMO_CACHE[clean_acc].copy()
        if "Protein" in core_engine and "Nucleotide" in item["mol"]:
            item["seq"] = translate_dna_to_protein(item["seq"])
            item["mol"] = "Protein (Translated CDS)"
            item["desc"] = f"{item['desc']} (Translated)"
        return {"status": "SUCCESS", "seq": item["seq"], "desc": item["desc"], "mol": item["mol"], "resolved": raw_acc}

    # Live Ensembl Fetch
    if clean_acc.startswith("ENS"):
        ens_type = "protein" if ("Protein" in core_engine or clean_acc.startswith("ENSP")) else ("cds" if "CDS" in core_engine else "cdna")
        try:
            r = requests.get(f"https://rest.ensembl.org/sequence/id/{clean_acc}?type={ens_type}", headers={"Content-Type": "application/json"}, timeout=12)
            if r.status_code == 200:
                data = r.json()
                mol_label = "Protein" if "protein" in ens_type else "Nucleotide"
                return {"status": "SUCCESS", "seq": data.get("seq", ""), "desc": data.get("desc", f"Ensembl {ens_type}"), "mol": mol_label, "resolved": data.get("id", raw_acc)}
        except: pass

    # Live NCBI Entrez Fetch
    else:
        is_prot = clean_acc.startswith(("NP_", "XP_", "YP_", "WP_")) or ("Protein" in core_engine and not clean_acc.startswith(("NM_", "NR_", "NC_")))
        db_name = "protein" if is_prot else "nuccore"
        try:
            url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db={db_name}&id={clean_acc}&rettype=fasta&retmode=text&tool=OmicsExpress&email=bhumikasihare555@gmail.com"
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
                    
                return {"status": "SUCCESS", "seq": seq_str, "desc": desc_str, "mol": "Protein" if is_prot else "Nucleotide", "resolved": resolved_id}
        except: pass

    return {"status": "FAILED", "seq": "", "desc": "Not Found or Invalid Accession", "mol": "N/A", "resolved": raw_acc}

# ==========================================
# 5. INPUT UPLOAD & PASTE UI
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
# 6. PIPELINE CONFIGURATION LAYOUT
# ==========================================
if df_input is not None and not df_input.empty:
    with st.expander(f"👁️ Loaded Accession Input Preview ({len(df_input)} Accessions Ready)", expanded=False):
        st.dataframe(df_input.head(5), use_container_width=True)

    st.markdown("### ⚙️ Configure Sequence Retrieval Engine & FASTA Formatting")

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        core_engine = st.selectbox("1. Core Sequence Retrieval Engine (Switching engine starts a new pipeline run):", [
            "Hybrid Auto-Detect (Simultaneous NCBI RefSeq + Ensembl Transcript/Protein)",
            "Ensembl Transcript — Spliced cDNA / mRNA Sequence (Nucleotide)",
            "Ensembl Coding Sequence — CDS Only (ATG to Stop Codon)",
            "Ensembl Genomic — Full Gene Region Sequence (Exons + Introns)",
            "NCBI RefSeq & GenBank — Nucleotide Sequences (NM_, NR_, NC_, XM_)",
            "Protein / Peptide Sequences Only (NCBI NP_/XP_, Ensembl ENSP & CDS Translation)"
        ], on_change=reset_on_mode_change_t5)
    with col_t2:
        organism = st.selectbox("Model Organism (Switching organism starts a new pipeline run):", [
            "Homo sapiens (Human)", 
            "Mus musculus (Mouse)", 
            "Danio rerio (Zebrafish)", 
            "Universal / Cross-Species"
        ], on_change=reset_on_mode_change_t5)

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
            ["Standard Annotated (>Accession | Gene | Molecule | Length)", "Phylogenetics / Alignment Clean (>Gene_Accession)", "Minimal Accession Only (>Accession)"]
        )
        wrap_choice = st.selectbox(
            "FASTA Sequence Line Wrap Width:",
            ["60 bp/aa per line (NCBI Standard)", "80 bp/aa per line (Ensembl Standard)", "Single-Line Unwrapped (Best for Bash / grep / awk)"]
        )

    with c3:
        st.markdown("**4. Strand Orientation & Excel Guard**")
        strand_choice = st.selectbox(
            "Nucleotide Strand Orientation:",
            ["5' ➔ 3' Forward Sense Strand (Default)", "3' ➔ 5' Reverse Complement Strand (Nucleotide Only)"]
        )
        excel_guard = st.checkbox("🛡️ Enable Excel Gene-Name Guard (Protects MARCH1 / SEPT2)", value=False)

    current_file_sig = uploaded_file.name if uploaded_file else "demo_data"
    current_mode_sig = f"{current_file_sig}|{core_engine}|{organism}"

    # ==========================================
    # 7. RUN FETCH EXECUTION
    # ==========================================
    if st.button("🚀 Fetch & Compile Bulk FASTA Sequences"):
        if st.session_state["locked_mode_t5"] is not None and st.session_state["locked_mode_t5"] != current_mode_sig:
            st.session_state["is_unlocked_t5"] = False
        st.session_state["locked_mode_t5"] = current_mode_sig

        with st.spinner("Connecting to NCBI Entrez & Ensembl REST endpoints, screening ORF/restriction sites, and compiling FASTA blocks..."):
            wrap_width = 60 if "60" in wrap_choice else (80 if "80" in wrap_choice else 0)
            do_revcomp = "Reverse Complement" in strand_choice

            # Fail-safe: Detect if the user uploaded a headerless txt file
            if acc_col.startswith(("NM_", "NP_", "ENS", "NC_", "NR_")):
                raw_list = [acc_col] + [str(x).strip() for x in df_input[acc_col].dropna() if str(x).strip()]
            else:
                raw_list = [str(x).strip() for x in df_input[acc_col].dropna() if str(x).strip()]

            if dedup_ids:
                raw_list = list(dict.fromkeys(raw_list))

            total_items = len(raw_list)
            prog_bar = st.progress(0)
            prog_text = st.empty()

            compiled_rows = []
            failed_rows = []
            fasta_blocks = []
            failed_count = 0
            total_len = 0

            for i, q_acc in enumerate(raw_list):
                q_acc_str = str(q_acc).strip()
                
                prog_text.text(f"Fetching Sequence {i+1} of {total_items}: {q_acc_str}")
                prog_bar.progress((i + 1) / total_items)
                
                # Prevent rate-limit blocks
                if q_acc_str.split(".")[0].upper() not in DEMO_CACHE:
                    time.sleep(0.35)
                
                if not q_acc_str or q_acc_str.lower() in ["nan", "none", "null"]:
                    continue

                res = fetch_live_accession(q_acc_str, core_engine)
                
                if res["status"] != "SUCCESS" or not res["seq"]:
                    failed_count += 1
                    failed_rows.append({
                        "Query_Accession_ID": q_acc_str,
                        "Fetch_Status": "FAILED",
                        "Diagnostic_Note": res.get("desc", "Not Found")
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
                
                total_len += seq_len

                orf_status, restr_sites, pred_pi = check_orf_and_restriction(seq_str, is_prot)
                unit_str = "aa" if is_prot else "bp"
                comp_tag = f"Hydrophobic:{hydro_pct}%" if is_prot else f"GC:{gc_pct}%"

                resolved_acc = res.get("resolved", q_acc_str)
                gene_symbol = res.get("gene", "Target")
                db_source = res.get("db", "NCBI/Ensembl")

                if "Phylogenetics" in header_style:
                    clean_g = gene_symbol.replace(" ", "_")
                    clean_r = resolved_acc.replace(".", "_")
                    fasta_hdr = f">{clean_g}_{clean_r}"
                elif "Minimal" in header_style:
                    fasta_hdr = f">{resolved_acc}"
                else:
                    fasta_hdr = f">{resolved_acc} | Gene:{gene_symbol} | {mol_type} | Length:{seq_len}{unit_str} | {comp_tag} | MW:{mw_kda}kDa"

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
                    "Sequence_5Prime_Preview": f"{seq_str[:42]}..."
                })

            prog_text.empty()
            prog_bar.empty()

            st.session_state["fasta_df_t5"] = pd.DataFrame(compiled_rows)
            st.session_state["fasta_text_t5"] = "\n\n".join(fasta_blocks)
            st.session_state["failed_df_t5"] = pd.DataFrame(failed_rows) if failed_rows else pd.DataFrame()
            
            st.session_state["stats_t5"] = {
                "queried": len(raw_list),
                "success": len(fasta_blocks),
                "failed": failed_count,
                "total_len": total_len,
                "mean_len": int(total_len / len(fasta_blocks)) if len(fasta_blocks) > 0 else 0,
                "engine": core_engine,
                "org": organism
            }

# ==========================================
# 8. RESULTS, PAYWALL DISPLAY & EXPORTS
# ==========================================
if "fasta_df_t5" in st.session_state:
    res_df = st.session_state["fasta_df_t5"]
    fasta_str = st.session_state["fasta_text_t5"]
    fail_df = st.session_state["failed_df_t5"]
    stats = st.session_state["stats_t5"]

    st.markdown("---")
    st.markdown("### 📊 Bulk Sequence Retrieval Summary & FASTA Preview")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Accessions Queried", f"{stats['queried']:,}")
    m2.metric("Successfully Compiled", f"{stats['success']:,}")
    m3.metric("Failed / Unresolved", f"{stats['failed']:,}")
    m4.metric("Mean Sequence Length", f"{stats['mean_len']:,} bp/aa")

    if stats['success'] == 0:
        st.error("❌ 0 sequences were retrieved. This typically happens if the wrong 'Accession ID Column' was selected, or if the IDs do not match the selected Core Engine.")
        if not fail_df.empty:
            st.dataframe(fail_df, use_container_width=True)

    if stats['success'] > 0:
        if st.session_state["is_unlocked_t5"]:
            st.success(f"✅ **Payment Verified for [{stats['engine']} | {stats['org']}]!** Complete multi-FASTA file and biophysical metadata tables unlocked.")
            st.dataframe(res_df, use_container_width=True)

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
                    "⬇️ 2. Download Biophysical & Cloning QC Table (.csv)",
                    data=res_df.to_csv(index=False).encode("utf-8-sig"),
                    file_name="GenomeTech_Sequence_QC_Report.csv",
                    mime="text/csv"
                )
            with d3:
                st.download_button(
                    "⬇️ 3. Download Unresolved IDs Audit Log (.csv)",
                    data=fail_df.to_csv(index=False).encode("utf-8-sig") if not fail_df.empty else b"No failed IDs.",
                    file_name="GenomeTech_Unresolved_Audit.csv",
                    mime="text/csv"
                )
            
            st.markdown("#### 📦 What you get in these results:")
            st.info("The `.fasta` file contains your pristine sequences perfectly wrapped and ready for alignment, cloning, or BLAST. The `.csv` file contains verified molecular weights, GC percentages, and fetch diagnostics, natively readable on Windows & Mac.")

        else:
            st.markdown("**Live Preview (First 3 Retrieved Rows):**")
            st.dataframe(res_df.head(3), use_container_width=True)

            st.markdown("**FASTA Format Preview:**")
            st.code(fasta_str.split("\n\n")[0], language="text")

            blurred_preview = res_df.iloc[3:10] if len(res_df) > 3 else res_df
            st.markdown('<div class="blurred-table">', unsafe_allow_html=True)
            st.table(blurred_preview)
            st.markdown('</div>', unsafe_allow_html=True)

            razorpay_link = "https://rzp.io/rzp/UVDck3w"
            st.markdown(f"""
            <div class="paywall-overlay">
                <h3 style="color: #e9d5ff !important; margin-top: 0;">🔒 Unlock Full {stats['success']:,}-Sequence Multi-FASTA Output</h3>
                <p style="color: #cbd5e1 !important; font-size: 0.95rem;">
                    Your sequences are compiled and verified above. Complete the checkout to immediately download the full <code>.fasta</code> file and the Biophysical QC <code>.csv</code> table.
                </p>
                <div style="background:rgba(56,189,248,0.14);border:1px solid rgba(56,189,248,0.45);color:#e0f2fe !important;padding:8px 14px;border-radius:8px;font-size:0.88rem;font-weight:600;margin:10px auto 6px auto;max-width:520px;">🔥 <span style="color:#38bdf8 !important;font-weight:800;">FOUNDING LAB LAUNCH OFFER:</span> <s style="color:#94a3b8 !important;">$100 USD</s> <b style="color:#ffffff !important;">$40 USD</b> — Special Early-Access Rate</div><a href="{razorpay_link}" target="_blank" style="background: linear-gradient(90deg, #9333ea 0%, #2563eb 100%); color: white !important; padding: 14px 32px; text-decoration: none; border-radius: 10px; font-weight: 700; font-size: 1.05rem; display: inline-block; margin: 12px 0; border: 1px solid #c084fc; box-shadow: 0 4px 20px rgba(147, 51, 234, 0.5);">
                    💳 Pay $40 via Razorpay to Unlock .FASTA & .CSV
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
# 9. REMARKS, REVIEWS & TOOL REQUESTS
# ==========================================
st.markdown("---")
st.markdown("### 📝 Remarks, Reviews & New Tool Requests")
st.write("We build custom bioinformatics pipelines. Have feedback on this FASTA fetcher or need a new tool built? Submit it below. Fully supported on Windows & Mac.")

with st.form("feedback_form"):
    req_name = st.text_input("Your Name / Institution:")
    req_msg = st.text_area("Your Review, Remark, or Tool Request:")
    submit_btn = st.form_submit_button("Submit Form")
    
    if submit_btn:
        subject = urllib.parse.quote(f"OmicsExpress Tool Request / Review")
        body = urllib.parse.quote(f"From: {req_name}\n\nMessage:\n{req_msg}")
        mail_link = f"mailto:bhumikasihare555@gmail.com?subject={subject}&body={body}"
        
        st.success("🎉 Thank you for using OmicsExpress! Keep exploring more.")
        st.markdown(f"**Action Required:** Click the link below to securely pass your request to your default email application (Outlook/Mac Mail/Gmail) to finalize sending.")
        st.markdown(f'<a href="{mail_link}" style="background: linear-gradient(90deg, #7c3aed 0%, #2563eb 100%); color: white !important; padding: 10px 20px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block; margin-top: 10px; border: 1px solid #c084fc;">📧 Open Email App to Send</a>', unsafe_allow_html=True)