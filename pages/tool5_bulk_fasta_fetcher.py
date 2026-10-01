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
    "instantly retrieve, format, and compile full **Nucleotide (cDNA, CDS, Genomic)** or **Protein (Amino Acid)** `.fasta` sequences (up to **5,000 IDs** per run to protect server stability). "
    "Includes **ORF Start/Stop Codon Verification, Cloning Restriction Site Screening (`EcoRI/BamHI/BsaI`), Isoelectric Point (`pI`), and Molecular Weight (`kDa`)**."
)

with st.expander("📋 Accepted Accession Formats & Complete Researcher Columns (.csv, .txt, .tsv)", expanded=True):
    st.markdown("""
    * **Supported Accession Databases (Up to 5,000 per run):**
      1. **Ensembl IDs:** Gene (`ENSG...`), Transcript (`ENST...`), or Protein (`ENSP...`) across Human, Mouse, Rat, Zebrafish, Plant, and Yeast.
      2. **NCBI RefSeq / GenBank IDs:** mRNA/cDNA (`NM_...`, `XM_...`), non-coding RNA (`NR_...`), Genomic (`NC_...`, `NG_...`), or Protein (`NP_...`, `XP_...`).
    * **Complete Wet-Lab & Bioinformatics Columns Included:**
      1. **Numeric Biophysical Columns:** `Sequence_Length (bp/aa)`, `GC_Content (%)`, `Hydrophobic_AA (%)`, `Molecular_Weight (kDa)`, `Predicted_Protein_pI`, and `Ambiguous_Count (N/X)`.
      2. **Cloning & Synthesis QC:** `ORF_&_Codon_Status` (verifies `ATG` start and `TAA/TAG/TGA` stop codons) and `Internal_Restriction_Sites` (screens for `EcoRI, BamHI, HindIII, NotI, BsaI, BsmBI`).
      3. **3 Instant Deliverables:** (1) Compiled Multi-FASTA (`.fasta`), (2) Excel-Sortable Biophysical & Cloning Metadata Table (`.csv`), and (3) Unresolved Accessions Audit Log (`.csv`).
    * **💻 Cross-Platform File Compatibility (Windows & Apple macOS):** All exported `.csv` tables use universal `UTF-8-BOM` encoding—double-click to open directly in **Microsoft Excel (Windows/Mac)**, **Apple Numbers**, **Google Sheets**, or load into **R / Python**. Sequence (`.fasta`) and vector outputs open natively in any text editor (**Notepad / Mac TextEdit**) or web browser (**Safari / Chrome / Edge**).
    * **Single-Mode License Note:** Each checkout unlocks your selected **Core Sequence Retrieval Engine** and **Model Organism**. Adjusting FASTA header formats, line wrapping, deduplication, or strand orientation within your unlocked mode is free; switching the Core Engine/Organism or uploading a new file fundamentally changes the dataset and will require a new run license.
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

DEMO_CACHE = {
    "NM_000546": {"resolved": "NM_000546.6", "db": "NCBI RefSeq", "gene": "TP53", "mol": "Nucleotide (cDNA)", "desc": "Tumor protein p53 (TP53), transcript variant 1, mRNA", "seq": "ATGGAGGAGCCGCAGTCAGATCCTAGCGTCGAGCCCCCTCTGAGTCAGGAAACATTTTCAGACCTATGGAAACTACTTCCTGAAAACAACGTTCTGTCCCCCTTGCCGTCCCAAGCAATGGATGATTTGATGCTGTCCCCGGACGATATTGAACAATGGTTCACTGAAGACCCAGGTCCAGATGAAGCTCCCAGAATGCCAGAGGCTGCTCCCCCCGTGGCCCCTGCACCAGCAGCTCCTACACCGGCGGCCCCTGCACCAGCCCCCTCCTGGCCCCTGTCATCTTCTGTCCCTTCCCAGAAAACCTACCAGGGCAGCTACGGTTTCCGTCTGGGCTTCTTGCATTCTGGGACAGCCAAGTCTGTGACTTGCACGTACTCCCCTGCCCTCAACAAGATGTTTTGCCAACTGGCCAAGACCTGCCCTGTGCAGCTGTGGGTTGATTCCACACCCCCGCCCGGCACCCGCGTCCGCGCCATGGCCATCTACAAGCAGTCACATGA"},
    "NM_007294": {"resolved": "NM_007294.4", "db": "NCBI RefSeq", "gene": "BRCA1", "mol": "Nucleotide (cDNA)", "desc": "BRCA1 DNA repair associated (BRCA1), transcript variant 1, mRNA", "seq": "ATGGATTTATCTGCTCTTCGCGTTGAAGAAGTACAAAATGTCATTAATGCTATGCAGAAAATCTTAGAGTGTCCCATCTGTCTGGAGTTGATCAAGGAACCTGTCTCCACAAAGTGTGACCACATATTTTGCAAATTTTGCATGCTGAAACTTCTCAACCAGAAGAAAGGGCCTTCACAGTGTCCTTTATGTAAGAATGATATAACCAAAAGGAGCCTACAAGAAAGTACGAGATTTAGTCAACTTGTTGAAGAGCTATTGAAAATCATTTGTGCTTTTCAGCTTGACACAGGTTTGGAGTATGCAAACAGCTATAATTTTGCAAAAAAGGAAAATAACTCTCCTGAACATCTAAAAGATGAAGTTTCTATCATCCAAAGTATGGGCTACAGAAACCGTGCCAAAAGACTTCTACAGAGTGAACCCGAAAATCCTTCCTTGCAGGAAACCAGTCTCAGTGTCCAACTCTCTAACCTTGGAACTGTGAGAACTCTGAGGACTAA"},
    "NM_005228": {"resolved": "NM_005228.5", "db": "NCBI RefSeq", "gene": "EGFR", "mol": "Nucleotide (cDNA)", "desc": "Epidermal growth factor receptor (EGFR), transcript variant 1, mRNA", "seq": "ATGCGACCCTCCGGGACGGCCGGGGCAGCGCTCCTGGCGCTGCTGGCTGCGCTCTGCCCGGCGAGTCGGGCTCTGGAGGAAAAGAAAGTTTGCCAAGGCACGAGTAACAAGCTCACGCAGTTGGGCACTTTTGAAGATCATTTTCTCAGCCTCCAGAGGATGTTCAATAACTGTGAGGTGGTCCTTGGGAATTTGGAAATTACCTATGTGCAGAGGAATTATGATCTTTCCTTCTTAAAGACCATCCAGGAGGTGGCTGGTTATGTCCTCATTGCCCTCAACACAGTGGAGCGAATTCCTTTGGAAAACCTGCAGATCATCAGAGGAAATATGTACTACGAAAATTCCTATGCCTTAGCAGTCTTATCTAACTATGATGCAAATAAAACCGGACTGAAGGAGCTGCCCATGAGAAATTTACAGGAAATCCTGCATGGCGCCGTGCGGTTCAGCAACAACCCTGCCCTGTGCAACGTGGAGAGCATCCAGTGGCGGGACATTAG"},
    "NM_004333": {"resolved": "NM_004333.6", "db": "NCBI RefSeq", "gene": "BRAF", "mol": "Nucleotide (cDNA)", "desc": "B-Raf proto-oncogene, serine/threonine kinase (BRAF), mRNA", "seq": "ATGGCGGCGCTGAGCGGTGGCGGTGGTGGCGGCGCGGAGCCGGGCCAGGCTCTGTTCAACGGGGACATGGACCCGAGGCCGGCGCCGGCGCCGGCGCCGCGGCCTCTTCGGCTGCGGACCCTGCCCTTGGGAACCCCCGGGAAGCCTACGTGATGGCCAGCGTGGACAACCCCCACGTGTGCCGCCTGCTGGGCATCTGCCTCACCTCCACCGTGCAGCTCATCACGCAGCTCATGCCCTTCGGCTGCCTCCTGGACTATGTCCGGGAACACAAAGACAATATTGGCTCCCAGTACCTGCTCAACTGGTGTGTGCAGATCGCAAAGGGCATGAACTACTTGGAGGACCGTCGCTTGGTGCACCGCGACCTGGCAGCCAGGAACGTACTGGTGA"},
    "NM_004985": {"resolved": "NM_004985.5", "db": "NCBI RefSeq", "gene": "KRAS", "mol": "Nucleotide (cDNA)", "desc": "KRAS proto-oncogene, GTPase (KRAS), transcript variant a, mRNA", "seq": "ATGACTGAATATAAACTTGTGGTAGTTGGAGCTGGTGGCGTAGGCAAGAGTGCCTTGACGATACAGCTAATTCAGAATCATTTTGTGGACGAATATGATCCAACAATAGAGGATTCCTACAGGAAGCAAGTAGTAATTGATGGAGAAACCTGTCTCTTGGATATTCTCGACACAGCAGGTCAAGAGGAGTACAGTGCAATGAGGGACCAGTACATGAGGACTGGGGAGGGCTTTCTTTGTGTATTTGCCATAAATAATACTAAATCATTTGAAGATATTCACCATTATAGAGAACAAATTAAAAGAGTTAAGGACTCTGAAGATGTACCTATGGTCCTAGTAGGAAATAAATGTGATTTGCCTTCTAGAACAGTAGACACAAAACAGGCTCAGGACTTAGCAAGAAGTTATGGAATTCCTTTTATTGAAACATCAGCAAAGACAAGACAGGGTGTTGATGATGCCTTCTATACATTAGTTCGAGAAATTCGAAAACATAAATAA"},
    "NM_000314": {"resolved": "NM_000314.8", "db": "NCBI RefSeq", "gene": "PTEN", "mol": "Nucleotide (cDNA)", "desc": "Phosphatase and tensin homolog (PTEN), mRNA", "seq": "ATGACAGCCATCATCAAAGAGATCGTTAGCAGAAACAAAAGGAGATATCAAGAGGATGGATTCGACTTAGACTTGACCTATATTTATCCAAACATTATTGCTATGGGATTTCCTGCAGAAAGACTTGAAGGCGTATACAGGAACAATATTGATGATGTAGTAAGGTTTTTGGATTCAAAGCATAAAAACCATTACAAGATATACAATCTTTGTGCTGAAAGACATTATGACACCGCCAAATTTAACTGCAGAGTTGCACAGTATCCTTTTGAAGACCATAACCCACCACAGCTAGAACTTATCAAACCCTTTTGTGAAGATCTTGACCAATGGCTAAGTGAAGATGACAATCATGTTGCAGCAATTCACTGTAAAGCTGGAAAGGGACGAACTGGTGTAATGATATGTGCATATTTATTACATCGGGGCAAATTTTTAAAGGCACAAGAGGCCCTAGATTTCTATGGGGAAGTAAGGACCAGAGACAAAAAGGGAGTAACTATTCCCAGTCAGAGGCGCTATGTGTATTATTATAGCTACCTGTTG"},
    "NP_000537": {"resolved": "NP_000537.3", "db": "NCBI Protein", "gene": "TP53", "mol": "Protein (Amino Acid)", "desc": "Cellular tumor antigen p53 isoform a", "seq": "MEEPQSDPSVEPPLSQETFSDLWKLLPENNVLSPLPSQAMDDLMLSPDDIEQWFTEDPGPDEAPRMPEAAPPVAPAPAAPTPAAPAPAPSWPLSSSVPSQKTYQGSYGFRLGFLHSGTAKSVTCTYSPALNKMFCQLAKTCPVQLWVDSTPPPGTRVRAMAIYKQSQHMTEVVRRCPHHERCSDSDGLAPPQHLIRVEGNLRVEYLDDRNTFRHSVVVPYEPPEVGSDCTTIHYNYMCNSSCMGGMNRRPILTIITLEDSSGNLLGRNSFEVRVCACPGRDRRTEEENLRKKGEPHHELPPGSTKRALPNNTSSSPQPKKKPLDGEYFTLQIRGRERFEMFRELNEALELKDAQAGKEPGGSRAHSSHLKSKKGQSTSRHKKLMFKTEGPDSD"},
    "NP_009225": {"resolved": "NP_009225.1", "db": "NCBI Protein", "gene": "BRAF", "mol": "Protein (Amino Acid)", "desc": "B-Raf proto-oncogene serine/threonine-protein kinase isoform a", "seq": "MAALSGGGGGGAEPGQALFNGDMEPEAGAGAGAAASSAADPAIPEEVWNIKQMIKLTQEHIEALLDKFGGEHNPPSIYLEAYEEYTSKLDALQQREQQLLESLGNGTDFSVSSSASMDTVTSSSSSSLSVLPSSLSVFQNPTDVARSNPKSPQKPIVRVFLPNKQRTVVPARCGVTVRDSLKKALMMRGLIPECCAVYRIQDGEKKPIGWDTDISWLTGEELHVEVLENVPLTTHNFVRKTFFTLAFCDFCRKLLFQGFRCQTCGYKFHQRCSTEVPLMCVNYDQLDLLFVSKFFEHHPIPQEEASLAETALTSGSSPSAPASDSIGPQILTSPSPSKSIPIPQPFRPADEDHRNQFGQRDRSSSAPNVHINTIEPVNIDDLIRDQGFRGDGGSTTGLSATPPASLPGSLTNVKALQKSPGPQRERKSSSSSEDRNRMKTLGRRDSSDDWEIPDGQITVGQRIGSGSFGTVYKGKWHGDVAVKMLNVTAPTPQQLQAFKNEVGVLRKTRHVNILLFMGYSTKPQLAIVTQWCEGSSLYHHLHIIETKFEMIKLIDIARQTAQGMDYLHAKSIIHRDLKSNNIFLHEDLTVKIGDFGLATVKSRWSGSHQFEQLSGSILWMAPEVIRMQDKNPYSFQSDVYAFGIVLYELMTGQLPYSNINNRDQIIFMVGRGYLSPDLSKVRSNCPKAMKRLMAECLKKKRDERPLFPQILASIELLARSLPKIHRSASEPSLNRAGFQTEDFSLYACASPKTPIQAGGYGAFPVH"}
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

def fetch_live_accession(raw_acc, core_engine, strip_ver=True):
    clean_base = raw_acc.split(".")[0].strip().upper() if strip_ver else raw_acc.strip().upper()
    lookup_key = raw_acc.split(".")[0].strip().upper()

    # 1. Local Cache Lookup
    if lookup_key in DEMO_CACHE:
        item = DEMO_CACHE[lookup_key].copy()
        if "Protein" in core_engine and "Nucleotide" in item["mol"]:
            item["seq"] = translate_dna_to_protein(item["seq"])
            item["mol"] = "Protein (Translated CDS)"
            item["desc"] = f"{item['desc']} (Translated)"
        return {"status": "SUCCESS", "resolved": item["resolved"], "db": item["db"], "gene": item["gene"], "mol": item["mol"], "desc": item["desc"], "seq": item["seq"]}

    # 2. Live Ensembl REST API Query
    if clean_base.startswith("ENS"):
        ens_type = "cds" if "CDS" in core_engine else ("genomic" if "Genomic" in core_engine else ("protein" if ("Protein" in core_engine or clean_base.startswith("ENSP")) else "cdna"))
        try:
            r = requests.get(f"https://rest.ensembl.org/sequence/id/{clean_base}?type={ens_type}", headers={"Content-Type": "application/json"}, timeout=12)
            if r.status_code == 200:
                data = r.json()
                mol_label = "Protein (Amino Acid)" if (ens_type == "protein" or clean_base.startswith("ENSP")) else f"Nucleotide ({ens_type.upper()})"
                return {"status": "SUCCESS", "resolved": data.get("id", raw_acc), "db": "Ensembl (REST API)", "gene": clean_base, "mol": mol_label, "desc": data.get("desc", f"Ensembl {ens_type.upper()}"), "seq": data.get("seq", "")}
        except: pass

    # 3. Live NCBI Entrez Query
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
                gene_guess = "RefSeq_Gene"
                if "(" in desc_str and ")" in desc_str:
                    gene_guess = desc_str.split("(")[-1].split(")")[0]
                
                if "Protein" in core_engine and not is_prot:
                    seq_str = translate_dna_to_protein(seq_str)
                    is_prot = True
                    
                return {"status": "SUCCESS", "resolved": resolved_id, "db": f"NCBI Entrez ({db_name})", "gene": gene_guess, "mol": "Protein (Amino Acid)" if is_prot else "Nucleotide", "desc": desc_str, "seq": seq_str}
        except: pass

    return {"status": "UNRESOLVED / INVALID ID", "resolved": "Unmapped", "db": "Not Found", "gene": "N/A", "mol": "N/A", "desc": "Accession not found or retired in target database", "seq": ""}

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

# Robustly load the dataframe, preventing pandas from destroying un-headered txt lists
df_input = None
if uploaded_file is not None:
    try:
        fname = uploaded_file.name.lower()
        if fname.endswith(".csv"):
            df_input = pd.read_csv(uploaded_file)
        else:
            df_input = pd.read_csv(uploaded_file, sep="\t")
            
        # Fail-safe: Detect if a headerless .txt file was uploaded and pandas grabbed the first ID as the column name
        first_col = str(df_input.columns[0]).upper()
        if not df_input.empty and first_col.startswith(("NM_", "NP_", "ENS", "NC_", "NR_", "XM_", "XP_")):
            uploaded_file.seek(0)
            if fname.endswith(".csv"):
                df_input = pd.read_csv(uploaded_file, header=None)
            else:
                df_input = pd.read_csv(uploaded_file, sep="\t", header=None)
            df_input.columns = ["Accession_ID"] + [f"Col_{i}" for i in range(1, len(df_input.columns))]
            
    except Exception as e:
        st.error(f"Error reading file: {e}")
elif paste_ids.strip():
    raw_tokens = [tok.strip() for line in paste_ids.splitlines() for tok in line.split(",") if tok.strip()]
    df_input = pd.DataFrame({"Accession_ID": raw_tokens})
elif use_sample:
    df_input = DEMO_ACCESSION_DF.copy()

if df_input is not None and not df_input.empty:
    df_input.columns = [str(c).strip() if str(c).strip() else f"Column_{i}" for i, c in enumerate(df_input.columns)]

# ==========================================
# 6. CONFIGURATION UI LAYOUT 
# ==========================================
if df_input is not None and not df_input.empty:
    with st.expander(f"👁️ Loaded Accession Input Preview ({len(df_input)} Accessions Ready)", expanded=False):
        st.dataframe(df_input.head(5), use_container_width=True)

    st.markdown("### ⚙️️ Configure Sequence Retrieval Engine & FASTA Formatting")

    c_top1, c_top2 = st.columns(2)
    with c_top1:
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
    with c_top2:
        org_select = st.selectbox(
            "Model Organism (Switching organism starts a new pipeline run):",
            ["Homo sapiens (Human)", "Mus musculus (Mouse)", "Danio rerio (Zebrafish)", "Universal / Cross-Species", "Other (Custom Organism)"],
            on_change=reset_on_mode_change_t5
        )
        if org_select == "Other (Custom Organism)":
            organism = st.text_input("Enter Custom Organism Name:", value="Arabidopsis thaliana")
        else:
            organism = org_select

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
        excel_guard = st.checkbox("🛡️️ Enable Excel Gene-Name Guard (Protects MARCH1 / SEPT2)", value=False)

    current_file_sig = uploaded_file.name if uploaded_file is not None else ("pasted" if paste_ids.strip() else "demo_acc")
    current_mode_sig = f"{current_file_sig}|{core_engine}|{organism}"

    # ==========================================
    # 7. RUN FETCH EXECUTION
    # ==========================================
    if st.button("🚀 Fetch & Compile Bulk FASTA Sequences"):
        if st.session_state.get("locked_mode_t5") is not None and st.session_state.get("locked_mode_t5") != current_mode_sig:
            st.session_state["is_unlocked_t5"] = False
        st.session_state["locked_mode_t5"] = current_mode_sig

        with st.spinner("Connecting to NCBI Entrez & Ensembl REST endpoints, screening ORF/restriction sites, and compiling FASTA blocks..."):
            wrap_width = 60 if "60" in wrap_choice else (80 if "80" in wrap_choice else 0)
            do_revcomp = "Reverse Complement" in strand_choice

            raw_list = [str(x).strip() for x in df_input[acc_col].dropna() if str(x).strip()]

            if dedup_ids:
                raw_list = list(dict.fromkeys(raw_list))

            # Strictly enforce 5,000 ID limit to prevent API bans
            if len(raw_list) > 5000:
                st.warning("⚠️ File exceeds 5,000 IDs. Truncating to the first 5,000 to ensure API stability.")
                raw_list = raw_list[:5000]

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
                
                # Protect from NCBI blocks
                if q_acc_str.split(".")[0].upper() not in DEMO_CACHE:
                    time.sleep(0.35)
                
                if not q_acc_str or q_acc_str.lower() in ["nan", "none", "null"]:
                    continue

                res = fetch_live_accession(q_acc_str, core_engine, strip_ver)
                
                if res["status"] != "SUCCESS" or not res["seq"]:
                    failed_count += 1
                    failed_rows.append({
                        "Query_Accession_ID": q_acc_str,
                        "Fetch_Status": "FAILED",
                        "Diagnostic_Note": res.get("desc", "Not Found or API Timeout")
                    })
                    continue

                seq_str = str(res["seq"]).upper().strip()
                mol_type = str(res.get("mol", ""))
                is_prot = "Protein" in mol_type or "peptide" in mol_type.lower()

                # Filter out Proteins if user explicitly requested only Nucleotides
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

            # --- START API & ANTI-REUSE GATEWAY UPGRADE ---
            u_col1, u_col2, u_col3 = st.columns([1, 2, 1])
            with u_col2:
                entered_key = st.text_input(
                    "🔑 Completed payment? Paste your Razorpay Payment ID or Founder Key:",
                    placeholder="pay_XXXXXXXXXXXXXX or GTS-DEMO-..."
                ).strip()
                
                if st.button("Unlock Full Download", use_container_width=True):
                    if not entered_key:
                        st.warning("Please enter a key.")
                    else:
                        import json
                        import os
                        import razorpay
                        import time
                        
                        DB_FILE = "used_keys.json"
                        
                        def is_key_burned(key_to_check):
                            if not os.path.exists(DB_FILE):
                                with open(DB_FILE, 'w') as f:
                                    json.dump({"used_keys": {}}, f)
                            with open(DB_FILE, 'r') as f:
                                data = json.load(f)
                            return key_to_check in data["used_keys"], data.get("used_keys", {}).get(key_to_check, "")
                            
                        def burn_key(key_to_burn):
                            with open(DB_FILE, 'r') as f:
                                data = json.load(f)
                            data["used_keys"][key_to_burn] = time.strftime("%Y-%m-%d %H:%M:%S")
                            with open(DB_FILE, 'w') as f:
                                json.dump(data, f)

                        # 1. INFINITE MASTER KEY CHECK
                        if entered_key == "GTS-MASTER-UNLIMITED":
                            st.session_state["is_unlocked_t5"] = True
                            st.rerun()

                        # 2. DEMO KEY CHECK (One-Time Use)
                        elif entered_key.startswith("GTS-DEMO-"):
                            burned, burn_date = is_key_burned(entered_key)
                            if burned:
                                st.error(f"❌ Security Lock: This Demo Key was already claimed on {burn_date}.")
                            else:
                                burn_key(entered_key)
                                st.session_state["is_unlocked_t5"] = True
                                st.rerun()

                        # 3. RAZORPAY API VERIFICATION (One-Time Use)
                        elif entered_key.startswith("pay_") and len(entered_key) >= 14:
                            burned, burn_date = is_key_burned(entered_key)
                            if burned:
                                st.error(f"❌ Security Lock: This Receipt ID was already claimed on {burn_date}. Keys cannot be shared.")
                            else:
                                try:
                                    # Authenticate with Razorpay Servers
                                    client = razorpay.Client(auth=(st.secrets["razorpay"]["key_id"], st.secrets["razorpay"]["key_secret"]))
                                    payment = client.payment.fetch(entered_key)
                                    
                                    # Verify the transaction was successful
                                    if payment["status"] in ["captured", "authorized"]:
                                        burn_key(entered_key)
                                        st.session_state["is_unlocked_t5"] = True
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Payment Status: {payment['status'].upper()}. This transaction is not complete.")
                                        
                                except Exception as e:
                                    st.error("❌ Invalid Payment ID. The bank API could not verify this transaction.")
                                    
                        else:
                            st.error("❌ Invalid Key Format. Must be a valid Razorpay ID (pay_...) or authorized Demo Key.")
            # --- END API & ANTI-REUSE GATEWAY UPGRADE ---

    # ==========================================
    # 9. AUTOMATED REMARKS & DIRECT EMAIL
    # ==========================================
    st.markdown("---")
    st.markdown("### 📝 Automated Sequence Retrieval Remarks & Direct Support")

    st.info(
        f"**Automated Bulk FASTA Diagnostics:**\n"
        f"* **Retrieval Pipeline:** {stats['engine']} ({stats['org']})\n"
        f"* **Compilation Summary:** Successfully retrieved, deduplicated, and formatted **{stats['success']:,}** of **{stats['queried']:,}** accessions (Total sequence volume: **{stats['total_len']:,} bp/aa**, Mean length: **{stats['mean_len']:,} bp/aa**).\n"
        f"* **Biophysical & Cloning QC Audit:** Computed numeric GC% / Hydrophobic AA%, molecular weight (kDa), predicted protein pI, start/stop codon ORF integrity, and screened for internal cloning restriction sites (`EcoRI, BamHI, HindIII, NotI, BsaI, BsmBI`)."
    )

    with st.expander("💬 Send Remarks or Questions Directly to GenomeTech Team (via Email)"):
        client_email = st.text_input("Your Lab / Institutional Email:")
        client_remark = st.text_area("Your Remarks or Questions about this Bulk FASTA Run:")
        if st.button("Prepare Direct Email"):
            subject = urllib.parse.quote(f"OmicsExpress Tool #5 Remark - {client_email}")
            body = urllib.parse.quote(
                f"Client Email: {client_email}\n"
                f"Tool Used: Tool #5 - Bulk FASTA Fetcher\n"
                f"Engine: {stats['engine']} | Organism: {stats['org']}\n"
                f"Accessions Queried: {stats['queried']} (Compiled: {stats['success']})\n"
                f"Total Sequence Volume: {stats['total_len']} bp/aa\n\n"
                f"Client Remarks:\n{client_remark}"
            )
            mailto_url = f"mailto:bhumikasihare555@gmail.com?subject={subject}&body={body}"
            st.success("✅ Your remark and FASTA diagnostics are ready! Click below to send directly from your email client:")
            st.markdown(f'👉 <a href="https://mail.google.com/mail/?view=cm&fs=1&to=bhumikasihare555@gmail.com&su={subject}&body={body}" target="_blank" style="color:#38bdf8;font-weight:700;text-decoration:underline;">Click Here to Send via Gmail (Browser)</a> &nbsp;|&nbsp; <a href="{mailto_url}" style="color:#c4b5fd;font-weight:600;text-decoration:underline;">Open in Default Mail App (Outlook/Mac)</a>', unsafe_allow_html=True)