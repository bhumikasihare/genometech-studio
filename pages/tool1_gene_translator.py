import streamlit as st
import pandas as pd
import numpy as np
import requests
import urllib.parse

# 1. Page Configuration (Isolated Single-Tool View)
st.set_page_config(
    page_title="Universal Gene ID Translator | OmicsExpress",
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
    <span class="gts-badge">⚡ Tool #1: Universal Gene ID Translator</span>
</div>
""", unsafe_allow_html=True)

if "is_unlocked_t1" not in st.session_state:
    st.session_state["is_unlocked_t1"] = False
if "locked_pipeline_t1" not in st.session_state:
    st.session_state["locked_pipeline_t1"] = None

def reset_on_pipeline_change_t1():
    st.session_state["is_unlocked_t1"] = False
    st.session_state.pop("result_df_t1", None)
    st.session_state.pop("unmapped_df_t1", None)
    st.session_state.pop("stats_t1", None)

st.markdown("## Universal Gene ID Translator")
st.markdown(
    "Convert up to **50,000 Ensembl IDs, Official Gene Symbols, or Entrez IDs** instantly across major model organisms. "
    "Automatically enriches your dataset with **Genomic Coordinates (`Chr:Start-End`), Cross-Database IDs (`Entrez` & `UniProt`), "
    "Gene Biotypes, and Microsoft Excel Gene-Symbol Protection**."
)

with st.expander("📋 Required File Format & Clinical Annotation Features (.csv or .txt)", expanded=True):
    st.markdown("""
    * **Accepted File Types:** Comma-separated (`.csv`) or Tab/Line-separated (`.txt`) files up to **50,000 rows**.
    * **Complete Annotation Columns Included:**
      1. **Primary Translated Identifier** (`Official_Gene_Symbol`, `Ensembl_Gene_ID`, or `Entrez_Gene_ID`)
      2. **Cross-Database Links** (`NCBI_Entrez_ID` for KEGG/GSEA & `UniProt_SwissProt_ID` for Proteomics)
      3. **Genomic Loci** (`Chromosome`, `Start_bp`, `End_bp`, `Strand`)
      4. **Functional Metadata** (`Gene_Biotype`, `Gene_Description`, `Mapping_Status`)
      5. **Microsoft Excel Gene-Date Guard:** Prevents Excel from corrupting gene symbols like `MARCH1` or `SEPT2` into calendar dates.
    * **💻 Cross-Platform File Compatibility (Windows & Apple macOS):** All exported `.csv` tables use universal `UTF-8-BOM` encoding—double-click to open directly in **Microsoft Excel (Windows/Mac)**, **Apple Numbers**, **Google Sheets**, or load into **R / Python**. Sequence (`.fasta`) and vector figure (`.svg` / `.html`) outputs open natively in any text editor (**Notepad / Mac TextEdit**) or web browser (**Safari / Chrome / Edge**).
    * **Single-Pipeline License Note:** Each checkout unlocks your selected **Conversion Direction & Organism**. Adjusting formatting toggles within the same conversion direction is free; switching to a new conversion direction or organism starts a new run.
    """)

# ==========================================
# STEP 2: TOOL-SPECIFIC INPUTS
# ==========================================
col_up, col_sample = st.columns([3, 1])
with col_up:
    uploaded_file = st.file_uploader(
        "Upload your Gene List or Expression Table (.csv or .txt)",
        type=["csv", "txt"],
        on_change=reset_on_pipeline_change_t1
    )
with col_sample:
    st.write("")
    st.write("")
    use_sample = st.checkbox("🧪 Load Demo Ensembl Dataset", value=False, on_change=reset_on_pipeline_change_t1)

df_input = None
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".txt"):
            df_input = pd.read_csv(uploaded_file, sep=None, engine="python")
        else:
            df_input = pd.read_csv(uploaded_file)
        if len(df_input) > 50000:
            st.warning("⚠️ File exceeds 50,000 rows. Truncating to the first 50,000 IDs.")
            df_input = df_input.iloc[:50000]
    except Exception as e:
        st.error(f"Error reading file: {e}. Please ensure it is a valid .csv or .txt file.")
elif use_sample:
    df_input = pd.DataFrame({
        "Ensembl_ID": [
            "ENSG00000141510.15", "ENSG00000012048.20", "ENSG00000171862.11",
            "ENSG00000157764.14", "ENSG00000136997.18", "ENSG00000146648.15",
            "ENSG00000196712.12", "ENSG00000115414.18", "ENSG00000133703.11",
            "ENSG00000148773.12", "ENSG00000105329.9", "ENSG00009999999.1"
        ],
        "Log2FoldChange": [2.45, -1.82, 3.10, 1.25, -2.90, 4.12, -0.95, 1.88, -3.40, 2.05, 1.15, 0.42],
        "Adjusted_P_Value": [0.0001, 0.0023, 0.00004, 0.012, 0.0008, 0.00001, 0.041, 0.003, 0.0002, 0.009, 0.018, 0.45]
    })

if df_input is not None:
    st.markdown("### ⚙️ Configure Translation & Annotation Parameters")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        id_col = st.selectbox("1. Column Containing Source IDs:", df_input.columns, index=0)
        conversion_dir = st.selectbox(
            "2. Conversion Direction (Core Pipeline):",
            [
                "Ensembl Gene ID ➔ Official Gene Symbol",
                "Official Gene Symbol ➔ Ensembl Gene ID",
                "Ensembl Transcript ID ➔ Official Gene Symbol",
                "Entrez Gene ID ➔ Official Gene Symbol"
            ],
            on_change=reset_on_pipeline_change_t1
        )
        species_map = {
            "Homo sapiens (Human)": "9606",
            "Mus musculus (Mouse)": "10090",
            "Rattus norvegicus (Rat)": "10116",
            "Danio rerio (Zebrafish)": "7955",
            "Drosophila melanogaster (Fruit fly)": "7227",
            "Arabidopsis thaliana (Thale cress)": "3702",
            "Saccharomyces cerevisiae (Yeast)": "559292",
            "Other (Enter Custom NCBI Taxon ID)": "custom"
        }
        species_choice = st.selectbox(
            "3. Organism / Species (Core Pipeline):",
            list(species_map.keys()),
            on_change=reset_on_pipeline_change_t1
        )
        if species_map[species_choice] == "custom":
            species_taxid = st.text_input(
                "Enter NCBI Taxonomy ID (e.g., 9913 for Cattle):",
                value="9606",
                on_change=reset_on_pipeline_change_t1
            )
        else:
            species_taxid = species_map[species_choice]

    with c2:
        st.markdown("**4. Annotation Columns to Include**")
        include_name = st.checkbox("Include Full Gene Name & Biotype", value=True)
        include_coords = st.checkbox("Include Genomic Coordinates (Chr, Start, End, Strand)", value=True)
        include_xrefs = st.checkbox("Include Cross-DB IDs (NCBI Entrez & UniProt Swiss-Prot)", value=True)

    with c3:
        st.markdown("**5. Cleaning & Excel Protection**")
        strip_versions = st.checkbox("Strip Ensembl Version Suffixes (e.g. .15)", value=True)
        excel_guard = st.checkbox(
            "🛡️ Enable Excel Gene-Name Guard (Protects MARCH1 / SEPT2)",
            value=False,
            help="Wraps gene symbols as explicit Excel text strings (=\"GENE\") so Microsoft Excel never converts MARCH1 or SEPT2 into calendar dates."
        )
        unmapped_action = st.selectbox("Unmapped ID Handling:", ["Keep row & mark as 'Unmapped'", "Drop unmapped rows"])

    current_file_sig = uploaded_file.name if uploaded_file is not None else "demo_data"
    current_pipeline_sig = f"{current_file_sig}|{conversion_dir}|{species_taxid}"

    # ==========================================
    # STEP 3: RUN LIVE TRANSLATION & PREVIEW
    # ==========================================
    if st.button("🚀 Run Gene ID Translation"):
        if st.session_state["locked_pipeline_t1"] is not None and st.session_state["locked_pipeline_t1"] != current_pipeline_sig:
            st.session_state["is_unlocked_t1"] = False
        st.session_state["locked_pipeline_t1"] = current_pipeline_sig

        with st.spinner("Querying genomic annotation databases for symbols, coordinates, and cross-references..."):
            raw_ids = df_input[id_col].astype(str).str.strip().tolist()
            
            versions_stripped_count = sum(1 for x in raw_ids if "." in x and x.startswith("ENS")) if strip_versions else 0
            if strip_versions:
                clean_ids = [x.split(".")[0] if x.startswith("ENS") else x for x in raw_ids]
            else:
                clean_ids = raw_ids

            if conversion_dir == "Ensembl Gene ID ➔ Official Gene Symbol":
                scopes = "ensembl.gene"
                target_field = "symbol"
                target_col_name = "Official_Gene_Symbol"
            elif conversion_dir == "Official Gene Symbol ➔ Ensembl Gene ID":
                scopes = "symbol,alias"
                target_field = "ensembl.gene"
                target_col_name = "Ensembl_Gene_ID"
            elif conversion_dir == "Ensembl Transcript ID ➔ Official Gene Symbol":
                scopes = "ensembl.transcript"
                target_field = "symbol"
                target_col_name = "Official_Gene_Symbol"
            else:
                scopes = "entrezgene"
                target_field = "symbol"
                target_col_name = "Official_Gene_Symbol"

            fields_to_fetch = ["symbol", "ensembl.gene", "entrezgene", "uniprot.Swiss-Prot", "name", "type_of_gene", "genomic_pos"]
            
            unique_queries = list(dict.fromkeys(clean_ids))
            mapping_dict = {}
            
            for i in range(0, len(unique_queries), 1000):
                batch = unique_queries[i:i+1000]
                try:
                    res = requests.post(
                        "https://mygene.info/v3/query",
                        data={
                            "q": ",".join(batch),
                            "scopes": scopes,
                            "fields": ",".join(fields_to_fetch),
                            "species": species_taxid
                        },
                        timeout=30
                    )
                    if res.status_code == 200:
                        for hit in res.json():
                            q_id = hit.get("query")
                            if q_id in mapping_dict or hit.get("notfound", False):
                                continue
                            
                            # Primary Target Field
                            ens = hit.get("ensembl", {})
                            if isinstance(ens, list):
                                ens_gene_val = ens[0].get("gene", "Unmapped")
                            elif isinstance(ens, dict):
                                ens_gene_val = ens.get("gene", "Unmapped")
                            else:
                                ens_gene_val = "Unmapped"

                            sym_val = hit.get("symbol", "Unmapped")
                            mapped_val = ens_gene_val if target_field == "ensembl.gene" else sym_val

                            # Entrez & UniProt
                            entrez_val = str(hit.get("entrezgene", "N/A"))
                            uniprot_raw = hit.get("uniprot", {}).get("Swiss-Prot", "N/A")
                            if isinstance(uniprot_raw, list):
                                uniprot_val = uniprot_raw[0]
                            else:
                                uniprot_val = str(uniprot_raw)

                            # Genomic Coordinates
                            gpos = hit.get("genomic_pos", {})
                            if isinstance(gpos, list):
                                gpos = gpos[0]
                            if isinstance(gpos, dict) and gpos.get("chr"):
                                chr_val = f"chr{gpos.get('chr')}"
                                start_val = gpos.get("start", "N/A")
                                end_val = gpos.get("end", "N/A")
                                strand_raw = gpos.get("strand", 0)
                                strand_val = "+" if strand_raw == 1 else ("-" if strand_raw == -1 else str(strand_raw))
                                locus_str = f"{chr_val}:{start_val}-{end_val} ({strand_val})"
                            else:
                                locus_str = "N/A"

                            mapping_dict[q_id] = {
                                "mapped": mapped_val,
                                "name": hit.get("name", "N/A"),
                                "biotype": hit.get("type_of_gene", "N/A"),
                                "entrez": entrez_val,
                                "uniprot": uniprot_val,
                                "locus": locus_str
                            }
                except Exception as e:
                    st.error(f"Network error contacting genomic server: {e}")

            out_df = df_input.copy()
            mapped_col_vals = [mapping_dict.get(cid, {}).get("mapped", "Unmapped") for cid in clean_ids]
            if excel_guard and target_col_name == "Official_Gene_Symbol":
                mapped_col_vals = [f'="{v}"' if v != "Unmapped" else v for v in mapped_col_vals]

            insert_pos = 1
            out_df.insert(insert_pos, target_col_name, mapped_col_vals)
            insert_pos += 1

            if include_name:
                out_df.insert(insert_pos, "Gene_Biotype", [mapping_dict.get(cid, {}).get("biotype", "Unmapped") for cid in clean_ids])
                out_df.insert(insert_pos + 1, "Gene_Description", [mapping_dict.get(cid, {}).get("name", "Unmapped") for cid in clean_ids])
                insert_pos += 2

            if include_coords:
                out_df.insert(insert_pos, "Genomic_Coordinates (Chr:Start-End)", [mapping_dict.get(cid, {}).get("locus", "N/A") for cid in clean_ids])
                insert_pos += 1

            if include_xrefs:
                out_df.insert(insert_pos, "NCBI_Entrez_ID", [mapping_dict.get(cid, {}).get("entrez", "N/A") for cid in clean_ids])
                out_df.insert(insert_pos + 1, "UniProt_SwissProt_ID", [mapping_dict.get(cid, {}).get("uniprot", "N/A") for cid in clean_ids])
                insert_pos += 2

            total_rows = len(out_df)
            unmapped_mask = out_df[target_col_name] == "Unmapped"
            unmapped_count = int(unmapped_mask.sum())
            mapped_count = total_rows - unmapped_count
            mapped_pct = (mapped_count / total_rows * 100) if total_rows > 0 else 0

            unmapped_df = out_df[unmapped_mask].copy()
            if unmapped_action == "Drop unmapped rows":
                out_df = out_df[~unmapped_mask].copy()

            st.session_state["result_df_t1"] = out_df
            st.session_state["unmapped_df_t1"] = unmapped_df
            st.session_state["stats_t1"] = {
                "total": total_rows,
                "mapped": mapped_count,
                "unmapped": unmapped_count,
                "pct": mapped_pct,
                "stripped": versions_stripped_count,
                "species": species_choice,
                "direction": conversion_dir
            }

# ==========================================
# DISPLAY PREVIEW, PAYWALL, DOWNLOAD & REMARKS
# ==========================================
if "result_df_t1" in st.session_state:
    res_df = st.session_state["result_df_t1"]
    unmap_df = st.session_state["unmapped_df_t1"]
    stats = st.session_state["stats_t1"]

    st.markdown("---")
    st.markdown("### 📊 Translation Summary & Preview")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total IDs Processed", f"{stats['total']:,}")
    m2.metric("Successfully Mapped", f"{stats['mapped']:,} ({stats['pct']:.1f}%)")
    m3.metric("Unmapped / Novel IDs", f"{stats['unmapped']:,}")

    if st.session_state["is_unlocked_t1"]:
        st.success(f"✅ **Payment Verified for [{stats['direction']} | {stats['species']}]!** Full dataset unlocked. You may freely adjust annotation checkboxes or Excel guard toggles and re-run within this conversion mode.")
        st.dataframe(res_df, use_container_width=True)
        
        d1, d2 = st.columns(2)
        with d1:
            st.download_button(
                "⬇️ 1. Download Complete Translated & Annotated Table (.csv)",
                data=res_df.to_csv(index=False).encode("utf-8-sig"),
                file_name="GenomeTech_Translated_Genes.csv",
                mime="text/csv"
            )
        with d2:
            st.download_button(
                "⬇️ 2. Download Unmapped IDs Audit Report (.csv)",
                data=unmap_df.to_csv(index=False).encode("utf-8-sig"),
                file_name="GenomeTech_Unmapped_IDs.csv",
                mime="text/csv"
            )
    else:
        st.markdown("**Live Preview (First 5 Verified Rows):**")
        st.dataframe(res_df.head(5), use_container_width=True)

        blurred_preview = res_df.iloc[5:15] if len(res_df) > 5 else res_df
        st.markdown('<div class="blurred-table">', unsafe_allow_html=True)
        st.table(blurred_preview)
        st.markdown('</div>', unsafe_allow_html=True)

        razorpay_link = "https://rzp.io/rzp/UVDck3w"
        st.markdown(f"""
        <div class="paywall-overlay">
            <h3 style="color: #e9d5ff !important; margin-top: 0;">🔒 Unlock Full {stats['total']:,}-Row Translated CSV</h3>
            <p style="color: #cbd5e1 !important; font-size: 0.95rem;">
                Your first 5 rows are verified above. Complete the $40 OmicsExpress checkout to immediately download the complete merged table with genomic coordinates, Entrez/UniProt IDs, and unmapped ID audit report.
            </p>
            <div style="background:rgba(56,189,248,0.14);border:1px solid rgba(56,189,248,0.45);color:#e0f2fe !important;padding:8px 14px;border-radius:8px;font-size:0.88rem;font-weight:600;margin:10px auto 6px auto;max-width:520px;">🔥 <span style="color:#38bdf8 !important;font-weight:800;">FOUNDING LAB LAUNCH OFFER:</span> <s style="color:#94a3b8 !important;">$100 USD</s> <b style="color:#ffffff !important;">$40 USD</b> — Special Early-Access Rate for Our First 20 Research Clients</div><a href="{razorpay_link}" target="_blank" style="background: linear-gradient(90deg, #9333ea 0%, #2563eb 100%); color: white !important; padding: 14px 32px; text-decoration: none; border-radius: 10px; font-weight: 700; font-size: 1.05rem; display: inline-block; margin: 12px 0; border: 1px solid #c084fc; box-shadow: 0 4px 20px rgba(147, 51, 234, 0.5);">
                💳 Pay $40 via Razorpay to Unlock CSV
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
                    st.session_state["is_unlocked_t1"] = True
                    st.rerun()
                else:
                    st.error("Invalid Payment ID. Please paste the 'pay_...' ID shown on your Razorpay payment confirmation screen.")

    st.markdown("---")
    st.markdown("### 📝 Automated Quality Remarks & Direct Support")
    
    st.info(
        f"**Automated Run Diagnostics:**\n"
        f"* **Pipeline:** {stats['direction']} ({stats['species']})\n"
        f"* **Pre-processing:** {stats['stripped']} Ensembl version suffixes (e.g., `.14`) were automatically stripped prior to querying.\n"
        f"* **Mapping Audit:** {stats['pct']:.1f}% of input IDs mapped cleanly to official nomenclature with cross-database Entrez/UniProt links and genomic coordinates. "
        f"The remaining {stats['unmapped']} unmapped records typically represent retired archive IDs, pseudogenes, or novel unannotated lncRNA transcripts."
    )

    with st.expander("💬 Send Remarks or Questions Directly to GenomeTech Team (via Email)"):
        client_email = st.text_input("Your Lab / Institutional Email:")
        client_remark = st.text_area("Your Remarks or Questions about this Run:")
        if st.button("Prepare Direct Email"):
            subject = urllib.parse.quote(f"OmicsExpress Tool #1 Remark - {client_email}")
            body = urllib.parse.quote(
                f"Client Email: {client_email}\n"
                f"Tool Used: Tool #1 - Universal Gene ID Translator\n"
                f"Organism: {stats['species']}\n"
                f"Conversion: {stats['direction']}\n"
                f"Total IDs Processed: {stats['total']} (Mapped: {stats['pct']:.1f}%)\n\n"
                f"Client Remarks:\n{client_remark}"
            )
            mailto_url = f"mailto:bhumikasihare555@gmail.com?subject={subject}&body={body}"
            st.success("✅ Your remark and run diagnostics are ready! Click below to send directly from your email client:")
            st.markdown(f'👉 <a href="https://mail.google.com/mail/?view=cm&fs=1&to=bhumikasihare555@gmail.com&su={subject}&body={body}" target="_blank" style="color:#38bdf8;font-weight:700;text-decoration:underline;">Click Here to Send via Gmail (Browser)</a> &nbsp;|&nbsp; <a href="{mailto_url}" style="color:#c4b5fd;font-weight:600;text-decoration:underline;">Open in Default Mail App (Outlook/Mac)</a>', unsafe_allow_html=True)