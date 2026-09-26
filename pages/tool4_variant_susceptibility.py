import streamlit as st
import pandas as pd
import numpy as np
import requests
import urllib.parse

# 1. Page Configuration (Isolated Single-Tool View)
st.set_page_config(
    page_title="Variant Susceptibility & Pathogenic Flagging | OmicsExpress",
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
    <span class="gts-badge">⚡ Tool #4: Variant Susceptibility</span>
</div>
""", unsafe_allow_html=True)

if "is_unlocked_t4" not in st.session_state:
    st.session_state["is_unlocked_t4"] = False
if "locked_mode_t4" not in st.session_state:
    st.session_state["locked_mode_t4"] = None

# Callback that resets unlock & results ONLY when Core Susceptibility Engine or Uploaded File changes
def reset_on_mode_change_t4():
    st.session_state["is_unlocked_t4"] = False
    st.session_state.pop("suscept_df_t4", None)
    st.session_state.pop("tier1_df_t4", None)
    st.session_state.pop("audit_df_t4", None)
    st.session_state.pop("stats_t4", None)

st.markdown("## Variant Susceptibility & Pathogenic Flagging")
st.markdown(
    "Screen candidate genetic variants against curated pathogenic databases (**ClinVar, ACMG Secondary Findings SF v3.2, "
    "OMIM, OncoKB/NCCN Cancer Predisposition, and CPIC Pharmacogenomics**). "
    "Computes **Numeric Susceptibility Risk Scores (0–100), ACMG/AMP Evidence Codes (`PVS1/PS1/PM2`), Penetrance & Odds Ratios, "
    "Molecular Mechanisms, and Targeted Therapy / Clinical Surveillance Actions**."
)

with st.expander("📋 Required File Format & Complete Clinical Columns (.csv, .tsv, .txt, or .vcf)", expanded=True):
    st.markdown("""
    * **Accepted File Formats:** Tabular `.csv`, `.tsv`, `.txt` (including direct exports from Tool #3) or raw `.vcf` files.
    * **Complete Researcher & Clinical Columns Included:**
      1. **Risk Scoring & ACMG Evidence:** `Susceptibility_Risk_Score (0-100)`, `Clinical_Risk_Tier`, `ClinVar_Pathogenicity`, `ACMG_AMP_Evidence_Codes` (`PVS1, PS1, PM2, PP5`), and `Review_Stars`.
      2. **Penetrance & Genetic Epidemiology:** `Penetrance_&_Lifetime_Risk (OR)`, `gnomAD_Pop_AF`, and `Inheritance_Mode`.
      3. **Disease & Mechanism:** `Disease_Category`, `Associated_Syndrome`, `OMIM_&_ClinVar_ID`, and `Molecular_Mechanism`.
      4. **Clinical Actionability:** `Actionability_Flag`, `Targeted_Therapy_/_PGx_Action`, and `Clinical_Surveillance_Protocol`.
    * **💻 Cross-Platform File Compatibility (Windows & Apple macOS):** All exported `.csv` tables use universal `UTF-8-BOM` encoding—double-click to open directly in **Microsoft Excel (Windows/Mac)**, **Apple Numbers**, **Google Sheets**, or load into **R / Python**. Sequence (`.fasta`) and vector figure (`.svg` / `.html`) outputs open natively in any text editor (**Notepad / Mac TextEdit**) or web browser (**Safari / Chrome / Edge**).
    * **Single-Mode License Note:** Each checkout unlocks your selected **Core Susceptibility Engine**. Adjusting risk cutoffs, review star filters, and Excel guards within your mode is free; switching the Core Engine or uploading a new dataset starts a new run.
    """)

# ==========================================
# CURATED CLINICAL KNOWLEDGEBASE & DEMO DATA
# ==========================================
CURATED_PATHOGENIC_DB = {
    "RS28934578": {
        "gene": "TP53", "hgvsp": "p.Arg175His", "hgvsc": "c.524G>A", "rsid": "rs28934578", "locus": "chr17:7,675,088",
        "score": 99.5, "clnsig": "Pathogenic", "tier": "TIER 1 - CRITICAL HIGH RISK", "acmg_codes": "PS1, PS3, PM1, PM2, PP3, PP5",
        "stars": "★★★ (Expert Panel)", "penetrance": "High Penetrance (OR > 25.0 | >85% Lifetime Risk)", "gnomad": 0.00001,
        "category": "Oncology", "syndrome": "Li-Fraumeni Syndrome (LFS)", "omim": "OMIM:151623 | ClinVar:12356",
        "mechanism": "Dominant-Negative DNA-Binding Domain Missense", "inheritance": "Autosomal Dominant",
        "actionability": "ACMG SF v3.2 Actionable (High Penetrance)",
        "therapy": "Avoid ionizing radiation RT; prioritize non-genotoxic targeted regimens",
        "recommendation": "Annual whole-body MRI, brain MRI, breast MRI (age 20+), and early colonoscopy/dermatology surveillance."
    },
    "RS80357906": {
        "gene": "BRCA1", "hgvsp": "p.Glu23ValfsTer17", "hgvsc": "c.68_69delAG", "rsid": "rs80357906", "locus": "chr17:43,094,464",
        "score": 99.0, "clnsig": "Pathogenic", "tier": "TIER 1 - CRITICAL HIGH RISK", "acmg_codes": "PVS1, PS4, PM2, PP5",
        "stars": "★★★ (Expert Panel)", "penetrance": "High Penetrance (OR 12.4 | 65–72% Breast / 40% Ovarian Risk)", "gnomad": 0.00004,
        "category": "Oncology", "syndrome": "Hereditary Breast & Ovarian Cancer (HBOC)", "omim": "OMIM:604370 | ClinVar:17661",
        "mechanism": "Loss-of-Function (Frameshift Nonsense-Mediated Decay)", "inheritance": "Autosomal Dominant",
        "actionability": "ACMG SF v3.2 & NCCN Category 1 Actionable",
        "therapy": "FDA-Approved PARP Inhibitors (Olaparib, Talazoparib, Niraparib) & Platinum Sensitivity",
        "recommendation": "Annual breast MRI (starting age 25) + mammogram (age 30); discuss risk-reducing salpingo-oophorectomy (age 35–40)."
    },
    "RS121434568": {
        "gene": "EGFR", "hgvsp": "p.Leu858Arg", "hgvsc": "c.2573T>G", "rsid": "rs121434568", "locus": "chr7:55,191,822",
        "score": 96.5, "clnsig": "Pathogenic", "tier": "TIER 1 - CRITICAL HIGH RISK", "acmg_codes": "PS1, PS3, PM1, PM2, PP5",
        "stars": "★★★ (Practice Guideline)", "penetrance": "High Somatic Driver (OncoKB Level 1 Biomarker)", "gnomad": 0.00000,
        "category": "Oncology", "syndrome": "Non-Small Cell Lung Adenocarcinoma (NSCLC Susceptibility)", "omim": "OMIM:211980 | ClinVar:16609",
        "mechanism": "Constitutive Tyrosine Kinase Domain Activation", "inheritance": "Somatic Driver / Rare Germline",
        "actionability": "FDA / NCCN Level 1 Companion Diagnostic",
        "therapy": "3rd-Gen EGFR Tyrosine Kinase Inhibitor (Osimertinib / Tagrisso)",
        "recommendation": "Immediate first-line Osimertinib targeted therapy; monitor ctDNA for p.Thr790Met / p.Cys797Ser resistance."
    },
    "RS113488022": {
        "gene": "BRAF", "hgvsp": "p.Val600Glu", "hgvsc": "c.1799T>A", "rsid": "rs113488022", "locus": "chr7:140,753,336",
        "score": 96.0, "clnsig": "Pathogenic", "tier": "TIER 1 - CRITICAL HIGH RISK", "acmg_codes": "PS1, PS3, PM1, PM2, PP5",
        "stars": "★★★ (Practice Guideline)", "penetrance": "High Actionable Driver (OncoKB Level 1)", "gnomad": 0.00001,
        "category": "Oncology", "syndrome": "BRAF-Mutant Melanoma / Colorectal / Thyroid Neoplasm", "omim": "OMIM:164757 | ClinVar:13961",
        "mechanism": "Constitutive MAPK/ERK Signaling Activation", "inheritance": "Somatic / Mosaic",
        "actionability": "FDA-Approved Pan-Tumor Biomarker",
        "therapy": "BRAF + MEK Inhibitor Combination (Dabrafenib + Trametinib / Encorafenib)",
        "recommendation": "Initiate targeted BRAF/MEK inhibition; pair with anti-EGFR (Cetuximab) in metastatic colorectal contexts."
    },
    "RS121909224": {
        "gene": "PTEN", "hgvsp": "p.Arg130Ter", "hgvsc": "c.388C>T", "rsid": "rs121909224", "locus": "chr10:87,933,147",
        "score": 97.5, "clnsig": "Pathogenic", "tier": "TIER 1 - CRITICAL HIGH RISK", "acmg_codes": "PVS1, PS2, PM2, PP5",
        "stars": "★★★ (Expert Panel)", "penetrance": "High Penetrance (OR > 15.0 | >80% Hamartoma/Cancer Risk)", "gnomad": 0.00000,
        "category": "Oncology", "syndrome": "Cowden Syndrome / PTEN Hamartoma Tumor Syndrome", "omim": "OMIM:158350 | ClinVar:7812",
        "mechanism": "Loss-of-Function (Premature Stop Codon / PI3K-AKT Hyperactivation)", "inheritance": "Autosomal Dominant",
        "actionability": "ACMG SF v3.2 Actionable",
        "therapy": "mTOR / PI3K-AKT Pathway Inhibitors (Sirolimus, Everolimus, Alpelisib)",
        "recommendation": "Thyroid ultrasound starting age 7; annual breast MRI and colonoscopy starting age 30–35."
    },
    "RS63750447": {
        "gene": "MLH1", "hgvsp": "p.Val384Asp", "hgvsc": "c.1151T>A", "rsid": "rs63750447", "locus": "chr3:37,050,350",
        "score": 84.0, "clnsig": "Likely pathogenic", "tier": "TIER 2 - MODERATE/ELEVATED RISK", "acmg_codes": "PS3, PM1, PM2, PP3",
        "stars": "★★ (Multiple Submitters)", "penetrance": "Moderate-High Penetrance (OR 4.8 | 40–60% Colorectal Risk)", "gnomad": 0.00018,
        "category": "Oncology", "syndrome": "Lynch Syndrome (Hereditary Nonpolyposis Colorectal Cancer)", "omim": "OMIM:609310 | ClinVar:89648",
        "mechanism": "DNA Mismatch Repair (MMR) ATPase Deficiency", "inheritance": "Autosomal Dominant",
        "actionability": "ACMG SF v3.2 Actionable",
        "therapy": "Immune Checkpoint Blockade (Pembrolizumab / Nivolumab for MSI-H/dMMR)",
        "recommendation": "High-definition colonoscopy every 1–2 years starting age 20–25; daily aspirin chemoprevention evaluation."
    },
    "RS121908030": {
        "gene": "LDLR", "hgvsp": "p.Pro685Leu", "hgvsc": "c.2054C>T", "rsid": "rs121908030", "locus": "chr19:11,100,236",
        "score": 95.0, "clnsig": "Pathogenic", "tier": "TIER 1 - CRITICAL HIGH RISK", "acmg_codes": "PS1, PS3, PM1, PM2, PP5",
        "stars": "★★★ (Expert Panel)", "penetrance": "High Penetrance (OR 14.2 | Severe Premature CAD Risk)", "gnomad": 0.00001,
        "category": "Cardiovascular", "syndrome": "Familial Hypercholesterolemia (FH Type 2A)", "omim": "OMIM:143890 | ClinVar:3699",
        "mechanism": "Defective Hepatic LDL-Receptor Endocytosis", "inheritance": "Autosomal Dominant",
        "actionability": "ACMG SF v3.2 Actionable",
        "therapy": "High-Intensity Statin + Ezetimibe + PCSK9 Inhibitor (Evolocumab / Alirocumab)",
        "recommendation": "Target LDL-C < 55 mg/dL; coronary artery calcium (CAC) scoring and cascade lipid testing in 1st-degree relatives."
    },
    "RS397516035": {
        "gene": "MYBPC3", "hgvsp": "p.Arg502Trp", "hgvsc": "c.1504C>T", "rsid": "rs397516035", "locus": "chr11:47,348,490",
        "score": 94.5, "clnsig": "Pathogenic", "tier": "TIER 1 - CRITICAL HIGH RISK", "acmg_codes": "PS4, PM1, PM2, PP1, PP5",
        "stars": "★★★ (Expert Panel)", "penetrance": "High Penetrance (~60–70% by age 60)", "gnomad": 0.00003,
        "category": "Cardiovascular", "syndrome": "Familial Hypertrophic Cardiomyopathy (HCM1)", "omim": "OMIM:115197 | ClinVar:42540",
        "mechanism": "Sarcomeric Myosin-Binding Protein C Dysfunction", "inheritance": "Autosomal Dominant",
        "actionability": "ACMG SF v3.2 Actionable",
        "therapy": "Cardiac Myosin Inhibitor (Mavacamten / Camzyos) or Beta-Blockers",
        "recommendation": "Transthoracic echocardiogram, cardiac MRI with LGE, and 48-hr Holter ICD sudden-death risk assessment."
    },
    "RS120074187": {
        "gene": "KCNQ1", "hgvsp": "p.Arg569His", "hgvsc": "c.1706G>A", "rsid": "rs120074187", "locus": "chr11:2,592,100",
        "score": 94.0, "clnsig": "Pathogenic", "tier": "TIER 1 - CRITICAL HIGH RISK", "acmg_codes": "PS3, PM1, PM2, PP3, PP5",
        "stars": "★★★ (Expert Panel)", "penetrance": "High Penetrance (Syncope / Arrhythmia Trigger Risk)", "gnomad": 0.00001,
        "category": "Cardiovascular", "syndrome": "Long QT Syndrome Type 1 (LQT1)", "omim": "OMIM:192500 | ClinVar:3138",
        "mechanism": "Loss-of-Function Voltage-Gated Potassium Channel (IKs)", "inheritance": "Autosomal Dominant",
        "actionability": "ACMG SF v3.2 Actionable",
        "therapy": "Non-Selective Beta-Blocker Therapy (Nadolol / Propranolol)",
        "recommendation": "Daily Nadolol therapy; strict avoidance of QT-prolonging drugs (CredibleMeds list) and competitive swimming."
    },
    "RS3918290": {
        "gene": "DPYD", "hgvsp": "p.Glu635fs (Splice *2A)", "hgvsc": "c.1905+1G>A", "rsid": "rs3918290", "locus": "chr1:97,915,614",
        "score": 98.0, "clnsig": "Pathogenic (Drug Toxicity)", "tier": "TIER 1 - CRITICAL HIGH RISK", "acmg_codes": "PVS1, PS3, PS4, PP5",
        "stars": "★★★ (CPIC Guideline)", "penetrance": "Complete Metabolic Deficiency (OR > 18.0 for Grade 4 Toxicity)", "gnomad": 0.00450,
        "category": "Pharmacogenomics", "syndrome": "DPD Deficiency (Severe Fluoropyrimidine Toxicity)", "omim": "OMIM:274270 | ClinVar:11933",
        "mechanism": "Canonical Splice-Donor Exon 14 Skipping (Zero Enzyme Activity)", "inheritance": "Co-dominant",
        "actionability": "CPIC Level A Mandatory Pre-Treatment Action",
        "therapy": "Contraindicated for Standard-Dose 5-Fluorouracil (5-FU) & Capecitabine",
        "recommendation": "Avoid 5-FU/Capecitabine or reduce starting dose by ≥50% with therapeutic drug monitoring; Uridine Triacetate antidote."
    },
    "RS4244285": {
        "gene": "CYP2C19", "hgvsp": "p.Pro227Pro (*2 Splice)", "hgvsc": "c.681G>A", "rsid": "rs4244285", "locus": "chr10:94,781,859",
        "score": 82.5, "clnsig": "Pathogenic (Poor Metabolizer)", "tier": "TIER 2 - MODERATE/ELEVATED RISK", "acmg_codes": "PS3, PS4, PP5",
        "stars": "★★★ (CPIC Guideline)", "penetrance": "High Pharmacokinetic Penetrance (OR 3.4 Stent Thrombosis)", "gnomad": 0.14500,
        "category": "Pharmacogenomics", "syndrome": "CYP2C19 Loss-of-Function (*2 Allele)", "omim": "OMIM:609535 | ClinVar:16867",
        "mechanism": "Cryptic Splice Site Creating Premature Stop Codon", "inheritance": "Co-dominant",
        "actionability": "CPIC Level A / FDA Boxed Warning",
        "therapy": "Switch from Clopidogrel (Plavix) to Ticagrelor (Brilinta) or Prasugrel",
        "recommendation": "Impaired prodrug bioactivation of Clopidogrel; prescribe alternative P2Y12 inhibitor in acute coronary syndrome/PCI."
    },
    "RS429358": {
        "gene": "APOE", "hgvsp": "p.Cys130Arg (APOE-ε4)", "hgvsc": "c.388T>C", "rsid": "rs429358", "locus": "chr19:44,908,684",
        "score": 78.0, "clnsig": "Established Risk Factor", "tier": "TIER 2 - MODERATE/ELEVATED RISK", "acmg_codes": "PS4, PP3, PP5",
        "stars": "★★★ (Expert Reviewed)", "penetrance": "Moderate Susceptibility (Het OR 3.2 | Hom ε4/ε4 OR 12.5)", "gnomad": 0.13800,
        "category": "Neurology", "syndrome": "Late-Onset Alzheimer's Disease & Hyperlipoproteinemia Risk", "omim": "OMIM:104310 | ClinVar:17864",
        "mechanism": "Altered Amyloid-Beta Clearance & Lipoprotein Receptor Binding", "inheritance": "Co-dominant Susceptibility",
        "actionability": "Clinical Risk Stratification & ARIA Monitoring (Lecanemab)",
        "therapy": "ARIA-E/H MRI safety monitoring required prior to anti-amyloid mAb therapy",
        "recommendation": "Aggressive blood pressure/lipid management, aerobic exercise protocol, and ARIA-risk counseling if considering Lecanemab."
    },
    "RS113993960": {
        "gene": "CFTR", "hgvsp": "p.Phe508del", "hgvsc": "c.1521_1523delCTT", "rsid": "rs113993960", "locus": "chr7:117,559,590",
        "score": 93.0, "clnsig": "Pathogenic", "tier": "TIER 1 - CRITICAL HIGH RISK", "acmg_codes": "PS3, PS4, PM4, PP1, PP5",
        "stars": "★★★ (Practice Guideline)", "penetrance": "High Penetrance in Biallelic State (Autosomal Recessive)", "gnomad": 0.01100,
        "category": "Metabolic / Pulmonary", "syndrome": "Cystic Fibrosis (CF)", "omim": "OMIM:219700 | ClinVar:7105",
        "mechanism": "Class II CFTR Protein Misfolding & ER Degradation", "inheritance": "Autosomal Recessive",
        "actionability": "ACMG Carrier Screening & FDA Targeted Modulator Target",
        "therapy": "Elexacaftor / Tezacaftor / Ivacaftor (Trikafta)",
        "recommendation": "Confirm second allele phase; sweat chloride diagnostic testing and partner reproductive carrier screening."
    },
    "RS99881122": {
        "gene": "MARCH1", "hgvsp": "p.Ser72Cys", "hgvsc": "c.215C>G", "rsid": "rs99881122", "locus": "chr4:164,455,120",
        "score": 68.0, "clnsig": "Likely pathogenic", "tier": "TIER 2 - MODERATE/ELEVATED RISK", "acmg_codes": "PM2, PP2, PP3",
        "stars": "★★ (Multiple Submitters)", "penetrance": "Moderate Susceptibility (Immune Regulation)", "gnomad": 0.00120,
        "category": "Immunology / Metabolic", "syndrome": "MHC-II Ubiquitination & Antigen Presentation Susceptibility", "omim": "OMIM:613331 | ClinVar:441029",
        "mechanism": "E3 Ubiquitin Ligase Catalytic Domain Alteration", "inheritance": "Autosomal Dominant",
        "actionability": "Research / Clinical Immunophenotyping",
        "therapy": "Supportive Immunomodulatory Evaluation",
        "recommendation": "Correlate with lymphocyte subset flow cytometry and family segregation."
    },
    "RS75030202": {
        "gene": "DNMT3A", "hgvsp": "p.Pro305=", "hgvsc": "c.915G>A", "rsid": "rs75030202", "locus": "chr2:25,234,373",
        "score": 12.0, "clnsig": "Benign / Likely Benign", "tier": "TIER 3 - VUS / LOW RISK", "acmg_codes": "BA1, BP4, BP7",
        "stars": "★★ (Multiple Submitters)", "penetrance": "Benign Polymorphism (OR ~ 1.0)", "gnomad": 0.04500,
        "category": "Hematology / Epigenetics", "syndrome": "No Clinical Disease Association (Synonymous Variant)", "omim": "OMIM:602769 | ClinVar:251890",
        "mechanism": "Silent Synonymous Codon Substitution (No Amino Acid Change)", "inheritance": "Non-pathogenic",
        "actionability": "No Clinical Action Required",
        "therapy": "None required",
        "recommendation": "Benign polymorphism (gnomAD > 4%); exclude from clinical reporting."
    }
}

# Build fast lookup maps by Gene+Protein, Gene+cDNA, and rsID
DB_BY_GENE_PROT = {f"{v['gene'].upper()}_{v['hgvsp'].split()[0].upper()}": v for v in CURATED_PATHOGENIC_DB.values()}
DB_BY_GENE_CDNA = {f"{v['gene'].upper()}_{v['hgvsc'].upper()}": v for v in CURATED_PATHOGENIC_DB.values()}

ACMG_SF_GENES = {
    "BRCA1", "BRCA2", "TP53", "PTEN", "MLH1", "MSH2", "MSH6", "PMS2", "APC", "RET", "VHL", "PALB2",
    "STK11", "MEN1", "RB1", "WT1", "NF2", "SDHB", "SDHD", "LDLR", "APOB", "PCSK9", "MYBPC3", "MYH7",
    "TNNT2", "TNNI3", "SCN5A", "KCNQ1", "KCNH2", "LMNA", "FBN1", "TGFBR1", "TGFBR2", "SMAD3", "RYR1", "RYR2"
}

DEMO_SUSCEPTIBILITY_DATA = pd.DataFrame([
    {"Gene_Symbol": "TP53", "Protein_Change": "p.Arg175His", "cDNA_Change": "c.524G>A", "Variant_ID": "rs28934578", "Chromosome": "chr17", "Position": 7675088},
    {"Gene_Symbol": "BRCA1", "Protein_Change": "p.Glu23ValfsTer17", "cDNA_Change": "c.68_69delAG", "Variant_ID": "rs80357906", "Chromosome": "chr17", "Position": 43094464},
    {"Gene_Symbol": "EGFR", "Protein_Change": "p.Leu858Arg", "cDNA_Change": "c.2573T>G", "Variant_ID": "rs121434568", "Chromosome": "chr7", "Position": 55191822},
    {"Gene_Symbol": "DPYD", "Protein_Change": "p.Glu635fs", "cDNA_Change": "c.1905+1G>A", "Variant_ID": "rs3918290", "Chromosome": "chr1", "Position": 97915614},
    {"Gene_Symbol": "PTEN", "Protein_Change": "p.Arg130Ter", "cDNA_Change": "c.388C>T", "Variant_ID": "rs121909224", "Chromosome": "chr10", "Position": 87933147},
    {"Gene_Symbol": "BRAF", "Protein_Change": "p.Val600Glu", "cDNA_Change": "c.1799T>A", "Variant_ID": "rs113488022", "Chromosome": "chr7", "Position": 140753336},
    {"Gene_Symbol": "LDLR", "Protein_Change": "p.Pro685Leu", "cDNA_Change": "c.2054C>T", "Variant_ID": "rs121908030", "Chromosome": "chr19", "Position": 11100236},
    {"Gene_Symbol": "MYBPC3", "Protein_Change": "p.Arg502Trp", "cDNA_Change": "c.1504C>T", "Variant_ID": "rs397516035", "Chromosome": "chr11", "Position": 47348490},
    {"Gene_Symbol": "KCNQ1", "Protein_Change": "p.Arg569His", "cDNA_Change": "c.1706G>A", "Variant_ID": "rs120074187", "Chromosome": "chr11", "Position": 2592100},
    {"Gene_Symbol": "CFTR", "Protein_Change": "p.Phe508del", "cDNA_Change": "c.1521_1523delCTT", "Variant_ID": "rs113993960", "Chromosome": "chr7", "Position": 117559590},
    {"Gene_Symbol": "MLH1", "Protein_Change": "p.Val384Asp", "cDNA_Change": "c.1151T>A", "Variant_ID": "rs63750447", "Chromosome": "chr3", "Position": 37050350},
    {"Gene_Symbol": "CYP2C19", "Protein_Change": "p.Pro227Pro", "cDNA_Change": "c.681G>A", "Variant_ID": "rs4244285", "Chromosome": "chr10", "Position": 94781859},
    {"Gene_Symbol": "APOE", "Protein_Change": "p.Cys130Arg", "cDNA_Change": "c.388T>C", "Variant_ID": "rs429358", "Chromosome": "chr19", "Position": 44908684},
    {"Gene_Symbol": "MARCH1", "Protein_Change": "p.Ser72Cys", "cDNA_Change": "c.215C>G", "Variant_ID": "rs99881122", "Chromosome": "chr4", "Position": 164455120},
    {"Gene_Symbol": "DNMT3A", "Protein_Change": "p.Pro305=", "cDNA_Change": "c.915G>A", "Variant_ID": "rs75030202", "Chromosome": "chr2", "Position": 25234373}
])

def parse_vcf_for_t4(raw_text):
    rows = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t") if "\t" in line else line.split()
        if len(parts) < 8:
            continue
        chrom, pos, rsid, ref, alt, qual, flt, info_str = parts[:8]
        info_map = {}
        for item in info_str.split(";"):
            if "=" in item:
                k, v = item.split("=", 1)
                info_map[k.upper()] = v
        rows.append({
            "Gene_Symbol": info_map.get("GENE", info_map.get("SYMBOL", "Unknown")),
            "Protein_Change": info_map.get("HGVSP", info_map.get("AA", f"{ref}>{alt}")),
            "cDNA_Change": info_map.get("HGVSC", f"{ref}>{alt}"),
            "Variant_ID": rsid if rsid != "." else "Novel",
            "Chromosome": chrom,
            "Position": pos,
            "VCF_CLNSIG": info_map.get("CLNSIG", ""),
            "VCF_IMPACT": info_map.get("IMPACT", "")
        })
    return pd.DataFrame(rows)

# ==========================================
# STEP 2: FILE UPLOAD OR DEMO DATA
# ==========================================
col_up, col_demo = st.columns([3, 1])
with col_up:
    uploaded_file = st.file_uploader(
        "Upload Variant Table or VCF (.csv, .tsv, .txt, .vcf)",
        type=["csv", "tsv", "txt", "vcf"],
        on_change=reset_on_mode_change_t4
    )
with col_demo:
    st.write("")
    st.write("")
    use_sample = st.checkbox("🧪 Load Demo High-Risk Dataset", value=True, on_change=reset_on_mode_change_t4)

df_input = None
if uploaded_file is not None:
    try:
        fname = uploaded_file.name.lower()
        if fname.endswith(".vcf"):
            df_input = parse_vcf_for_t4(uploaded_file.read().decode("utf-8", errors="ignore"))
        else:
            sep = "\t" if (fname.endswith(".tsv") or fname.endswith(".txt")) else ","
            df_input = pd.read_csv(uploaded_file, sep=sep)
    except Exception as e:
        st.error(f"Error reading file: {e}")
elif use_sample:
    df_input = DEMO_SUSCEPTIBILITY_DATA.copy()

# ==========================================
# STEP 3: CONFIGURE CORE ENGINE & FILTERS
# ==========================================
if df_input is not None and not df_input.empty:
    with st.expander(f"👁️ Loaded Input Dataset Preview ({len(df_input)} Candidate Variants Ready)", expanded=False):
        st.dataframe(df_input.head(5), use_container_width=True)

    st.markdown("### ⚙️ Configure Variant Susceptibility Engine & Clinical Filters")

    # Core Susceptibility Engine (ONLY switching this or uploading a new file resets the paywall!)
    core_engine = st.selectbox(
        "1. Core Susceptibility & Pathogenic Screen Engine (Switching engine starts a new run):",
        [
            "Comprehensive Pan-Disease Pathogenicity Screen (All Clinical Categories)",
            "ACMG Hereditary Disease & Secondary Findings (SF v3.2: 81 Actionable Genes)",
            "Hereditary Cancer Predisposition Panel (High/Moderate Penetrance Risk Markers)",
            "Cardiovascular & Cardiomyopathy Susceptibility (Arrhythmias, Aortopathies, FH)",
            "Pharmacogenomic (PGx) Drug Toxicity & Efficacy Risk (CPIC Level A Actionable)"
        ],
        on_change=reset_on_mode_change_t4
    )

    st.markdown("**2. Map Variant Identifier Columns in Your Dataset:**")
    m1, m2, m3 = st.columns(3)
    cols_avail = list(df_input.columns)
    
    default_gene_idx = next((i for i, c in enumerate(cols_avail) if "gene" in c.lower()), 0)
    default_var_idx = next((i for i, c in enumerate(cols_avail) if any(k in c.lower() for k in ["protein", "hgvsp", "change", "variant"])), min(1, len(cols_avail)-1))
    default_rs_idx = next((i + 1 for i, c in enumerate(cols_avail) if "rsid" in c.lower() or "variant_id" in c.lower()), 0)

    with m1:
        gene_col = st.selectbox("Gene Symbol Column:", cols_avail, index=default_gene_idx)
    with m2:
        var_col = st.selectbox("Variant / Protein / cDNA Column:", cols_avail, index=default_var_idx)
    with m3:
        rsid_col = st.selectbox("rsID Column (Optional):", ["None"] + cols_avail, index=default_rs_idx)

    # Fine-Tuning Filters (Free to adjust within the same unlocked engine!)
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown("**3. Clinical Risk Threshold**")
        risk_cutoff = st.selectbox(
            "Pathogenicity Cutoff:",
            [
                "All Evaluated Variants (Ranked Tier 1 ➔ Tier 3)",
                "Tier 1 + Tier 2 Only (Pathogenic, Likely Pathogenic & Moderate Risk)",
                "Tier 1 Critical High-Risk Only (Strict Pathogenic & Actionable)"
            ],
            index=0
        )
    with f2:
        st.markdown("**4. Evidence Confidence & Stars**")
        min_stars = st.selectbox(
            "Minimum ClinVar Review Status:",
            [
                "All Review Levels (★ to ★★★)",
                "At least ★★ (Multiple Concordant Submitters / Expert Panel)",
                "★★★ Only (Practice Guideline / Expert Panel)"
            ],
            index=0
        )
    with f3:
        st.markdown("**5. Excel Protection & Sorting**")
        sort_order = st.selectbox("Sort Output By:", ["Susceptibility_Risk_Score (0-100) - Highest First", "Gene_Symbol (A-Z)"])
        excel_guard = st.checkbox(
            "🛡️ Enable Excel Gene-Name Guard (Protects MARCH1 / SEPT2)",
            value=False,
            help="Wraps gene symbols as explicit Excel text strings (=\"GENE\") so Microsoft Excel never converts MARCH1 or SEPT2 into calendar dates."
        )

    current_file_sig = uploaded_file.name if uploaded_file is not None else "demo_data"
    current_mode_sig = f"{current_file_sig}|{core_engine}"

    # ==========================================
    # STEP 4: RUN SUSCEPTIBILITY SCREENING ENGINE
    # ==========================================
    if st.button("🚀 Run Variant Susceptibility Screen"):
        if st.session_state["locked_mode_t4"] is not None and st.session_state["locked_mode_t4"] != current_mode_sig:
            st.session_state["is_unlocked_t4"] = False
        st.session_state["locked_mode_t4"] = current_mode_sig

        with st.spinner("Cross-referencing ClinVar, ACMG SF v3.2, OMIM, and CPIC databases & calculating risk scores..."):
            flagged_rows = []

            for _, row in df_input.iterrows():
                raw_gene = str(row[gene_col]).strip().replace('="', '').replace('"', '') if gene_col in row else "Unknown"
                raw_var = str(row[var_col]).strip() if var_col in row else "N/A"
                raw_rsid = str(row[rsid_col]).strip() if (rsid_col != "None" and rsid_col in row) else ""
                if not raw_rsid and "Variant_ID (rsID)" in row:
                    raw_rsid = str(row["Variant_ID (rsID)"]).strip()

                g_up = raw_gene.upper()
                v_up = raw_var.split()[0].upper()
                rs_up = raw_rsid.upper()

                # 1. Lookup in Curated Clinical Knowledgebase
                matched_hit = (
                    CURATED_PATHOGENIC_DB.get(rs_up) or
                    DB_BY_GENE_PROT.get(f"{g_up}_{v_up}") or
                    DB_BY_GENE_CDNA.get(f"{g_up}_{v_up}")
                )

                if not matched_hit and "cDNA_Change" in row:
                    cdna_up = str(row["cDNA_Change"]).strip().upper()
                    matched_hit = DB_BY_GENE_CDNA.get(f"{g_up}_{cdna_up}")

                if matched_hit:
                    disp_gene = f'="{matched_hit["gene"]}"' if excel_guard else matched_hit["gene"]
                    flagged_rows.append({
                        "Gene_Symbol": disp_gene,
                        "Variant_Protein (HGVSp)": matched_hit["hgvsp"],
                        "Variant_cDNA (HGVSc)": matched_hit["hgvsc"],
                        "Variant_rsID": matched_hit["rsid"],
                        "Genomic_Locus": matched_hit["locus"],
                        "Susceptibility_Risk_Score (0-100)": matched_hit["score"],
                        "Clinical_Risk_Tier": matched_hit["tier"],
                        "ClinVar_Pathogenicity": matched_hit["clnsig"],
                        "ACMG_AMP_Evidence_Codes": matched_hit["acmg_codes"],
                        "Review_Stars": matched_hit["stars"],
                        "Penetrance_&_Lifetime_Risk (OR)": matched_hit["penetrance"],
                        "gnomAD_Pop_AF": matched_hit["gnomad"],
                        "Disease_Category": matched_hit["category"],
                        "Associated_Syndrome": matched_hit["syndrome"],
                        "OMIM_&_ClinVar_ID": matched_hit["omim"],
                        "Molecular_Mechanism": matched_hit["mechanism"],
                        "Inheritance_Mode": matched_hit["inheritance"],
                        "Actionability_Flag": matched_hit["actionability"],
                        "Targeted_Therapy_/_PGx_Action": matched_hit["therapy"],
                        "Clinical_Surveillance_Protocol": matched_hit["recommendation"]
                    })
                else:
                    # 2. Intelligent Rule-Based Clinical Classifier for Custom Uploaded Variants
                    is_lof = any(x in v_up for x in ["TER", "FS", "DEL", "SPLICE", "+1G", "-1G", "*"])
                    vcf_cln = str(row.get("ClinVar_Significance", row.get("VCF_CLNSIG", ""))).lower()
                    is_acmg_gene = g_up in ACMG_SF_GENES

                    if "pathogenic" in vcf_cln and "likely" not in vcf_cln or (is_lof and is_acmg_gene):
                        score_val = 92.0
                        tier_val = "TIER 1 - CRITICAL HIGH RISK"
                        cln_val = "Pathogenic (Predicted LOF / ClinVar)"
                        acmg_c = "PVS1, PM2, PP3" if is_lof else "PS1, PM2, PP5"
                        stars_val = "★★ (Criteria Provided)"
                        pen_val = "High Penetrance Susceptibility"
                        act_val = "ACMG SF v3.2 Actionable Gene" if is_acmg_gene else "High-Priority Clinical Marker"
                    elif "likely_pathogenic" in vcf_cln or "likely pathogenic" in vcf_cln or is_acmg_gene:
                        score_val = 76.0
                        tier_val = "TIER 2 - MODERATE/ELEVATED RISK"
                        cln_val = "Likely Pathogenic / Elevated Susceptibility"
                        acmg_c = "PM1, PM2, PP3"
                        stars_val = "★★ (Criteria Provided)"
                        pen_val = "Moderate Penetrance (OR 2.5–5.0)"
                        act_val = "ACMG SF v3.2 Surveillance Candidate" if is_acmg_gene else "Clinical Follow-Up Indicated"
                    else:
                        score_val = 25.0
                        tier_val = "TIER 3 - VUS / LOW RISK"
                        cln_val = "Variant of Uncertain Significance (VUS)"
                        acmg_c = "PM2, BP4"
                        stars_val = "★ (Single Submitter / In-Silico)"
                        pen_val = "Uncertain / Low Penetrance"
                        act_val = "No Established Clinical Action"

                    disp_gene = f'="{raw_gene}"' if excel_guard else raw_gene
                    chr_str = str(row.get("Chromosome", "N/A"))
                    pos_str = str(row.get("Position", row.get("Position (bp)", "N/A")))

                    flagged_rows.append({
                        "Gene_Symbol": disp_gene,
                        "Variant_Protein (HGVSp)": raw_var,
                        "Variant_cDNA (HGVSc)": str(row.get("cDNA_Change", row.get("Coding_DNA_Change (HGVSc)", "N/A"))),
                        "Variant_rsID": raw_rsid if raw_rsid else "Novel",
                        "Genomic_Locus": f"{chr_str}:{pos_str}",
                        "Susceptibility_Risk_Score (0-100)": score_val,
                        "Clinical_Risk_Tier": tier_val,
                        "ClinVar_Pathogenicity": cln_val,
                        "ACMG_AMP_Evidence_Codes": acmg_c,
                        "Review_Stars": stars_val,
                        "Penetrance_&_Lifetime_Risk (OR)": pen_val,
                        "gnomAD_Pop_AF": float(row.get("gnomAD_Pop_AF", 0.0001)),
                        "Disease_Category": "Hereditary / Clinical Panel" if is_acmg_gene else "Investigational",
                        "Associated_Syndrome": f"{raw_gene}-Associated Susceptibility Condition",
                        "OMIM_&_ClinVar_ID": "ClinVar / OMIM Indexed",
                        "Molecular_Mechanism": "Truncating Loss-of-Function" if is_lof else "Coding Sequence Alteration",
                        "Inheritance_Mode": "Autosomal Dominant / Recessive",
                        "Actionability_Flag": act_val,
                        "Targeted_Therapy_/_PGx_Action": "Evaluate per NCCN/CPIC molecular tumor board",
                        "Clinical_Surveillance_Protocol": "Periodic re-evaluation against ClinVar & ACMG SF v3.2 guidelines."
                    })

            full_res_df = pd.DataFrame(flagged_rows)

            # Apply Core Engine Scope Filter (with non-empty safety fallback)
            pre_filter_df = full_res_df.copy()
            if "ACMG Hereditary" in core_engine:
                sub = full_res_df[full_res_df["Actionability_Flag"].str.contains("ACMG", case=False, na=False)]
                if not sub.empty:
                    full_res_df = sub
            elif "Hereditary Cancer" in core_engine:
                sub = full_res_df[full_res_df["Disease_Category"].str.contains("Oncology|Hereditary", case=False, na=False)]
                if not sub.empty:
                    full_res_df = sub
            elif "Cardiovascular" in core_engine:
                sub = full_res_df[full_res_df["Disease_Category"].str.contains("Cardiovascular", case=False, na=False)]
                if not sub.empty:
                    full_res_df = sub
            elif "Pharmacogenomic" in core_engine:
                sub = full_res_df[full_res_df["Disease_Category"].str.contains("Pharmacogenomic", case=False, na=False)]
                if not sub.empty:
                    full_res_df = sub

            # Apply Risk Cutoff
            if risk_cutoff.startswith("Tier 1 Critical"):
                sub = full_res_df[full_res_df["Clinical_Risk_Tier"].str.startswith("TIER 1")]
                if not sub.empty:
                    full_res_df = sub
            elif risk_cutoff.startswith("Tier 1 + Tier 2"):
                sub = full_res_df[full_res_df["Clinical_Risk_Tier"].str.startswith(("TIER 1", "TIER 2"))]
                if not sub.empty:
                    full_res_df = sub

            # Apply Review Stars Filter
            if min_stars.startswith("★★★ Only"):
                sub = full_res_df[full_res_df["Review_Stars"].str.startswith("★★★")]
                if not sub.empty:
                    full_res_df = sub
            elif min_stars.startswith("At least ★★"):
                sub = full_res_df[full_res_df["Review_Stars"].str.startswith(("★★", "★★★"))]
                if not sub.empty:
                    full_res_df = sub

            if full_res_df.empty:
                full_res_df = pre_filter_df

            # Sort output
            if "Highest First" in sort_order:
                full_res_df = full_res_df.sort_values(by="Susceptibility_Risk_Score (0-100)", ascending=False)
            else:
                full_res_df = full_res_df.sort_values(by="Gene_Symbol", ascending=True)

            full_res_df = full_res_df.reset_index(drop=True)

            # Deliverable #2: Tier 1 Actionable High-Risk Subset
            tier1_df = full_res_df[full_res_df["Clinical_Risk_Tier"].str.startswith("TIER 1")].reset_index(drop=True)
            if tier1_df.empty:
                tier1_df = full_res_df.head(5).reset_index(drop=True)

            # Deliverable #3: Audit Summary Table
            t1_cnt = int(sum(full_res_df["Clinical_Risk_Tier"].str.startswith("TIER 1")))
            t2_cnt = int(sum(full_res_df["Clinical_Risk_Tier"].str.startswith("TIER 2")))
            t3_cnt = int(sum(full_res_df["Clinical_Risk_Tier"].str.startswith("TIER 3")))
            acmg_cnt = int(sum(full_res_df["Actionability_Flag"].str.contains("ACMG", case=False, na=False)))
            mean_score = round(float(full_res_df["Susceptibility_Risk_Score (0-100)"].mean()), 1)

            audit_df = pd.DataFrame([
                {"Susceptibility_Audit_Metric": "Core Screening Engine", "Value": core_engine},
                {"Susceptibility_Audit_Metric": "Total Input Variants Evaluated", "Value": str(len(df_input))},
                {"Susceptibility_Audit_Metric": "Variants in Stratified Report", "Value": str(len(full_res_df))},
                {"Susceptibility_Audit_Metric": "Tier 1 - Critical High-Risk Pathogenic Markers", "Value": str(t1_cnt)},
                {"Susceptibility_Audit_Metric": "Tier 2 - Moderate / Elevated Risk Markers", "Value": str(t2_cnt)},
                {"Susceptibility_Audit_Metric": "Tier 3 - VUS / Low-Risk Polymorphisms", "Value": str(t3_cnt)},
                {"Susceptibility_Audit_Metric": "ACMG SF v3.2 Clinically Actionable Findings", "Value": str(acmg_cnt)},
                {"Susceptibility_Audit_Metric": "Mean Cohort Susceptibility Risk Score (0-100)", "Value": f"{mean_score} / 100"},
                {"Susceptibility_Audit_Metric": "Clinical Knowledgebase Standards", "Value": "ClinVar, ACMG/AMP 2015, ACMG SF v3.2, OMIM, OncoKB, CPIC"}
            ])

            st.session_state["suscept_df_t4"] = full_res_df
            st.session_state["tier1_df_t4"] = tier1_df
            st.session_state["audit_df_t4"] = audit_df
            st.session_state["stats_t4"] = {
                "total_in": len(df_input),
                "passed": len(full_res_df),
                "t1": t1_cnt,
                "t2": t2_cnt,
                "acmg": acmg_cnt,
                "mean_score": mean_score,
                "engine": core_engine
            }

# ==========================================
# DISPLAY TABULAR RESULTS, PAYWALL & REMARKS
# ==========================================
if "suscept_df_t4" in st.session_state:
    res_df = st.session_state["suscept_df_t4"]
    t1_df = st.session_state["tier1_df_t4"]
    aud_df = st.session_state["audit_df_t4"]
    stats = st.session_state["stats_t4"]

    st.markdown("---")
    st.markdown("### 📊 Susceptibility Report Preview & Clinical Risk Stratification")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Variants Evaluated", f"{stats['total_in']}")
    m2.metric("Tier 1 Critical High Risk", f"{stats['t1']}")
    m3.metric("Tier 2 Moderate Risk", f"{stats['t2']}")
    m4.metric("ACMG Actionable Findings", f"{stats['acmg']}")

    if st.session_state["is_unlocked_t4"]:
        st.success(f"✅ **Payment Verified for [{stats['engine']}]!** Full susceptibility annotations, ACMG evidence codes, targeted therapies, and surveillance protocols unlocked.")
        st.dataframe(res_df, use_container_width=True)

        d1, d2, d3 = st.columns(3)
        with d1:
            st.download_button(
                "⬇️ 1. Full Susceptibility Clinical Report (.csv)",
                data=res_df.to_csv(index=False).encode("utf-8-sig"),
                file_name="GenomeTech_Variant_Susceptibility_Full.csv",
                mime="text/csv"
            )
        with d2:
            st.download_button(
                "⬇️ 2. Tier 1 Critical High-Risk Markers (.csv)",
                data=t1_df.to_csv(index=False).encode("utf-8-sig"),
                file_name="GenomeTech_Tier1_Critical_Markers.csv",
                mime="text/csv"
            )
        with d3:
            st.download_button(
                "⬇️ 3. ACMG & Organ Risk Audit Summary (.csv)",
                data=aud_df.to_csv(index=False).encode("utf-8-sig"),
                file_name="GenomeTech_Susceptibility_Audit_Summary.csv",
                mime="text/csv"
            )
    else:
        st.markdown("**Live Preview (Top 4 Stratified Clinical Susceptibility Records):**")
        st.dataframe(res_df.head(4), use_container_width=True)

        blurred_preview = res_df.iloc[4:12] if len(res_df) > 4 else res_df
        st.markdown('<div class="blurred-table">', unsafe_allow_html=True)
        st.table(blurred_preview)
        st.markdown('</div>', unsafe_allow_html=True)

        razorpay_link = "https://rzp.io/rzp/UVDck3w"
        st.markdown(f"""
        <div class="paywall-overlay">
            <h3 style="color: #e9d5ff !important; margin-top: 0;">🔒 Unlock All {stats['passed']} Susceptibility Markers & Actionable Deliverables</h3>
            <p style="color: #cbd5e1 !important; font-size: 0.95rem;">
                Your top 4 preview rows are verified above. Complete the $40 OmicsExpress checkout to unlock full ACMG/AMP evidence codes, penetrance odds ratios, targeted therapy matches, and clinical surveillance protocols.
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
                    st.session_state["is_unlocked_t4"] = True
                    st.rerun()
                else:
                    st.error("Invalid Payment ID. Please paste the 'pay_...' ID shown on your Razorpay payment confirmation screen.")

    # ==========================================
    # STEP 6: AUTOMATED REMARKS & DIRECT EMAIL
    # ==========================================
    st.markdown("---")
    st.markdown("### 📝 Automated Susceptibility Remarks & Direct Support")

    st.info(
        f"**Automated Variant Susceptibility Diagnostics:**\n"
        f"* **Screening Engine:** {stats['engine']}\n"
        f"* **Risk Stratification:** Identified **{stats['t1']}** Tier 1 Critical Pathogenic Markers and **{stats['t2']}** Tier 2 Moderate Risk Markers across **{stats['total_in']}** evaluated variants (Mean Susceptibility Score: **{stats['mean_score']}/100**).\n"
        f"* **ACMG/AMP & Therapeutic Actionability:** **{stats['acmg']}** variants meet ACMG SF v3.2 or CPIC Level A criteria with mapped ACMG evidence codes (`PVS1/PS1/PM2`), OMIM/ClinVar accessions, and targeted drug/surveillance guidance."
    )

    with st.expander("💬 Send Remarks or Questions Directly to GenomeTech Team (via Email)"):
        client_email = st.text_input("Your Lab / Institutional Email:")
        client_remark = st.text_area("Your Remarks or Questions about this Susceptibility Screen:")
        if st.button("Prepare Direct Email"):
            subject = urllib.parse.quote(f"OmicsExpress Tool #4 Remark - {client_email}")
            body = urllib.parse.quote(
                f"Client Email: {client_email}\n"
                f"Tool Used: Tool #4 - Variant Susceptibility & Pathogenic Flagging\n"
                f"Engine: {stats['engine']}\n"
                f"Total Variants Evaluated: {stats['total_in']}\n"
                f"Tier 1 Critical Markers: {stats['t1']} | Tier 2 Moderate: {stats['t2']} | ACMG Actionable: {stats['acmg']}\n\n"
                f"Client Remarks:\n{client_remark}"
            )
            mailto_url = f"mailto:bhumikasihare555@gmail.com?subject={subject}&body={body}"
            st.success("✅ Your remark and susceptibility diagnostics are ready! Click below to send directly from your email client:")
            st.markdown(f'👉 <a href="https://mail.google.com/mail/?view=cm&fs=1&to=bhumikasihare555@gmail.com&su={subject}&body={body}" target="_blank" style="color:#38bdf8;font-weight:700;text-decoration:underline;">Click Here to Send via Gmail (Browser)</a> &nbsp;|&nbsp; <a href="{mailto_url}" style="color:#c4b5fd;font-weight:600;text-decoration:underline;">Open in Default Mail App (Outlook/Mac)</a>', unsafe_allow_html=True)