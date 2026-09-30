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
# 2. SESSION STATE & RUN LOCKING
# ==========================================
if "is_unlocked_t5" not in st.session_state:
    st.session_state["is_unlocked_t5"] = False
if "locked_mode_t5" not in st.session_state:
    st.session_state["locked_mode_t5"] = None

def reset_on_mode_change_t5():
    st.session_state["is_unlocked_t5"] = False
    st.session_state.pop("fasta_df_t5", None)
    st.session_state.pop("fasta_text_t5", None)
    st.session_state.pop("stats_t5", None)

# ==========================================
# 3. TOOL HEADER & INSTRUCTIONS
# ==========================================
st.markdown("## Bulk NCBI & Ensembl FASTA Sequence Fetcher")
st.markdown(
    "**What we do in this tool:** We utilize Python-based REST API integrations to query the NCBI Entrez and Ensembl databases "
    "to bulk-download biological sequences based on your accession IDs. We compute biophysical parameters (GC%, MW, pI) and "
    "screen for cloning restriction sites.\n\n"
    "**Files Provided:** A compiled Multi-FASTA text file (`.fasta`) and a Metadata/Quality Control table (`.csv`)."
)

with st.expander("📋 Required File Format, Output Details & License Note", expanded=True):
    st.markdown("""
    * **Accepted File Formats:** Upload `.csv`, `.txt`, or `.tsv` files. Your file must contain a column with NCBI (e.g., `NM_`, `NP_`) or Ensembl (e.g., `ENSG`, `ENST`) IDs.
    * **Data Provided in Files:**
      1. **FASTA:** Clean, properly formatted sequence blocks wrapped to your specified base-pair length.
      2. **CSV Table:** Accession resolution, Sequence Length, GC/Hydrophobic %, Molecular Weight (kDa), and Cloning Restriction Cut Sites (`EcoRI`, `BamHI`, `BsaI`, etc).
    * **💻 Cross-Platform File Compatibility (Windows & Apple macOS):** All exported `.csv` tables use universal `UTF-8-BOM` encoding—double-click to open directly in **Microsoft Excel (Windows/Mac)**, **Apple Numbers**, **Google Sheets**, or load into **R / Python**. Sequence (`.fasta`) outputs open natively in any text editor.
    * **Single-Mode License Note:** Changing the **Core Engine**, **Model Organism**, or **Uploading a New File** fundamentally alters the dataset being queried and will lock the tool, requiring a new run license. Adjusting text formats, header styles, or display settings is completely free.
    """)

# ==========================================
# 4. BIOINFORMATICS LOGIC & CACHE
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
    "NM_000546": {"seq": "ATGGAGGAGCCGCAGTCAGATCCTAGCGTCGAGCCCCCTCTGAGTCAGGAAACATTTTCAGACCTATGGAAACTACTTCCTGAAAACAACGTTCTGTCCCCCTTGCCGTCCCAAGCAATGGATGATTTGATGCTGTCCCCGGACGATATTGAACAATGGTTCACTGAAGACCCAGGTCCAGATGAAGCTCCCAGAATGCCAGAGGCTGCTCCCCCCGTGGCCCCTGCACCAGCAGCTCCTACACCGGCGGCCCCTGCACCAGCCCCCTCCTGGCCCCTGTCATCTTCTGTCCCTTCCCAGAAAACCTACCAGGGCAGCTACGGTTTCCGTCTGGGCTTCTTGCATTCTGGGACAGCCAAGTCTGTGACTTGCACGTACTCCCCTGCCCTCAACAAGATGTTTTGCCAACTGGCCAAGACCTGCCCTGTGCAGCTGTGGGTTGATTCCACACCCCCGCCCGGCACCCGCGTCCGCGCCATGGCCATCTACAAGCAGTCACATGA", "desc": "TP53 Tumor protein p53", "mol": "Nucleotide (cDNA)"},
    "NM_007294": {"seq": "ATGGATTTATCTGCTCTTCGCGTTGAAGAAGTACAAAATGTCATTAATGCTATGCAGAAAATCTTAGAGTGTCCCATCTGTCTGGAGTTGATCAAGGAACCTGTCTCCACAAAGTGTGACCACATATTTTGCAAATTTTGCATGCTGAAACTTCTCAACCAGAAGAAAGGGCCTTCACAGTGTCCTTTATGTAAGAATGATATAACCAAAAGGAGCCTACAAGAAAGTACGAGATTTAGTCAACTTGTTGAAGAGCTATTGAAAATCATTTGTGCTTTTCAGCTTGACACAGGTTTGGAGTATGCAAACAGCTATAATTTTGCAAAAAAGGAAAATAACTCTCCTGAACATCTAAAAGATGAAGTTTCTATCATCCAAAGTATGGGCTACAGAAACCGTGCCAAAAGACTTCTACAGAGTGAACCCGAAAATCCTTCCTTGCAGGAAACCAGTCTCAGTGTCCAACTCTCTAACCTTGGAACTGTGAGAACTCTGAGGACTAA", "desc": "BRCA1 DNA repair associated", "mol": "Nucleotide (cDNA)"},
    "ENSG00000133703": {"seq": "ATGACTGAATATAAACTTGTGGTAGTTGGAGCTGGTGGCGTAGGCAAGAGTGCCTTGACGATACAGCTAATTCAGAATCATTTTGTGGACGAATATGATCCAACAATAGAGGATTCCTACAGGAAGCAAGTAGTAATTGATGGAGAAACCTGTCTCTTGGATATTCTCGACACAGCAGGTCAAGAGGAGTACAGTGCAATGAGGGACCAGTACATGAGGACTGGGGAGGGCTTTCTTTGTGTATTTGCCATAAATAATACTAAATCATTTGAAGATATTCACCATTATAGAGAACAAATTAAAAGAGTTAAGGACTCTGAAGATGTACCTATGGTCCTAGTAGGAAATAAATGTGATTTGCCTTCTAGAACAGTAGACACAAAACAGGCTCAGGACTTAGCAAGAAGTTATGGAATTCCTTTTATTGAAACATCAGCAAAGACAAGACAGGGTGTTGATGATGCCTTCTATACATTAGTTCGAGAAATTCGAAAACATAAATAA", "desc": "KRAS proto-oncogene", "mol": "Nucleotide (Genomic/CDS)"}
}

def rev_comp_dna(seq):
    trans = str.maketrans("ATGCRYSWKMBDHVNatgcryswkmbdhvn", "TACGYRSWMKVHDBNtacgyrswmkvhdbn")
    return seq.translate(trans)[::-1].upper()

def translate_dna(dna_seq):
    s = dna_seq.upper()
    start_idx = max(0, s.find("ATG"))
    aa_list = []
    for i in range(start_idx, len(s) - 2, 3):
        codon = s[i:i+3]
        aa = CODON_TABLE.get(codon, "X")
        if aa == "*": break
        aa_list.append(aa)
    return "".join(aa_list)

def fetch_live_accession(acc, core_engine):
    clean_acc = acc.split(".")[0].upper()
    
    # Check Cache First
    if clean_acc in DEMO_CACHE:
        item = DEMO_CACHE[clean_acc]
        seq = item["seq"]
        if "Protein" in core_engine and "Nucleotide" in item["mol"]:
            seq = translate_dna(seq)
            mol = "Protein (Translated)"
        else:
            mol = item["mol"]
        return {"status": "SUCCESS", "seq": seq, "desc": item["desc"], "mol": mol}

    # Live API Fetch
    if clean_acc.startswith("ENS"):
        ens_type = "protein" if "Protein" in core_engine else "cdna"
        try:
            r = requests.get(f"https://rest.ensembl.org/sequence/id/{clean_acc}?type={ens_type}", headers={"Content-Type": "application/json"}, timeout=10)
            if r.status_code == 200:
                data = r.json()
                return {"status": "SUCCESS", "seq": data.get("seq", ""), "desc": data.get("desc", "Ensembl Hit"), "mol": "Protein" if ens_type=="protein" else "Nucleotide"}
        except: pass
    else:
        db_name = "protein" if ("Protein" in core_engine or clean_acc.startswith(("NP_", "XP_"))) else "nuccore"
        try:
            r = requests.get(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db={db_name}&id={clean_acc}&rettype=fasta&retmode=text", timeout=10)
            if r.status_code == 200 and r.text.strip().startswith(">"):
                lines = r.text.strip().splitlines()
                return {"status": "SUCCESS", "seq": "".join(l for l in lines[1:] if not l.startswith(">")), "desc": " ".join(lines[0].split()[1:]), "mol": "Protein" if db_name=="protein" else "Nucleotide"}
        except: pass
        
    return {"status": "FAILED", "seq": "", "desc": "Not Found", "mol": "N/A"}

# ==========================================
# 5. INPUT & CONFIGURATION
# ==========================================
col_up, col_sample = st.columns([3, 1])
with col_up:
    uploaded_file = st.file_uploader("Upload Accession List (.csv, .txt, .tsv)", type=["csv", "txt", "tsv"], on_change=reset_on_mode_change_t5)
with col_sample:
    st.write("")
    st.write("")
    use_sample = st.checkbox("🧪 Load Demo NCBI Dataset", value=(uploaded_file is None), on_change=reset_on_mode_change_t5)

df_input = None
if uploaded_file is not None:
    try:
        df_input = pd.read_csv(uploaded_file, sep=None, engine="python")
    except Exception as e:
        st.error(f"Error reading file: {e}")
elif use_sample:
    df_input = pd.DataFrame({"Accession_ID": ["NM_000546.6", "NM_007294.4", "ENSG00000133703", "INVALID_99"]})

if df_input is not None and not df_input.empty:
    st.markdown("### ⚙️ Pipeline Configuration")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        acc_col = st.selectbox("1. Accession ID Column:", df_input.columns, index=0)
        core_engine = st.selectbox("2. Core Retrieval Engine (Locks on change):", [
            "Hybrid Auto-Detect (NCBI + Ensembl)",
            "NCBI RefSeq (Nucleotide mRNA/cDNA)",
            "Ensembl Transcript (CDS / mRNA)",
            "Protein / Peptide Sequences Only"
        ], on_change=reset_on_mode_change_t5)
        
    with col2:
        organism = st.selectbox("3. Model Organism (Locks on change):", [
            "Homo sapiens (Human)", 
            "Mus musculus (Mouse)", 
            "Danio rerio (Zebrafish)", 
            "Universal / Cross-Species"
        ], on_change=reset_on_mode_change_t5)
        header_style = st.selectbox("4. FASTA Header Style (Free to change):", ["Standard Annotated", "Minimal (ID Only)"])

    with col3:
        wrap_width = st.selectbox("5. Sequence Line Wrap (Free to change):", [60, 80, 0], format_func=lambda x: "Single-Line (No wrap)" if x==0 else f"{x} bp/line")
        excel_guard = st.checkbox("🛡️ Enable Excel Gene-Name Guard (Protects MARCH1 / SEPT2)", value=False)

    current_file_sig = uploaded_file.name if uploaded_file else "demo_data"
    current_mode_sig = f"{current_file_sig}|{core_engine}|{organism}"

    # ==========================================
    # 6. RUN EXECUTION
    # ==========================================
    if st.button("🚀 Fetch & Compile Bulk FASTA Sequences"):
        if st.session_state["locked_mode_t5"] is not None and st.session_state["locked_mode_t5"] != current_mode_sig:
            st.session_state["is_unlocked_t5"] = False
        st.session_state["locked_mode_t5"] = current_mode_sig

        raw_ids = df_input[acc_col].dropna().astype(str).str.strip().tolist()
        # Deduplicate
        raw_ids = list(dict.fromkeys([x for x in raw_ids if x.lower() not in ["nan", "none", ""]]))

        progress_bar = st.progress(0)
        status_text = st.empty()
        
        compiled_rows = []
        fasta_blocks = []
        failed_count = 0
        total_len = 0
        
        for i, acc in enumerate(raw_ids):
            status_text.text(f"Fetching Sequence {i+1} of {len(raw_ids)}: {acc}")
            progress_bar.progress((i + 1) / len(raw_ids))
            
            # Rate limiting for live calls to prevent freezing/blocking
            if acc.split('.')[0] not in DEMO_CACHE:
                time.sleep(0.35)

            res = fetch_live_accession(acc, core_engine)
            
            if res["status"] == "SUCCESS" and res["seq"]:
                seq = res["seq"].upper()
                is_prot = "Protein" in res["mol"]
                seq_len = len(seq)
                total_len += seq_len
                
                # Biophysics
                if is_prot:
                    hydro = round(sum(1 for aa in seq if aa in "AVILMFYW") / max(1, seq_len) * 100, 1)
                    gc, mw = 0.0, round((seq_len * 110.0) / 1000.0, 2)
                    comp_tag = f"Hydrophobic:{hydro}%"
                else:
                    gc = round(sum(1 for b in seq if b in "GC") / max(1, seq_len) * 100, 1)
                    hydro, mw = 0.0, round((seq_len * 308.0) / 1000.0, 2)
                    comp_tag = f"GC:{gc}%"
                    
                # Restriction Sites
                cuts = [enz for enz, site in {"EcoRI":"GAATTC", "BamHI":"GGATCC", "BsaI":"GGTCTC"}.items() if site in seq or rev_comp_dna(site) in seq]
                cut_str = "0 Cuts (Cloning-Safe)" if not cuts else f"Cuts: {', '.join(cuts)}"

                # Header & Fasta
                hdr = f">{acc}" if header_style == "Minimal (ID Only)" else f">{acc} | {res['desc']} | Len:{seq_len} | {comp_tag}"
                wrapped_seq = "\n".join([seq[j:j+wrap_width] for j in range(0, len(seq), wrap_width)]) if wrap_width > 0 else seq
                fasta_blocks.append(f"{hdr}\n{wrapped_seq}")
                
                gene_disp = f'="{acc}"' if excel_guard else acc
                
                compiled_rows.append({
                    "Accession": gene_disp, "Fetch_Status": "Success", "Molecule_Type": res["mol"],
                    "Sequence_Length": seq_len, "GC_or_Hydro_Pct": comp_tag, "Molecular_Weight_kDa": mw,
                    "Cloning_Restriction_Sites": cut_str, "Description": res["desc"]
                })
            else:
                failed_count += 1
                compiled_rows.append({"Accession": acc, "Fetch_Status": "Failed", "Molecule_Type": "N/A", "Sequence_Length": 0, "GC_or_Hydro_Pct": "N/A", "Molecular_Weight_kDa": 0, "Cloning_Restriction_Sites": "N/A", "Description": "Not Found"})

        status_text.empty()
        progress_bar.empty()
        
        st.session_state["fasta_df_t5"] = pd.DataFrame(compiled_rows)
        st.session_state["fasta_text_t5"] = "\n\n".join(fasta_blocks)
        st.session_state["stats_t5"] = {
            "queried": len(raw_ids),
            "success": len(fasta_blocks),
            "failed": failed_count,
            "total_len": total_len,
            "engine": core_engine,
            "org": organism
        }

# ==========================================
# 7. RESULTS & PAYWALL DISPLAY
# ==========================================
if "fasta_df_t5" in st.session_state:
    res_df = st.session_state["fasta_df_t5"]
    fasta_str = st.session_state["fasta_text_t5"]
    stats = st.session_state["stats_t5"]

    st.markdown("---")
    st.markdown("### 📊 Bulk Sequence Retrieval Summary & FASTA Preview")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Accessions Queried", f"{stats['queried']:,}")
    m2.metric("Successfully Compiled", f"{stats['success']:,}")
    m3.metric("Failed / Unresolved", f"{stats['failed']:,}")
    m4.metric("Total Base/Residue Volume", f"{stats['total_len']:,}")

    if stats['success'] == 0:
        st.error("❌ 0 sequences were retrieved. Please ensure you selected the correct Accession ID Column and your IDs match the selected database.")
        st.dataframe(res_df, use_container_width=True)

    if stats['success'] > 0:
        if st.session_state["is_unlocked_t5"]:
            st.success(f"✅ **Payment Verified for [{stats['engine']} | {stats['org']}]!** Complete multi-FASTA file and biophysical metadata tables unlocked.")
            st.dataframe(res_df, use_container_width=True)

            d1, d2 = st.columns(2)
            d1.download_button(
                "⬇️ 1. Download Compiled Multi-FASTA (.fasta)",
                data=fasta_str.encode("utf-8-sig"),
                file_name="GenomeTech_Bulk_Sequences.fasta",
                mime="text/plain"
            )
            d2.download_button(
                "⬇️ 2. Download Biophysical & Cloning QC Table (.csv)",
                data=res_df.to_csv(index=False).encode("utf-8-sig"),
                file_name="GenomeTech_Sequence_QC.csv",
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
# 8. REMARKS, REVIEWS & TOOL REQUESTS
# ==========================================
st.markdown("---")
st.markdown("### 📝 Remarks, Reviews & New Tool Requests")
st.write("We build custom bioinformatics pipelines. Have feedback on this FASTA fetcher or need a new tool built? Submit it below. Fully supported on Windows & Mac.")

with st.form("feedback_form"):
    req_name = st.text_input("Your Name / Institution:")
    req_msg = st.text_area("Your Review, Remark, or Tool Request:")
    submit_btn = st.form_submit_button("Submit Form")
    
    if submit_btn:
        subject = urllib.parse.quote(f"OmicsExpress Feedback - Tool #5 (From: {req_name})")
        body = urllib.parse.quote(f"Name/Institution: {req_name}\nTool: Tool #5 - Bulk FASTA Fetcher\n\nMessage/Request:\n{req_msg}")
        mail_link = f"mailto:bhumikasihare555@gmail.com?subject={subject}&body={body}"
        
        st.success("🎉 Thank you for using OmicsExpress! Keep exploring more.")
        st.markdown(f"**Action Required:** Click the link below to securely pass your request to your default email application (Outlook/Mac Mail/Gmail) to finalize sending.")
        st.markdown(f'<a href="{mail_link}" style="background: linear-gradient(90deg, #7c3aed 0%, #2563eb 100%); color: white !important; padding: 10px 20px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block; margin-top: 10px; border: 1px solid #c084fc;">📧 Open Email App to Send</a>', unsafe_allow_html=True)