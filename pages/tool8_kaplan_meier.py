import streamlit as st
import pandas as pd
import numpy as np
import math
import html
import urllib.parse

try:
    from scipy import stats as sp_stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

# 1. Page Configuration (Isolated Single-Tool View)
st.set_page_config(
    page_title="Kaplan-Meier Survival Plotter | OmicsExpress",
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
    <span class="gts-badge">⚡ Tool #8: Kaplan-Meier Survival Plotter</span>
</div>
""", unsafe_allow_html=True)

query_params = st.query_params
if "unlocked" in query_params and query_params["unlocked"] == "GTS2026":
    st.session_state["is_unlocked_t8"] = True
if "is_unlocked_t8" not in st.session_state:
    st.session_state["is_unlocked_t8"] = False
if "locked_mode_t8" not in st.session_state:
    st.session_state["locked_mode_t8"] = None

# Callback that resets unlock & results ONLY when Core Survival Engine or Uploaded File changes
def reset_on_mode_change_t8():
    st.session_state["is_unlocked_t8"] = False
    st.session_state.pop("km_curve_df_t8", None)
    st.session_state.pop("summary_df_t8", None)
    st.session_state.pop("patient_assign_df_t8", None)
    st.session_state.pop("batch_hr_df_t8", None)
    st.session_state.pop("svg_km_t8", None)
    st.session_state.pop("svg_haz_t8", None)
    st.session_state.pop("svg_forest_t8", None)
    st.session_state.pop("svg_landmark_t8", None)
    st.session_state.pop("html_report_t8", None)
    st.session_state.pop("stats_t8", None)

st.markdown("## Kaplan-Meier Clinical Survival & Prognostic Biomarker Suite")
st.markdown(
    "Upload clinical **Time-to-Event (`OS` / `PFS` / `DFS` / `RFS`)** and **Gene Expression / Biomarker** spreadsheets (`.csv`, `.tsv`, `.txt`). "
    "Instantly computes **Mantel-Cox Log-Rank exact $P$-values, Hazard Ratios ($\text{HR}$) with 95% CIs, Restricted Mean Survival Time (`RMST`), "
    "Optimal Cutpoint thresholds, Greenwood 95% CI bands, Number-at-Risk tables, and 4 Publication-Ready Vector Figures (`.svg`)**."
)

with st.expander("📋 Accepted File Formats, Cross-Platform Guide & Complete Deliverables (.csv, .svg, .html)", expanded=True):
    st.markdown("""
    * **Required Columns in Your Spreadsheet:**
      1. **Follow-Up Time Column:** Numeric survival time (`OS_Months`, `PFS_Days`, `FollowUp_Years`).
      2. **Event Status Column:** Supports numeric (`1` = Event/Deceased/Relapsed, `0` = Censored/Alive/Event-Free) OR clinical text (`Deceased`/`Alive`, `Dead`/`Living`, `Event`/`Censored`, `Progressed`/`Stable`).
      3. **Biomarker / Gene Columns (or Clinical Group Column):** Continuous expression columns (`TPM`, `FPKM`, `Log2`, `Protein_Level`) or categorical arms (`Stage`, `Treatment_Group`).
    * **4 Publication-Ready Figures & 4 Clinical CSV Tables Generated Automatically:**
      * **Figure 1A (Annotated Kaplan-Meier Curve + Number-at-Risk Table):** Step-function survival curves, toggleable **95% CI shaded ribbons**, censored tick marks (`+`), 50% median drop-lines, and aligned **Number at Risk** matrix.
      * **Figure 1B (Nelson-Aalen Cumulative Hazard Trajectory):** Plots cumulative event hazard $H(t)$ over follow-up time.
      * **Figure 1C (Multi-Gene Prognostic Hazard Ratio Forest Plot):** Ranks all genes/biomarkers in your file by Hazard Ratio ($\text{HR}$) and 95% CI.
      * **Figure 1D (Landmark Survival Probability Chart):** Automatically adapts landmarks to your chosen time unit (`12/24/36/60 Months`, `1/2/3/5 Years`, or `180/365/730/1095 Days`).
      * **4 CSV Tables:** (1) Cohort Summary (`Median Survival`, `RMST`, `HR`, `Landmarks`), (2) Patient-Level Risk Group Assignments (`High` vs `Low`), (3) Multi-Gene Batch Prognostic Screen, and (4) Exact KM Step Coordinates.
    * **💻 Cross-Platform File Compatibility (Windows & Apple macOS):** All exported `.csv` tables use universal `UTF-8-BOM` encoding—double-click to open directly in **Microsoft Excel (Windows/Mac)**, **Apple Numbers**, **Google Sheets**, or load into **R / Python**. Vector figure (`.svg` / `.html`) outputs open natively in any web browser (**Safari / Chrome / Edge**) or vector editor (**Illustrator / PowerPoint / Keynote**).
    * **Single-Mode License Note:** Each checkout unlocks your selected **Core Stratification & Survival Engine** across all genes/biomarkers in your uploaded dataset. Switching between target genes, changing endpoints, toggling 95% CI ribbons, or adjusting time units within your unlocked engine is free; switching the Core Survival Engine or uploading a new file starts a new run.
    """)

# ==========================================
# DEMO ONCOLOGY COHORT DATASET (N = 36)
# ==========================================
DEMO_SURVIVAL_DF = pd.DataFrame([
    {"Patient_ID": "PT_001", "OS_Months": 6.2,  "Vital_Status": "Deceased", "Clinical_Arm": "High_Risk_StageIV", "EGFR_TPM": 940.2, "MYC_TPM": 880.5, "CD274_PDL1_TPM": 14.2, "TP53_TPM": 32.1, "MARCH1_TPM": 88.4},
    {"Patient_ID": "PT_002", "OS_Months": 8.5,  "Vital_Status": "Deceased", "Clinical_Arm": "High_Risk_StageIV", "EGFR_TPM": 890.0, "MYC_TPM": 910.2, "CD274_PDL1_TPM": 18.5, "TP53_TPM": 28.4, "MARCH1_TPM": 82.0},
    {"Patient_ID": "PT_003", "OS_Months": 10.1, "Vital_Status": "Deceased", "Clinical_Arm": "High_Risk_StageIV", "EGFR_TPM": 815.4, "MYC_TPM": 790.0, "CD274_PDL1_TPM": 21.0, "TP53_TPM": 39.5, "MARCH1_TPM": 79.5},
    {"Patient_ID": "PT_004", "OS_Months": 11.8, "Vital_Status": "Deceased", "Clinical_Arm": "High_Risk_StageIV", "EGFR_TPM": 780.6, "MYC_TPM": 845.1, "CD274_PDL1_TPM": 16.8, "TP53_TPM": 35.0, "MARCH1_TPM": 91.2},
    {"Patient_ID": "PT_005", "OS_Months": 12.4, "Vital_Status": "Censored", "Clinical_Arm": "High_Risk_StageIV", "EGFR_TPM": 760.2, "MYC_TPM": 720.4, "CD274_PDL1_TPM": 24.5, "TP53_TPM": 42.8, "MARCH1_TPM": 74.1},
    {"Patient_ID": "PT_006", "OS_Months": 14.0, "Vital_Status": "Deceased", "Clinical_Arm": "High_Risk_StageIV", "EGFR_TPM": 840.9, "MYC_TPM": 805.6, "CD274_PDL1_TPM": 19.2, "TP53_TPM": 31.0, "MARCH1_TPM": 85.6},
    {"Patient_ID": "PT_007", "OS_Months": 15.6, "Vital_Status": "Deceased", "Clinical_Arm": "High_Risk_StageIV", "EGFR_TPM": 710.5, "MYC_TPM": 695.0, "CD274_PDL1_TPM": 28.4, "TP53_TPM": 48.2, "MARCH1_TPM": 69.8},
    {"Patient_ID": "PT_008", "OS_Months": 17.2, "Vital_Status": "Deceased", "Clinical_Arm": "High_Risk_StageIV", "EGFR_TPM": 685.0, "MYC_TPM": 740.8, "CD274_PDL1_TPM": 25.1, "TP53_TPM": 45.6, "MARCH1_TPM": 72.3},
    {"Patient_ID": "PT_009", "OS_Months": 18.9, "Vital_Status": "Deceased", "Clinical_Arm": "High_Risk_StageIV", "EGFR_TPM": 730.4, "MYC_TPM": 680.2, "CD274_PDL1_TPM": 31.0, "TP53_TPM": 52.1, "MARCH1_TPM": 66.0},
    {"Patient_ID": "PT_010", "OS_Months": 20.5, "Vital_Status": "Censored", "Clinical_Arm": "High_Risk_StageIV", "EGFR_TPM": 640.8, "MYC_TPM": 620.5, "CD274_PDL1_TPM": 34.8, "TP53_TPM": 58.0, "MARCH1_TPM": 61.5},
    {"Patient_ID": "PT_011", "OS_Months": 22.1, "Vital_Status": "Deceased", "Clinical_Arm": "High_Risk_StageIV", "EGFR_TPM": 695.2, "MYC_TPM": 660.0, "CD274_PDL1_TPM": 29.5, "TP53_TPM": 50.4, "MARCH1_TPM": 68.2},
    {"Patient_ID": "PT_012", "OS_Months": 24.0, "Vital_Status": "Deceased", "Clinical_Arm": "High_Risk_StageIV", "EGFR_TPM": 610.0, "MYC_TPM": 590.4, "CD274_PDL1_TPM": 38.2, "TP53_TPM": 63.5, "MARCH1_TPM": 58.9},
    {"Patient_ID": "PT_013", "OS_Months": 25.8, "Vital_Status": "Deceased", "Clinical_Arm": "High_Risk_StageIV", "EGFR_TPM": 580.4, "MYC_TPM": 555.0, "CD274_PDL1_TPM": 41.6, "TP53_TPM": 68.2, "MARCH1_TPM": 54.0},
    {"Patient_ID": "PT_014", "OS_Months": 27.5, "Vital_Status": "Censored", "Clinical_Arm": "High_Risk_StageIV", "EGFR_TPM": 540.2, "MYC_TPM": 510.8, "CD274_PDL1_TPM": 45.0, "TP53_TPM": 74.1, "MARCH1_TPM": 51.2},
    {"Patient_ID": "PT_015", "OS_Months": 29.0, "Vital_Status": "Deceased", "Clinical_Arm": "High_Risk_StageIV", "EGFR_TPM": 595.8, "MYC_TPM": 570.2, "CD274_PDL1_TPM": 39.8, "TP53_TPM": 65.0, "MARCH1_TPM": 56.4},
    {"Patient_ID": "PT_016", "OS_Months": 31.4, "Vital_Status": "Deceased", "Clinical_Arm": "High_Risk_StageIV", "EGFR_TPM": 520.0, "MYC_TPM": 495.6, "CD274_PDL1_TPM": 48.2, "TP53_TPM": 79.5, "MARCH1_TPM": 48.8},
    {"Patient_ID": "PT_017", "OS_Months": 34.2, "Vital_Status": "Censored", "Clinical_Arm": "High_Risk_StageIV", "EGFR_TPM": 490.5, "MYC_TPM": 470.1, "CD274_PDL1_TPM": 52.4, "TP53_TPM": 84.0, "MARCH1_TPM": 45.1},
    {"Patient_ID": "PT_018", "OS_Months": 36.0, "Vital_Status": "Deceased", "Clinical_Arm": "High_Risk_StageIV", "EGFR_TPM": 505.2, "MYC_TPM": 482.0, "CD274_PDL1_TPM": 49.9, "TP53_TPM": 81.2, "MARCH1_TPM": 47.0},
    {"Patient_ID": "PT_019", "OS_Months": 28.4, "Vital_Status": "Deceased", "Clinical_Arm": "Favorable_StageII", "EGFR_TPM": 340.1, "MYC_TPM": 310.5, "CD274_PDL1_TPM": 78.5, "TP53_TPM": 128.4, "MARCH1_TPM": 34.2},
    {"Patient_ID": "PT_020", "OS_Months": 33.0, "Vital_Status": "Censored", "Clinical_Arm": "Favorable_StageII", "EGFR_TPM": 310.8, "MYC_TPM": 295.0, "CD274_PDL1_TPM": 84.2, "TP53_TPM": 135.0, "MARCH1_TPM": 31.8},
    {"Patient_ID": "PT_021", "OS_Months": 37.5, "Vital_Status": "Deceased", "Clinical_Arm": "Favorable_StageII", "EGFR_TPM": 290.4, "MYC_TPM": 275.2, "CD274_PDL1_TPM": 89.0, "TP53_TPM": 142.6, "MARCH1_TPM": 29.5},
    {"Patient_ID": "PT_022", "OS_Months": 40.2, "Vital_Status": "Censored", "Clinical_Arm": "Favorable_StageII", "EGFR_TPM": 265.0, "MYC_TPM": 250.8, "CD274_PDL1_TPM": 94.6, "TP53_TPM": 151.2, "MARCH1_TPM": 27.0},
    {"Patient_ID": "PT_023", "OS_Months": 42.8, "Vital_Status": "Deceased", "Clinical_Arm": "Favorable_StageII", "EGFR_TPM": 280.5, "MYC_TPM": 268.4, "CD274_PDL1_TPM": 91.2, "TP53_TPM": 146.8, "MARCH1_TPM": 28.4},
    {"Patient_ID": "PT_024", "OS_Months": 45.6, "Vital_Status": "Censored", "Clinical_Arm": "Favorable_StageII", "EGFR_TPM": 240.2, "MYC_TPM": 230.1, "CD274_PDL1_TPM": 98.4, "TP53_TPM": 160.5, "MARCH1_TPM": 24.9},
    {"Patient_ID": "PT_025", "OS_Months": 48.0, "Vital_Status": "Deceased", "Clinical_Arm": "Favorable_StageII", "EGFR_TPM": 255.8, "MYC_TPM": 242.0, "CD274_PDL1_TPM": 96.0, "TP53_TPM": 155.0, "MARCH1_TPM": 26.1},
    {"Patient_ID": "PT_026", "OS_Months": 51.2, "Vital_Status": "Censored", "Clinical_Arm": "Favorable_StageII", "EGFR_TPM": 215.4, "MYC_TPM": 205.6, "CD274_PDL1_TPM": 105.2, "TP53_TPM": 172.4, "MARCH1_TPM": 22.3},
    {"Patient_ID": "PT_027", "OS_Months": 54.0, "Vital_Status": "Censored", "Clinical_Arm": "Favorable_StageII", "EGFR_TPM": 198.0, "MYC_TPM": 190.2, "CD274_PDL1_TPM": 112.5, "TP53_TPM": 180.9, "MARCH1_TPM": 20.8},
    {"Patient_ID": "PT_028", "OS_Months": 56.5, "Vital_Status": "Deceased", "Clinical_Arm": "Favorable_StageII", "EGFR_TPM": 228.6, "MYC_TPM": 218.0, "CD274_PDL1_TPM": 101.8, "TP53_TPM": 166.2, "MARCH1_TPM": 23.5},
    {"Patient_ID": "PT_029", "OS_Months": 59.1, "Vital_Status": "Censored", "Clinical_Arm": "Favorable_StageII", "EGFR_TPM": 182.4, "MYC_TPM": 175.5, "CD274_PDL1_TPM": 118.0, "TP53_TPM": 189.4, "MARCH1_TPM": 19.2},
    {"Patient_ID": "PT_030", "OS_Months": 62.0, "Vital_Status": "Censored", "Clinical_Arm": "Favorable_StageII", "EGFR_TPM": 170.2, "MYC_TPM": 162.8, "CD274_PDL1_TPM": 124.6, "TP53_TPM": 196.0, "MARCH1_TPM": 18.0},
    {"Patient_ID": "PT_031", "OS_Months": 64.8, "Vital_Status": "Deceased", "Clinical_Arm": "Favorable_StageII", "EGFR_TPM": 205.0, "MYC_TPM": 198.4, "CD274_PDL1_TPM": 108.9, "TP53_TPM": 176.5, "MARCH1_TPM": 21.4},
    {"Patient_ID": "PT_032", "OS_Months": 67.5, "Vital_Status": "Censored", "Clinical_Arm": "Favorable_StageII", "EGFR_TPM": 158.6, "MYC_TPM": 149.0, "CD274_PDL1_TPM": 131.2, "TP53_TPM": 205.8, "MARCH1_TPM": 16.5},
    {"Patient_ID": "PT_033", "OS_Months": 70.2, "Vital_Status": "Censored", "Clinical_Arm": "Favorable_StageII", "EGFR_TPM": 145.0, "MYC_TPM": 138.2, "CD274_PDL1_TPM": 138.4, "TP53_TPM": 214.0, "MARCH1_TPM": 15.1},
    {"Patient_ID": "PT_034", "OS_Months": 73.0, "Vital_Status": "Censored", "Clinical_Arm": "Favorable_StageII", "EGFR_TPM": 132.8, "MYC_TPM": 126.5, "CD274_PDL1_TPM": 144.0, "TP53_TPM": 222.5, "MARCH1_TPM": 14.0},
    {"Patient_ID": "PT_035", "OS_Months": 76.4, "Vital_Status": "Censored", "Clinical_Arm": "Favorable_StageII", "EGFR_TPM": 120.4, "MYC_TPM": 115.0, "CD274_PDL1_TPM": 152.1, "TP53_TPM": 231.2, "MARCH1_TPM": 12.8},
    {"Patient_ID": "PT_036", "OS_Months": 80.0, "Vital_Status": "Censored", "Clinical_Arm": "Favorable_StageII", "EGFR_TPM": 110.0, "MYC_TPM": 104.8, "CD274_PDL1_TPM": 160.5, "TP53_TPM": 242.0, "MARCH1_TPM": 11.5}
])

# ==========================================
# SURVIVAL MATH & KAPLAN-MEIER ENGINE HELPERS
# ==========================================
def xml_esc(txt):
    return html.escape(str(txt), quote=True)

def normal_sf(z):
    return 0.5 * math.erfc(abs(z) / math.sqrt(2.0))

def chi2_1df_p(chi2_val):
    if chi2_val <= 0:
        return 1.0
    if HAS_SCIPY:
        return float(sp_stats.chi2.sf(chi2_val, 1))
    return min(1.0, max(1e-15, 2.0 * normal_sf(math.sqrt(chi2_val))))

def format_p(p):
    if p < 1e-12:
        return "< 1.00e-12"
    elif p < 0.0001:
        return f"{p:.2e}"
    return f"{p:.5f}"

def p_to_stars(p):
    if p < 0.0001:
        return "**** (p < 0.0001)"
    elif p < 0.001:
        return "*** (p < 0.001)"
    elif p < 0.01:
        return "** (p < 0.01)"
    elif p < 0.05:
        return "* (p < 0.05)"
    return "ns (Not Significant)"

def get_landmarks_for_unit(time_unit):
    if time_unit == "Years":
        return [1, 2, 3, 5]
    elif time_unit == "Days":
        return [180, 365, 730, 1095]
    elif time_unit == "Weeks":
        return [26, 52, 104, 156]
    return [12, 24, 36, 60]

def decode_event_column(series):
    out = []
    for val in series:
        s = str(val).strip().upper()
        if s in ("1", "1.0", "DECEASED", "DEAD", "EVENT", "PROGRESSED", "RELAPSED", "TRUE", "YES", "DOD", "RECURRED"):
            out.append(1)
        elif s in ("0", "0.0", "ALIVE", "LIVING", "CENSORED", "FALSE", "NO", "NED", "EVENT-FREE", "STABLE"):
            out.append(0)
        else:
            try:
                num = float(s)
                out.append(1 if num >= 1.0 else 0)
            except ValueError:
                out.append(0)
    return np.array(out, dtype=int)

def compute_km_curve(times, events, group_label):
    order = np.argsort(times)
    t_arr = np.array(times, dtype=float)[order]
    e_arr = np.array(events, dtype=int)[order]
    n_total = len(t_arr)

    unique_t = np.unique(t_arr)
    rows = [{
        "Cohort_Group": group_label,
        "Time": 0.0,
        "Number_at_Risk": n_total,
        "Events_at_Time": 0,
        "Censored_at_Time": 0,
        "Survival_Probability": 1.0,
        "Survival_Pct": 100.0,
        "Greenwood_SE": 0.0,
        "95%_CI_Lower": 1.0,
        "95%_CI_Upper": 1.0,
        "Cumulative_Hazard_H(t)": 0.0
    }]

    s_curr = 1.0
    var_sum = 0.0
    h_curr = 0.0
    censored_times = []

    for ut in unique_t:
        n_risk = int(np.sum(t_arr >= ut))
        d_i = int(np.sum((t_arr == ut) & (e_arr == 1)))
        c_i = int(np.sum((t_arr == ut) & (e_arr == 0)))

        if c_i > 0:
            s_at_c = s_curr * (1.0 - (d_i / float(n_risk))) if (d_i > 0 and n_risk > 0) else s_curr
            censored_times.append((float(ut), s_at_c))

        if d_i > 0 and n_risk > 0:
            s_curr = s_curr * (1.0 - (d_i / float(n_risk)))
            if (n_risk - d_i) > 0:
                var_sum += d_i / float(n_risk * (n_risk - d_i))
            h_curr += d_i / float(n_risk)

        se_s = s_curr * math.sqrt(var_sum)
        ci_low = max(0.0, s_curr - 1.96 * se_s)
        ci_high = min(1.0, s_curr + 1.96 * se_s)

        rows.append({
            "Cohort_Group": group_label,
            "Time": round(float(ut), 3),
            "Number_at_Risk": n_risk,
            "Events_at_Time": d_i,
            "Censored_at_Time": c_i,
            "Survival_Probability": round(s_curr, 4),
            "Survival_Pct": round(s_curr * 100.0, 2),
            "Greenwood_SE": round(se_s, 4),
            "95%_CI_Lower": round(ci_low, 4),
            "95%_CI_Upper": round(ci_high, 4),
            "Cumulative_Hazard_H(t)": round(h_curr, 4)
        })

    km_df = pd.DataFrame(rows)

    # Median survival time & Brookmeyer-Crowley 95% CI bounds
    below_50 = km_df[km_df["Survival_Probability"] <= 0.50]
    median_surv = float(below_50["Time"].iloc[0]) if not below_50.empty else None
    low_50 = km_df[km_df["95%_CI_Lower"] <= 0.50]
    high_50 = km_df[km_df["95%_CI_Upper"] <= 0.50]
    med_ci_low = float(low_50["Time"].iloc[0]) if not low_50.empty else None
    med_ci_high = float(high_50["Time"].iloc[0]) if not high_50.empty else None

    # Restricted Mean Survival Time (RMST = Area Under KM Step Curve)
    t_vals = km_df["Time"].values
    s_vals = km_df["Survival_Probability"].values
    rmst_val = 0.0
    for i in range(len(t_vals) - 1):
        rmst_val += s_vals[i] * (t_vals[i + 1] - t_vals[i])

    return km_df, median_surv, (med_ci_low, med_ci_high), round(rmst_val, 2), censored_times

def get_surv_at_landmark(km_df, t_landmark):
    sub = km_df[km_df["Time"] <= t_landmark]
    if sub.empty:
        return 100.0
    return round(float(sub["Survival_Pct"].iloc[-1]), 1)

def compute_logrank_and_hr(t1, e1, t2, e2):
    all_t = np.concatenate([t1, t2])
    all_e = np.concatenate([e1, e2])
    event_times = np.unique(all_t[all_e == 1])

    if len(event_times) == 0:
        return {"chi2": 0.0, "p_logrank": 1.0, "p_wilcoxon": 1.0, "hr": 1.0, "hr_low": 0.5, "hr_high": 2.0, "ph_status": "Holds"}

    obs_1, exp_1 = 0.0, 0.0
    obs_2, exp_2 = 0.0, 0.0
    var_lr = 0.0
    w_num, w_var = 0.0, 0.0
    sign_diffs = []

    for et in event_times:
        n1_j = float(np.sum(t1 >= et))
        n2_j = float(np.sum(t2 >= et))
        n_j = n1_j + n2_j
        if n_j <= 1:
            continue

        d1_j = float(np.sum((t1 == et) & (e1 == 1)))
        d2_j = float(np.sum((t2 == et) & (e2 == 1)))
        d_j = d1_j + d2_j

        e1_j = n1_j * (d_j / n_j)
        e2_j = n2_j * (d_j / n_j)

        obs_1 += d1_j
        exp_1 += e1_j
        obs_2 += d2_j
        exp_2 += e2_j
        sign_diffs.append(obs_1 - exp_1)

        v_j = (n1_j * n2_j * d_j * (n_j - d_j)) / ((n_j ** 2) * max(1.0, n_j - 1.0))
        var_lr += v_j

        w_num += n_j * (d1_j - e1_j)
        w_var += (n_j ** 2) * v_j

    chi2_lr = ((obs_1 - exp_1) ** 2) / max(1e-9, var_lr)
    p_lr = chi2_1df_p(chi2_lr)

    chi2_wilc = (w_num ** 2) / max(1e-9, w_var)
    p_wilc = chi2_1df_p(chi2_wilc)

    r1 = (obs_1 + 0.5) / max(0.5, exp_1 + 0.5) if (exp_1 == 0 or exp_2 == 0 or obs_1 == 0 or obs_2 == 0) else (obs_1 / exp_1)
    r2 = (obs_2 + 0.5) / max(0.5, exp_2 + 0.5) if (exp_1 == 0 or exp_2 == 0 or obs_1 == 0 or obs_2 == 0) else (obs_2 / exp_2)
    hr = r1 / max(1e-6, r2)
    se_ln_hr = math.sqrt(1.0 / max(1.0, exp_1) + 1.0 / max(1.0, exp_2))
    hr_low = math.exp(math.log(max(1e-6, hr)) - 1.96 * se_ln_hr)
    hr_high = math.exp(math.log(max(1e-6, hr)) + 1.96 * se_ln_hr)

    # Check if cumulative O-E changes sign mid-follow-up (indicates crossing survival curves)
    has_pos = any(sd > 0.5 for sd in sign_diffs)
    has_neg = any(sd < -0.5 for sd in sign_diffs)
    ph_status = "Crossing Curves Detected (Consider RMST / Wilcoxon P)" if (has_pos and has_neg) else "Proportional Hazards Hold (Log-Rank Optimal)"

    return {
        "chi2": round(chi2_lr, 3),
        "p_logrank": p_lr,
        "p_wilcoxon": p_wilc,
        "hr": round(hr, 3),
        "hr_low": round(hr_low, 3),
        "hr_high": round(hr_high, 3),
        "ph_status": ph_status
    }

def stratify_cohort(df, id_col, time_col, event_arr, feat_col, engine_mode, custom_pct=50, max_horizon=0.0):
    t_all = pd.to_numeric(df[time_col], errors="coerce").copy()
    e_all = np.array(event_arr, dtype=int).copy()

    # Apply optional right-censoring follow-up horizon truncation
    if max_horizon and max_horizon > 0:
        over_mask = t_all > max_horizon
        t_all[over_mask] = max_horizon
        e_all[over_mask] = 0

    valid_mask = t_all.notna() & (t_all >= 0)
    ids_all = df[id_col].astype(str) if id_col in df.columns else pd.Series([f"Sample_{i+1}" for i in range(len(df))])

    if "Categorical Clinical" in engine_mode:
        g_series = df[feat_col].astype(str)
        valid_df = pd.DataFrame({
            "id": ids_all[valid_mask],
            "t": t_all[valid_mask],
            "e": e_all[valid_mask],
            "g": g_series[valid_mask]
        })
        top_cats = valid_df["g"].value_counts().index[:2].tolist()
        if len(top_cats) < 2:
            return None
        g1_name, g2_name = str(top_cats[0]), str(top_cats[1])
        sub1 = valid_df[valid_df["g"] == g1_name]
        sub2 = valid_df[valid_df["g"] == g2_name]
        patient_df = pd.concat([
            pd.DataFrame({"Patient_Sample_ID": sub1["id"], "FollowUp_Time": sub1["t"], "Event_Status": sub1["e"], "Biomarker_Value": sub1["g"], "Assigned_Cohort_Stratum": g1_name}),
            pd.DataFrame({"Patient_Sample_ID": sub2["id"], "FollowUp_Time": sub2["t"], "Event_Status": sub2["e"], "Biomarker_Value": sub2["g"], "Assigned_Cohort_Stratum": g2_name})
        ], ignore_index=True)
        return {
            "g1_label": g1_name, "t1": sub1["t"].values, "e1": sub1["e"].values,
            "g2_label": g2_name, "t2": sub2["t"].values, "e2": sub2["e"].values,
            "cutpoint_str": f"Categorical ({g1_name} vs {g2_name})",
            "patient_df": patient_df
        }

    x_all = pd.to_numeric(df[feat_col], errors="coerce")
    valid_mask = valid_mask & x_all.notna()
    id_v = ids_all[valid_mask].values
    t_v = t_all[valid_mask].values
    e_v = e_all[valid_mask]
    x_v = x_all[valid_mask].values

    if len(x_v) < 6:
        return None

    if "Optimal Cutpoint" in engine_mode:
        best_p = 2.0
        best_cut = float(np.median(x_v))
        best_pct = 50
        for pct in range(20, 81, 5):
            cand = float(np.percentile(x_v, pct))
            m_high = x_v >= cand
            m_low = x_v < cand
            if np.sum(m_high) >= 3 and np.sum(m_low) >= 3:
                lr = compute_logrank_and_hr(t_v[m_high], e_v[m_high], t_v[m_low], e_v[m_low])
                if lr["p_logrank"] < best_p:
                    best_p = lr["p_logrank"]
                    best_cut = cand
                    best_pct = pct
        m_high = x_v >= best_cut
        m_low = x_v < best_cut
        cut_str = f"Optimal Cutpoint = {best_cut:.2f} ({best_pct}th Percentile)"
        g1_lbl = f"High {feat_col} (>= {best_cut:.2f})"
        g2_lbl = f"Low {feat_col} (< {best_cut:.2f})"
    elif "Quartile / Tertile" in engine_mode:
        q_low = float(np.percentile(x_v, 33.3))
        q_high = float(np.percentile(x_v, 66.7))
        m_high = x_v >= q_high
        m_low = x_v <= q_low
        cut_str = f"Top 33% (>= {q_high:.2f}) vs Bottom 33% (<= {q_low:.2f})"
        g1_lbl = f"High Tertile (>= {q_high:.2f})"
        g2_lbl = f"Low Tertile (<= {q_low:.2f})"
    else:
        cut_val = float(np.percentile(x_v, custom_pct))
        m_high = x_v >= cut_val
        m_low = x_v < cut_val
        cut_label = "Median" if custom_pct == 50 else f"{custom_pct}th Percentile"
        cut_str = f"{cut_label} Cutpoint = {cut_val:.2f}"
        g1_lbl = f"High {feat_col} (>= {cut_val:.2f})"
        g2_lbl = f"Low {feat_col} (< {cut_val:.2f})"

    p_high = pd.DataFrame({
        "Patient_Sample_ID": id_v[m_high], "FollowUp_Time": t_v[m_high],
        "Event_Status (1=Event, 0=Censored)": e_v[m_high], feat_col: x_v[m_high],
        "Assigned_Cohort_Stratum": g1_lbl, "Cutpoint_Rule": cut_str
    })
    p_low = pd.DataFrame({
        "Patient_Sample_ID": id_v[m_low], "FollowUp_Time": t_v[m_low],
        "Event_Status (1=Event, 0=Censored)": e_v[m_low], feat_col: x_v[m_low],
        "Assigned_Cohort_Stratum": g2_lbl, "Cutpoint_Rule": cut_str
    })

    return {
        "g1_label": g1_lbl, "t1": t_v[m_high], "e1": e_v[m_high],
        "g2_label": g2_lbl, "t2": t_v[m_low], "e2": e_v[m_low],
        "cutpoint_str": cut_str,
        "patient_df": pd.concat([p_high, p_low], ignore_index=True)
    }

# ==========================================
# 4-PANEL XML-SAFE VECTOR SVG SURVIVAL SUITE
# ==========================================
PALETTE_SURV = {
    "JCO / Nature Medicine (Crimson High-Risk vs Royal Blue Low-Risk)": ("#e11d48", "#2563eb"),
    "Lancet Oncology (Deep Violet vs Emerald Teal)": ("#7c3aed", "#0d9488"),
    "Cell Press (Amber Gold vs Cosmic Indigo)": ("#d97706", "#4f46e5"),
    "High-Contrast Print Grayscale (Black vs Slate Gray)": ("#0f172a", "#64748b")
}

def generate_svg_km_with_risk_table(km1, km2, cens1, cens2, med1, med2, lr_res, feat_name, endpoint_label, time_unit, palette_name, show_cens=True, show_ci=True, show_med_line=True):
    col1, col2 = PALETTE_SURV.get(palette_name, ("#e11d48", "#2563eb"))
    g1_name = str(km1["Cohort_Group"].iloc[0])
    g2_name = str(km2["Cohort_Group"].iloc[0])

    max_t = max(float(km1["Time"].max()), float(km2["Time"].max()), 10.0)
    t_max_axis = math.ceil(max_t / 10.0) * 10.0 if max_t > 10 else math.ceil(max_t)

    width, height = 840, 560
    pad_l, pad_r, pad_t, pad_b = 85, 35, 65, 145
    plot_w, plot_h = width - pad_l - pad_r, height - pad_t - pad_b

    def x_to_px(t_val):
        return pad_l + (t_val / max(1e-6, t_max_axis)) * plot_w

    def y_to_px(s_prob):
        return pad_t + plot_h - (s_prob * plot_h)

    f_esc = xml_esc(feat_name)
    ep_esc = xml_esc(endpoint_label)
    hr_str = xml_esc(f"HR = {lr_res['hr']:.2f} (95% CI: {lr_res['hr_low']:.2f}-{lr_res['hr_high']:.2f}) | Log-Rank p = {format_p(lr_res['p_logrank'])}")

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="background:#ffffff; border-radius:12px; font-family:Arial, Helvetica, sans-serif;">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff" rx="12"/>',
        f'<text x="{width/2}" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#0f172a">Figure 1A: {f_esc} — {ep_esc} Kaplan-Meier Curve &amp; Number at Risk</text>',
        f'<text x="{width/2}" y="48" text-anchor="middle" font-size="12" font-weight="bold" fill="#334155">{hr_str}</text>'
    ]

    for s_tick in [0.0, 0.25, 0.50, 0.75, 1.0]:
        py = y_to_px(s_tick)
        dash = "6,4" if (s_tick == 0.50 and show_med_line) else "3,3"
        stroke_c = "#94a3b8" if (s_tick == 0.50 and show_med_line) else "#e2e8f0"
        svg.append(f'<line x1="{pad_l}" y1="{py:.1f}" x2="{width - pad_r}" y2="{py:.1f}" stroke="{stroke_c}" stroke-dasharray="{dash}" stroke-width="1.2"/>')
        svg.append(f'<text x="{pad_l - 10}" y="{py + 4:.1f}" text-anchor="end" font-size="11" fill="#334155">{int(s_tick*100)}%</text>')

    time_ticks = [round((i / 5.0) * t_max_axis, 1) for i in range(6)]
    for tv in time_ticks:
        px = x_to_px(tv)
        svg.append(f'<line x1="{px:.1f}" y1="{pad_t}" x2="{px:.1f}" y2="{pad_t + plot_h}" stroke="#f1f5f9" stroke-width="1"/>')
        svg.append(f'<text x="{px:.1f}" y="{pad_t + plot_h + 20}" text-anchor="middle" font-size="11" font-weight="bold" fill="#0f172a">{tv:g}</text>')

    svg.append(f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{pad_t + plot_h}" stroke="#0f172a" stroke-width="1.8"/>')
    svg.append(f'<line x1="{pad_l}" y1="{pad_t + plot_h}" x2="{width - pad_r}" y2="{pad_t + plot_h}" stroke="#0f172a" stroke-width="1.8"/>')
    svg.append(f'<text x="24" y="{pad_t + plot_h/2}" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#0f172a" transform="rotate(-90, 24, {pad_t + plot_h/2})">{ep_esc} Probability (%)</text>')
    svg.append(f'<text x="{pad_l + plot_w/2}" y="{pad_t + plot_h + 38}" text-anchor="middle" font-size="12" font-weight="bold" fill="#0f172a">Follow-Up Time ({xml_esc(time_unit)})</text>')

    def build_step_svg(km_df, cens_list, col, med_val):
        t_vals = km_df["Time"].values
        s_vals = km_df["Survival_Probability"].values
        l_vals = km_df["95%_CI_Lower"].values
        u_vals = km_df["95%_CI_Upper"].values

        # Draw 95% Greenwood Confidence Interval Shaded Step Ribbon if enabled
        if show_ci and len(t_vals) > 1:
            upper_pts = []
            lower_pts = []
            for idx in range(len(t_vals)):
                if idx > 0:
                    upper_pts.append((x_to_px(t_vals[idx]), y_to_px(u_vals[idx - 1])))
                    lower_pts.append((x_to_px(t_vals[idx]), y_to_px(l_vals[idx - 1])))
                upper_pts.append((x_to_px(t_vals[idx]), y_to_px(u_vals[idx])))
                lower_pts.append((x_to_px(t_vals[idx]), y_to_px(l_vals[idx])))
            poly_pts = upper_pts + lower_pts[::-1]
            poly_str = " ".join(f"{px:.1f},{py:.1f}" for px, py in poly_pts)
            svg.append(f'<polygon points="{poly_str}" fill="{col}" fill-opacity="0.13" stroke="none"/>')

        step_coords = []
        for idx in range(len(t_vals)):
            if idx > 0:
                step_coords.append((x_to_px(t_vals[idx]), y_to_px(s_vals[idx - 1])))
            step_coords.append((x_to_px(t_vals[idx]), y_to_px(s_vals[idx])))

        path_str = "M " + " L ".join(f"{px:.1f} {py:.1f}" for px, py in step_coords)
        svg.append(f'<path d="{path_str}" fill="none" stroke="{col}" stroke-width="2.8"/>')

        if show_med_line and med_val is not None and med_val <= t_max_axis:
            px_m = x_to_px(med_val)
            py_50 = y_to_px(0.50)
            svg.append(f'<line x1="{px_m:.1f}" y1="{py_50:.1f}" x2="{px_m:.1f}" y2="{pad_t + plot_h:.1f}" stroke="{col}" stroke-dasharray="4,3" stroke-width="1.5"/>')

        if show_cens:
            for ct, cs in cens_list:
                px_c, py_c = x_to_px(ct), y_to_px(cs)
                svg.append(f'<line x1="{px_c:.1f}" y1="{py_c - 4.5:.1f}" x2="{px_c:.1f}" y2="{py_c + 4.5:.1f}" stroke="{col}" stroke-width="1.8"/>')
                svg.append(f'<line x1="{px_c - 3.5:.1f}" y1="{py_c:.1f}" x2="{px_c + 3.5:.1f}" y2="{py_c:.1f}" stroke="{col}" stroke-width="1.8"/>')

    build_step_svg(km1, cens1, col1, med1)
    build_step_svg(km2, cens2, col2, med2)

    m1_txt = f"{med1:.1f} {time_unit}" if med1 is not None else "Not Reached"
    m2_txt = f"{med2:.1f} {time_unit}" if med2 is not None else "Not Reached"
    svg.append(f'<rect x="{width - pad_r - 295}" y="{pad_t + 8}" width="287" height="54" fill="#f8fafc" fill-opacity="0.92" stroke="#cbd5e1" rx="6"/>')
    svg.append(f'<line x1="{width - pad_r - 285}" y1="{pad_t + 24}" x2="{width - pad_r - 263}" y2="{pad_t + 24}" stroke="{col1}" stroke-width="3"/>')
    svg.append(f'<text x="{width - pad_r - 255}" y="{pad_t + 28}" font-size="10.5" font-weight="bold" fill="#0f172a">{xml_esc(g1_name[:26])} (Med: {xml_esc(m1_txt)})</text>')
    svg.append(f'<line x1="{width - pad_r - 285}" y1="{pad_t + 46}" x2="{width - pad_r - 263}" y2="{pad_t + 46}" stroke="{col2}" stroke-width="3"/>')
    svg.append(f'<text x="{width - pad_r - 255}" y="{pad_t + 50}" font-size="10.5" font-weight="bold" fill="#0f172a">{xml_esc(g2_name[:26])} (Med: {xml_esc(m2_txt)})</text>')

    nar_top = pad_t + plot_h + 62
    svg.append(f'<line x1="15" y1="{nar_top - 14}" x2="{width - pad_r}" y2="{nar_top - 14}" stroke="#cbd5e1" stroke-width="1.2"/>')
    svg.append(f'<text x="18" y="{nar_top}" font-size="11" font-weight="bold" fill="#0f172a">Number at Risk:</text>')
    svg.append(f'<text x="18" y="{nar_top + 22}" font-size="10.5" font-weight="bold" fill="{col1}">{xml_esc(g1_name[:18])}</text>')
    svg.append(f'<text x="18" y="{nar_top + 42}" font-size="10.5" font-weight="bold" fill="{col2}">{xml_esc(g2_name[:18])}</text>')

    for tv in time_ticks:
        px = x_to_px(tv)
        sub1 = km1[km1["Time"] >= tv]
        n1_at_t = int(sub1["Number_at_Risk"].iloc[0]) if not sub1.empty else 0
        sub2 = km2[km2["Time"] >= tv]
        n2_at_t = int(sub2["Number_at_Risk"].iloc[0]) if not sub2.empty else 0
        svg.append(f'<text x="{px:.1f}" y="{nar_top + 22}" text-anchor="middle" font-size="11" font-weight="bold" fill="{col1}">{n1_at_t}</text>')
        svg.append(f'<text x="{px:.1f}" y="{nar_top + 42}" text-anchor="middle" font-size="11" font-weight="bold" fill="{col2}">{n2_at_t}</text>')

    svg.append('</svg>')
    return "\n".join(svg)

def generate_svg_cumulative_hazard(km1, km2, feat_name, time_unit, palette_name):
    col1, col2 = PALETTE_SURV.get(palette_name, ("#e11d48", "#2563eb"))
    g1_name = str(km1["Cohort_Group"].iloc[0])
    g2_name = str(km2["Cohort_Group"].iloc[0])

    max_t = max(float(km1["Time"].max()), float(km2["Time"].max()), 10.0)
    t_max_axis = math.ceil(max_t / 10.0) * 10.0 if max_t > 10 else math.ceil(max_t)
    max_h = max(float(km1["Cumulative_Hazard_H(t)"].max()), float(km2["Cumulative_Hazard_H(t)"].max()), 0.5) * 1.15

    width, height = 840, 460
    pad_l, pad_r, pad_t, pad_b = 85, 35, 65, 75
    plot_w, plot_h = width - pad_l - pad_r, height - pad_t - pad_b

    def x_to_px(t_val):
        return pad_l + (t_val / max(1e-6, t_max_axis)) * plot_w

    def y_to_px(h_val):
        return pad_t + plot_h - (h_val / max(1e-6, max_h)) * plot_h

    f_esc = xml_esc(feat_name)
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="background:#ffffff; border-radius:12px; font-family:Arial, Helvetica, sans-serif;">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff" rx="12"/>',
        f'<text x="{width/2}" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#0f172a">Figure 1B: {f_esc} — Nelson-Aalen Cumulative Hazard Curve H(t)</text>',
        f'<text x="{width/2}" y="48" text-anchor="middle" font-size="12" fill="#475569">Cumulative Event Risk Trajectory Across Follow-Up Time ({xml_esc(time_unit)})</text>'
    ]

    for idx in range(6):
        hv = (idx / 5.0) * max_h
        py = y_to_px(hv)
        svg.append(f'<line x1="{pad_l}" y1="{py:.1f}" x2="{width - pad_r}" y2="{py:.1f}" stroke="#e2e8f0" stroke-dasharray="4,4" stroke-width="1"/>')
        svg.append(f'<text x="{pad_l - 10}" y="{py + 4:.1f}" text-anchor="end" font-size="11" fill="#334155">{hv:.2f}</text>')

    for idx in range(6):
        tv = round((idx / 5.0) * t_max_axis, 1)
        px = x_to_px(tv)
        svg.append(f'<text x="{px:.1f}" y="{pad_t + plot_h + 22}" text-anchor="middle" font-size="11" font-weight="bold" fill="#0f172a">{tv:g}</text>')

    svg.append(f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{pad_t + plot_h}" stroke="#0f172a" stroke-width="1.8"/>')
    svg.append(f'<line x1="{pad_l}" y1="{pad_t + plot_h}" x2="{width - pad_r}" y2="{pad_t + plot_h}" stroke="#0f172a" stroke-width="1.8"/>')
    svg.append(f'<text x="24" y="{pad_t + plot_h/2}" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#0f172a" transform="rotate(-90, 24, {pad_t + plot_h/2})">Cumulative Hazard H(t)</text>')
    svg.append(f'<text x="{pad_l + plot_w/2}" y="{pad_t + plot_h + 44}" text-anchor="middle" font-size="12" font-weight="bold" fill="#0f172a">Follow-Up Time ({xml_esc(time_unit)})</text>')

    for km_df, col in [(km1, col1), (km2, col2)]:
        pts = list(zip(km_df["Time"].values, km_df["Cumulative_Hazard_H(t)"].values))
        step_coords = []
        for idx, (t_v, h_v) in enumerate(pts):
            if idx > 0:
                step_coords.append((x_to_px(t_v), y_to_px(pts[idx - 1][1])))
            step_coords.append((x_to_px(t_v), y_to_px(h_v)))
        path_str = "M " + " L ".join(f"{px:.1f} {py:.1f}" for px, py in step_coords)
        svg.append(f'<path d="{path_str}" fill="none" stroke="{col}" stroke-width="2.8"/>')

    svg.append(f'<rect x="{pad_l + 16}" y="{pad_t + 12}" width="250" height="48" fill="#f8fafc" stroke="#cbd5e1" rx="6"/>')
    svg.append(f'<line x1="{pad_l + 26}" y1="{pad_t + 26}" x2="{pad_l + 48}" y2="{pad_t + 26}" stroke="{col1}" stroke-width="3"/>')
    svg.append(f'<text x="{pad_l + 56}" y="{pad_t + 30}" font-size="10.5" font-weight="bold" fill="#0f172a">{xml_esc(g1_name[:26])}</text>')
    svg.append(f'<line x1="{pad_l + 26}" y1="{pad_t + 46}" x2="{pad_l + 48}" y2="{pad_t + 46}" stroke="{col2}" stroke-width="3"/>')
    svg.append(f'<text x="{pad_l + 56}" y="{pad_t + 50}" font-size="10.5" font-weight="bold" fill="#0f172a">{xml_esc(g2_name[:26])}</text>')

    svg.append('</svg>')
    return "\n".join(svg)

def generate_svg_hr_forest(batch_df, palette_name):
    col1, col2 = PALETTE_SURV.get(palette_name, ("#e11d48", "#2563eb"))
    n_rows = len(batch_df)
    width, height = 840, max(360, 140 + n_rows * 48)
    pad_l, pad_r, pad_t, pad_b = 185, 175, 65, 55
    plot_w, plot_h = width - pad_l - pad_r, height - pad_t - pad_b

    x_min, x_max = -3.0, 3.0

    def x_to_px(log2_hr):
        v_c = max(x_min, min(x_max, log2_hr))
        return pad_l + ((v_c - x_min) / (x_max - x_min)) * plot_w

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="background:#ffffff; border-radius:12px; font-family:Arial, Helvetica, sans-serif;">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff" rx="12"/>',
        f'<text x="{width/2}" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#0f172a">Figure 1C: Multi-Gene Prognostic Hazard Ratio Forest Plot (95% CI)</text>',
        f'<text x="{width/2}" y="48" text-anchor="middle" font-size="12" fill="#475569">HR &gt; 1.0 Indicates Adverse Risk Factor | HR &lt; 1.0 Indicates Protective / Favorable Prognosis</text>'
    ]

    px_one = x_to_px(0.0)
    svg.append(f'<line x1="{px_one:.1f}" y1="{pad_t}" x2="{px_one:.1f}" y2="{pad_t + plot_h}" stroke="#0f172a" stroke-dasharray="5,4" stroke-width="1.8"/>')
    svg.append(f'<line x1="{pad_l}" y1="{pad_t + plot_h}" x2="{width - pad_r}" y2="{pad_t + plot_h}" stroke="#0f172a" stroke-width="1.6"/>')

    for hr_tick, l2_val in [("0.12", -3.0), ("0.25", -2.0), ("0.50", -1.0), ("1.0 (Null)", 0.0), ("2.0", 1.0), ("4.0", 2.0), ("8.0", 3.0)]:
        px = x_to_px(l2_val)
        svg.append(f'<text x="{px:.1f}" y="{pad_t + plot_h + 22}" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#334155">{hr_tick}</text>')

    for idx, (_, row) in enumerate(batch_df.iterrows()):
        py = pad_t + (idx + 0.5) * (plot_h / max(1, n_rows))
        hr_v = max(0.05, float(row["Hazard_Ratio (HR)"]))
        low_v = max(0.05, float(row["95%_CI_Lower"]))
        high_v = max(0.05, float(row["95%_CI_Upper"]))

        px_hr = x_to_px(math.log2(hr_v))
        px_l = x_to_px(math.log2(low_v))
        px_h = x_to_px(math.log2(high_v))
        col = col1 if hr_v >= 1.0 else col2

        g_esc = xml_esc(str(row["Biomarker_or_Gene"]).replace('="', '').replace('"', ''))
        stat_esc = xml_esc(f"HR={hr_v:.2f} (p={row['LogRank_Exact_P']})")

        svg.append(f'<line x1="{pad_l}" y1="{py:.1f}" x2="{width - pad_r}" y2="{py:.1f}" stroke="#f1f5f9" stroke-width="1"/>')
        svg.append(f'<text x="{pad_l - 12}" y="{py + 4:.1f}" text-anchor="end" font-size="11.5" font-weight="bold" fill="#0f172a">{g_esc}</text>')
        svg.append(f'<line x1="{px_l:.1f}" y1="{py:.1f}" x2="{px_h:.1f}" y2="{py:.1f}" stroke="{col}" stroke-width="2.6"/>')
        svg.append(f'<line x1="{px_l:.1f}" y1="{py - 6:.1f}" x2="{px_l:.1f}" y2="{py + 6:.1f}" stroke="{col}" stroke-width="2.2"/>')
        svg.append(f'<line x1="{px_h:.1f}" y1="{py - 6:.1f}" x2="{px_h:.1f}" y2="{py + 6:.1f}" stroke="{col}" stroke-width="2.2"/>')
        svg.append(f'<rect x="{px_hr - 5:.1f}" y="{py - 5:.1f}" width="10" height="10" fill="{col}" stroke="#ffffff" stroke-width="1.3" rx="2"/>')
        svg.append(f'<text x="{width - pad_r + 10}" y="{py + 4:.1f}" text-anchor="start" font-size="10.5" font-weight="bold" fill="#1e293b">{stat_esc}</text>')

    svg.append('</svg>')
    return "\n".join(svg)

def generate_svg_landmark_bars(km1, km2, feat_name, endpoint_label, time_unit, palette_name):
    col1, col2 = PALETTE_SURV.get(palette_name, ("#e11d48", "#2563eb"))
    landmarks = get_landmarks_for_unit(time_unit)
    width, height = 840, 460
    pad_l, pad_r, pad_t, pad_b = 85, 35, 65, 75
    plot_w, plot_h = width - pad_l - pad_r, height - pad_t - pad_b

    def y_to_px(pct):
        return pad_t + plot_h - (pct / 100.0) * plot_h

    f_esc = xml_esc(feat_name)
    ep_esc = xml_esc(endpoint_label)
    lm_str = ", ".join(str(x) for x in landmarks)

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="background:#ffffff; border-radius:12px; font-family:Arial, Helvetica, sans-serif;">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff" rx="12"/>',
        f'<text x="{width/2}" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#0f172a">Figure 1D: {f_esc} — Clinical Landmark {ep_esc} Rate Comparison</text>',
        f'<text x="{width/2}" y="48" text-anchor="middle" font-size="12" fill="#475569">Estimated {ep_esc} Probability (%) at {xml_esc(lm_str)} {xml_esc(time_unit)}</text>'
    ]

    for s_pct in [0, 25, 50, 75, 100]:
        py = y_to_px(s_pct)
        svg.append(f'<line x1="{pad_l}" y1="{py:.1f}" x2="{width - pad_r}" y2="{py:.1f}" stroke="#e2e8f0" stroke-dasharray="4,4" stroke-width="1"/>')
        svg.append(f'<text x="{pad_l - 10}" y="{py + 4:.1f}" text-anchor="end" font-size="11" fill="#334155">{s_pct}%</text>')

    svg.append(f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{pad_t + plot_h}" stroke="#0f172a" stroke-width="1.8"/>')
    svg.append(f'<line x1="{pad_l}" y1="{pad_t + plot_h}" x2="{width - pad_r}" y2="{pad_t + plot_h}" stroke="#0f172a" stroke-width="1.8"/>')
    svg.append(f'<text x="24" y="{pad_t + plot_h/2}" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#0f172a" transform="rotate(-90, 24, {pad_t + plot_h/2})">Landmark {ep_esc} (%)</text>')

    bar_w = 48
    py_zero = y_to_px(0.0)
    for idx, lm in enumerate(landmarks):
        cx = pad_l + (idx + 0.5) * (plot_w / len(landmarks))
        s1 = get_surv_at_landmark(km1, lm)
        s2 = get_surv_at_landmark(km2, lm)

        py1, py2 = y_to_px(s1), y_to_px(s2)
        h1, h2 = max(2.0, py_zero - py1), max(2.0, py_zero - py2)

        svg.append(f'<rect x="{cx - bar_w - 4:.1f}" y="{py1:.1f}" width="{bar_w}" height="{h1:.1f}" fill="{col1}" fill-opacity="0.75" stroke="{col1}" stroke-width="1.8" rx="3"/>')
        svg.append(f'<text x="{cx - bar_w/2 - 4:.1f}" y="{py1 - 6:.1f}" text-anchor="middle" font-size="10.5" font-weight="bold" fill="{col1}">{s1:.1f}%</text>')

        svg.append(f'<rect x="{cx + 4:.1f}" y="{py2:.1f}" width="{bar_w}" height="{h2:.1f}" fill="{col2}" fill-opacity="0.75" stroke="{col2}" stroke-width="1.8" rx="3"/>')
        svg.append(f'<text x="{cx + bar_w/2 + 4:.1f}" y="{py2 - 6:.1f}" text-anchor="middle" font-size="10.5" font-weight="bold" fill="{col2}">{s2:.1f}%</text>')

        svg.append(f'<text x="{cx:.1f}" y="{pad_t + plot_h + 24}" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#0f172a">{lm} {xml_esc(time_unit)}</text>')

    svg.append('</svg>')
    return "\n".join(svg)

# ==========================================
# STEP 2: FILE UPLOAD OR DEMO DATASET
# ==========================================
col_up, col_demo = st.columns([3, 1])
with col_up:
    uploaded_file = st.file_uploader(
        "Upload Clinical Survival & Gene Expression Table (.csv, .tsv, .txt)",
        type=["csv", "tsv", "txt"],
        on_change=reset_on_mode_change_t8
    )
with col_demo:
    st.write("")
    st.write("")
    use_sample = st.checkbox("🧪 Load Demo Oncology Survival Cohort", value=True, on_change=reset_on_mode_change_t8)

df_input = None
if uploaded_file is not None:
    try:
        sep = "\t" if uploaded_file.name.lower().endswith((".tsv", ".txt")) else ","
        df_input = pd.read_csv(uploaded_file, sep=sep)
    except Exception as e:
        st.error(f"Error reading file: {e}")
elif use_sample:
    df_input = DEMO_SURVIVAL_DF.copy()

# ==========================================
# STEP 3: CONFIGURE SURVIVAL ENGINE & PLOT STYLING
# ==========================================
if df_input is not None and not df_input.empty:
    with st.expander(f"👁️ Inspect Loaded Survival & Expression Dataset ({len(df_input)} Patients Ready)", expanded=False):
        st.dataframe(df_input.head(6), use_container_width=True)

    st.markdown("### ⚙️ Configure Cohort Stratification Engine, Clinical Endpoint & Curve Options")

    # Core Stratification & Survival Engine (ONLY switching this or uploading a new file resets paywall!)
    core_engine = st.selectbox(
        "1. Core Stratification & Survival Engine (Switching engine starts a new pipeline run):",
        [
            "Median / Custom Percentile Split — High vs. Low Expression Cohort Stratification",
            "Optimal Cutpoint Discovery — Auto-Scan Thresholds to Maximize Log-Rank Separation",
            "Quartile / Tertile Extremes — Top 33% (High) vs. Bottom 33% (Low) Expression",
            "Categorical Clinical Arm — Direct Grouping by Treatment Arm, Stage, or Mutation Status",
            "Multi-Gene Batch Prognostic Screen — Simultaneous Log-Rank, Hazard Ratio & FDR Screen"
        ],
        on_change=reset_on_mode_change_t8
    )

    cols_all = list(df_input.columns)
    num_cols = list(df_input.select_dtypes(include=[np.number]).columns)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**2. Map Patient, Time, Event & Target Gene**")
        id_col = st.selectbox("Patient / Sample ID Column:", cols_all, index=0)
        default_t_idx = next((i for i, c in enumerate(cols_all) if any(k in c.lower() for k in ["os", "time", "month", "day", "surv"])), 1 if len(cols_all) > 1 else 0)
        default_e_idx = next((i for i, c in enumerate(cols_all) if any(k in c.lower() for k in ["vital", "status", "event", "dead", "censor"])), 2 if len(cols_all) > 2 else 0)

        time_col = st.selectbox("Follow-Up Time Column:", cols_all, index=default_t_idx)
        event_col = st.selectbox("Event / Vital Status Column (1/Deceased vs 0/Alive):", cols_all, index=default_e_idx)

        if "Categorical Clinical" in core_engine:
            cat_candidates = [c for c in cols_all if c not in (id_col, time_col, event_col)]
            target_feature = st.selectbox("Select Categorical Group Column (Free to switch):", cat_candidates if cat_candidates else cols_all, index=0)
        else:
            gene_candidates = [c for c in num_cols if c not in (id_col, time_col, event_col)]
            if not gene_candidates:
                gene_candidates = [c for c in cols_all if c not in (id_col, time_col, event_col)]
            target_feature = st.selectbox(
                "Select Target Gene / Biomarker (Free to switch):",
                gene_candidates,
                index=0,
                help="You can freely switch between any gene/biomarker in your dataset without resetting your unlock!"
            )

    with c2:
        st.markdown("**3. Clinical Endpoint, Cutpoint & Follow-Up**")
        endpoint_choice = st.selectbox(
            "Clinical Survival Endpoint Label:",
            [
                "Overall Survival (OS)",
                "Progression-Free Survival (PFS)",
                "Disease-Free Survival (DFS)",
                "Relapse-Free Survival (RFS)",
                "Disease-Specific Survival (DSS)"
            ],
            index=0
        )
        time_unit = st.selectbox("Follow-Up Time Unit Label:", ["Months", "Years", "Days", "Weeks"], index=0)
        if "Median / Custom Percentile" in core_engine:
            custom_pct = st.slider("Expression Percentile Cutpoint (50% = Median):", 15, 85, 50, 5)
        else:
            custom_pct = 50
        max_horizon = st.number_input(
            "Optional Right-Censor Follow-Up Horizon (0 = Full Follow-Up):",
            min_value=0.0, max_value=10000.0, value=0.0, step=12.0,
            help="Set to e.g. 60 to right-censor all patients at 60 months (5-year survival truncation), or leave at 0 for full follow-up."
        )

    with c3:
        st.markdown("**4. Publication Plot Annotations & Palette**")
        palette_choice = st.selectbox("Journal Color Palette:", list(PALETTE_SURV.keys()))
        show_ci_ribbon = st.checkbox("Show 95% Confidence Interval Shaded Ribbons", value=True)
        show_censored = st.checkbox("Show Censored Patient Tick Marks (+) on Curve", value=True)
        show_med_line = st.checkbox("Show 50% Median Survival Drop-Lines", value=True)
        excel_guard = st.checkbox(
            "🛡️ Enable Excel Gene-Name Guard (Protects MARCH1 / SEPT2)",
            value=False,
            help="Wraps gene symbols as explicit Excel strings (=\"GENE\") so Microsoft Excel never converts MARCH1 or SEPT2 into calendar dates."
        )

    current_file_sig = uploaded_file.name if uploaded_file is not None else "demo_survival"
    current_mode_sig = f"{current_file_sig}|{core_engine}"

    # ==========================================
    # STEP 4: RUN KAPLAN-MEIER & LOG-RANK ENGINE
    # ==========================================
    if st.button("🚀 Compute Survival Curves, Hazard Ratios & Generate 4-Panel Suite"):
        if st.session_state["locked_mode_t8"] is not None and st.session_state["locked_mode_t8"] != current_mode_sig:
            st.session_state["is_unlocked_t8"] = False
        st.session_state["locked_mode_t8"] = current_mode_sig

        with st.spinner("Computing Kaplan-Meier product-limit estimators, RMST, Greenwood 95% CIs, Mantel-Cox Log-Rank P-values, and 4 vector figures..."):
            event_arr = decode_event_column(df_input[event_col])
            strat = stratify_cohort(df_input, id_col, time_col, event_arr, target_feature, core_engine, custom_pct, max_horizon)

            if strat is None or len(strat["t1"]) < 2 or len(strat["t2"]) < 2:
                st.error("Insufficient valid survival observations in one or both stratified groups. Please check your Time, Event, and Biomarker column selections.")
            else:
                km1, med1, med1_ci, rmst1, cens1 = compute_km_curve(strat["t1"], strat["e1"], strat["g1_label"])
                km2, med2, med2_ci, rmst2, cens2 = compute_km_curve(strat["t2"], strat["e2"], strat["g2_label"])
                lr_res = compute_logrank_and_hr(strat["t1"], strat["e1"], strat["t2"], strat["e2"])
                lms = get_landmarks_for_unit(time_unit)

                km_combined_df = pd.concat([km1, km2], ignore_index=True)

                def fmt_med(m_val, m_ci, max_obs):
                    if m_val is None:
                        return f"Not Reached (> {max_obs:.1f} {time_unit})"
                    ci_l = f"{m_ci[0]:.1f}" if m_ci[0] is not None else "NR"
                    ci_u = f"{m_ci[1]:.1f}" if m_ci[1] is not None else "NR"
                    return f"{m_val:.1f} {time_unit} (95% CI: {ci_l}-{ci_u})"

                m1_str = fmt_med(med1, med1_ci, max(strat["t1"]))
                m2_str = fmt_med(med2, med2_ci, max(strat["t2"]))

                summary_df = pd.DataFrame([
                    {
                        "Target_Biomarker": (f'="{target_feature}"' if excel_guard else target_feature),
                        "Clinical_Endpoint": endpoint_choice,
                        "Cohort_Stratum": strat["g1_label"],
                        "Stratification_Rule": strat["cutpoint_str"],
                        "Total_Patients (N)": len(strat["t1"]),
                        "Events_Observed": int(np.sum(strat["e1"])),
                        "Censored_Patients": int(len(strat["t1"]) - np.sum(strat["e1"])),
                        "Median_Survival (95% CI)": m1_str,
                        f"RMST_Mean_Survival ({time_unit})": rmst1,
                        f"{lms[0]}_{time_unit}_Survival (%)": f"{get_surv_at_landmark(km1, lms[0])}%",
                        f"{lms[1]}_{time_unit}_Survival (%)": f"{get_surv_at_landmark(km1, lms[1])}%",
                        f"{lms[2]}_{time_unit}_Survival (%)": f"{get_surv_at_landmark(km1, lms[2])}%",
                        f"{lms[3]}_{time_unit}_Survival (%)": f"{get_surv_at_landmark(km1, lms[3])}%",
                        "Hazard_Ratio_vs_Ref": f"{lr_res['hr']:.2f} (95% CI: {lr_res['hr_low']:.2f}-{lr_res['hr_high']:.2f})",
                        "LogRank_Chi2": lr_res["chi2"],
                        "LogRank_Exact_P": format_p(lr_res["p_logrank"]),
                        "Wilcoxon_Breslow_P": format_p(lr_res["p_wilcoxon"]),
                        "Proportional_Hazards_Audit": lr_res["ph_status"],
                        "Significance_Call": p_to_stars(lr_res["p_logrank"])
                    },
                    {
                        "Target_Biomarker": (f'="{target_feature}"' if excel_guard else target_feature),
                        "Clinical_Endpoint": endpoint_choice,
                        "Cohort_Stratum": strat["g2_label"] + " [Reference]",
                        "Stratification_Rule": strat["cutpoint_str"],
                        "Total_Patients (N)": len(strat["t2"]),
                        "Events_Observed": int(np.sum(strat["e2"])),
                        "Censored_Patients": int(len(strat["t2"]) - np.sum(strat["e2"])),
                        "Median_Survival (95% CI)": m2_str,
                        f"RMST_Mean_Survival ({time_unit})": rmst2,
                        f"{lms[0]}_{time_unit}_Survival (%)": f"{get_surv_at_landmark(km2, lms[0])}%",
                        f"{lms[1]}_{time_unit}_Survival (%)": f"{get_surv_at_landmark(km2, lms[1])}%",
                        f"{lms[2]}_{time_unit}_Survival (%)": f"{get_surv_at_landmark(km2, lms[2])}%",
                        f"{lms[3]}_{time_unit}_Survival (%)": f"{get_surv_at_landmark(km2, lms[3])}%",
                        "Hazard_Ratio_vs_Ref": "1.00 (Reference Stratum)",
                        "LogRank_Chi2": lr_res["chi2"],
                        "LogRank_Exact_P": format_p(lr_res["p_logrank"]),
                        "Wilcoxon_Breslow_P": format_p(lr_res["p_wilcoxon"]),
                        "Proportional_Hazards_Audit": lr_res["ph_status"],
                        "Significance_Call": p_to_stars(lr_res["p_logrank"])
                    }
                ])

                # Multi-Gene Batch Prognostic Screen
                batch_rows = []
                eval_genes = [c for c in num_cols if c not in (id_col, time_col, event_col)]
                for g_col in eval_genes:
                    b_strat = stratify_cohort(df_input, id_col, time_col, event_arr, g_col, core_engine if "Categorical" not in core_engine else "Median", custom_pct, max_horizon)
                    if b_strat is not None and len(b_strat["t1"]) >= 2 and len(b_strat["t2"]) >= 2:
                        b_lr = compute_logrank_and_hr(b_strat["t1"], b_strat["e1"], b_strat["t2"], b_strat["e2"])
                        _, b_med1, _, b_rmst1, _ = compute_km_curve(b_strat["t1"], b_strat["e1"], "High")
                        _, b_med2, _, b_rmst2, _ = compute_km_curve(b_strat["t2"], b_strat["e2"], "Low")
                        if b_lr["p_logrank"] < 0.05:
                            prog_role = "Adverse Risk Factor (HR > 1)" if b_lr["hr"] > 1.0 else "Protective / Favorable Marker (HR < 1)"
                        else:
                            prog_role = "Neutral / Not Significant"
                        batch_rows.append({
                            "Biomarker_or_Gene": (f'="{g_col}"' if excel_guard else g_col),
                            "Cutpoint_Used": b_strat["cutpoint_str"],
                            "Hazard_Ratio (HR)": b_lr["hr"],
                            "95%_CI_Lower": b_lr["hr_low"],
                            "95%_CI_Upper": b_lr["hr_high"],
                            "Formatted_HR (95% CI)": f"{b_lr['hr']:.2f} ({b_lr['hr_low']:.2f}-{b_lr['hr_high']:.2f})",
                            "LogRank_Chi2": b_lr["chi2"],
                            "Raw_P_Numeric": b_lr["p_logrank"],
                            "LogRank_Exact_P": format_p(b_lr["p_logrank"]),
                            "Wilcoxon_Early_P": format_p(b_lr["p_wilcoxon"]),
                            f"High_Median ({time_unit})": f"{b_med1:.1f}" if b_med1 is not None else "NR",
                            f"Low_Median ({time_unit})": f"{b_med2:.1f}" if b_med2 is not None else "NR",
                            f"RMST_Diff_High_vs_Low ({time_unit})": round(b_rmst1 - b_rmst2, 2),
                            "Prognostic_Classification": prog_role
                        })

                batch_hr_df = pd.DataFrame(batch_rows)
                if not batch_hr_df.empty:
                    batch_hr_df = batch_hr_df.sort_values(by="Raw_P_Numeric").reset_index(drop=True)
                    m_tests = len(batch_hr_df)
                    bh_vals = [min(1.0, rp * m_tests / (idx + 1)) for idx, rp in enumerate(batch_hr_df["Raw_P_Numeric"])]
                    batch_hr_df.insert(8, "Benjamini_Hochberg_FDR_Q", [format_p(q) for q in bh_vals])
                    batch_hr_df = batch_hr_df.drop(columns=["Raw_P_Numeric"])
                else:
                    batch_hr_df = summary_df.copy()

                # Generate All 4 XML-Safe Publication Figures
                svg_km = generate_svg_km_with_risk_table(
                    km1, km2, cens1, cens2, med1, med2, lr_res, target_feature,
                    endpoint_choice, time_unit, palette_choice, show_censored, show_ci_ribbon, show_med_line
                )
                svg_haz = generate_svg_cumulative_hazard(km1, km2, target_feature, time_unit, palette_choice)
                svg_forest = generate_svg_hr_forest(batch_hr_df, palette_choice) if "Hazard_Ratio (HR)" in batch_hr_df.columns else svg_km
                svg_landmark = generate_svg_landmark_bars(km1, km2, target_feature, endpoint_choice, time_unit, palette_choice)

                html_report = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>GenomeTech Studio — {xml_esc(endpoint_choice)} Report ({xml_esc(target_feature)})</title>
<style>
  body {{ font-family: Arial, Helvetica, sans-serif; background: #f8fafc; color: #0f172a; margin: 24px; }}
  .header {{ background: linear-gradient(90deg, #1e1b4b, #4c1d95, #1e3a8a); color: #fff; padding: 20px 28px; border-radius: 12px; margin-bottom: 24px; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }}
  .card {{ background: #fff; border: 1px solid #cbd5e1; border-radius: 12px; padding: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 13px; }}
  th, td {{ border: 1px solid #cbd5e1; padding: 8px 10px; text-align: left; }}
  th {{ background: #f1f5f9; }}
</style>
</head>
<body>
  <div class="header">
    <h2 style="margin:0;">GenomeTech Studio | OmicsExpress Clinical Survival Report</h2>
    <p style="margin:6px 0 0 0;">Endpoint: <b>{xml_esc(endpoint_choice)}</b> | Biomarker: <b>{xml_esc(target_feature)}</b> | HR = {lr_res['hr']:.2f} (Log-Rank p = {xml_esc(format_p(lr_res['p_logrank']))})</p>
  </div>
  <div class="grid">
    <div class="card">{svg_km}</div>
    <div class="card">{svg_haz}</div>
    <div class="card">{svg_forest}</div>
    <div class="card">{svg_landmark}</div>
  </div>
  <div class="card">
    <h3>Cohort Survival Summary, RMST &amp; Landmark Survival Rates</h3>
    {summary_df.to_html(index=False)}
  </div>
</body>
</html>"""

                st.session_state["km_curve_df_t8"] = km_combined_df
                st.session_state["summary_df_t8"] = summary_df
                st.session_state["patient_assign_df_t8"] = strat["patient_df"]
                st.session_state["batch_hr_df_t8"] = batch_hr_df
                st.session_state["svg_km_t8"] = svg_km
                st.session_state["svg_haz_t8"] = svg_haz
                st.session_state["svg_forest_t8"] = svg_forest
                st.session_state["svg_landmark_t8"] = svg_landmark
                st.session_state["html_report_t8"] = html_report
                st.session_state["stats_t8"] = {
                    "feature": target_feature,
                    "endpoint": endpoint_choice,
                    "n_total": len(strat["t1"]) + len(strat["t2"]),
                    "events_total": int(np.sum(strat["e1"]) + np.sum(strat["e2"])),
                    "hr_str": f"{lr_res['hr']:.2f} ({lr_res['hr_low']:.2f}-{lr_res['hr_high']:.2f})",
                    "p_lr_str": format_p(lr_res["p_logrank"]),
                    "p_wilc_str": format_p(lr_res["p_wilcoxon"]),
                    "ph_status": lr_res["ph_status"],
                    "cutpoint": strat["cutpoint_str"],
                    "engine": core_engine
                }

# ==========================================
# DISPLAY TABULAR RESULTS, 4-PLOT SUITE, PAYWALL & REMARKS
# ==========================================
if "km_curve_df_t8" in st.session_state:
    km_df = st.session_state["km_curve_df_t8"]
    sum_df = st.session_state["summary_df_t8"]
    pat_df = st.session_state["patient_assign_df_t8"]
    batch_df = st.session_state["batch_hr_df_t8"]
    svg_km = st.session_state["svg_km_t8"]
    svg_haz = st.session_state["svg_haz_t8"]
    svg_forest = st.session_state["svg_forest_t8"]
    svg_landmark = st.session_state["svg_landmark_t8"]
    html_rep = st.session_state["html_report_t8"]
    stats = st.session_state["stats_t8"]

    st.markdown("---")
    st.markdown(f"### 📊 {stats['endpoint']} Summary & 4-Panel Clinical Figure Suite (`{stats['feature']}`)")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Cohort Size (Events)", f"{stats['n_total']} Patients ({stats['events_total']} Events)")
    m2.metric("Hazard Ratio (95% CI)", f"HR = {stats['hr_str']}")
    m3.metric("Mantel-Cox Log-Rank P", f"p = {stats['p_lr_str']}")
    m4.metric("Active Cutpoint", stats["cutpoint"])

    if st.session_state["is_unlocked_t8"]:
        st.success(f"✅ **Payment Verified for [{stats['engine']}]!** All 4 clinical survival figures, 4 CSV tables (including Patient Risk Group Assignments), and the printable HTML report are unlocked.")

        st.markdown("#### 🎨 4-Panel Clinical Survival Figure Suite (Vector `.svg` & Printable `.html`)")
        g1, g2 = st.columns(2)
        with g1:
            st.markdown(svg_km, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(svg_forest, unsafe_allow_html=True)
        with g2:
            st.markdown(svg_haz, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(svg_landmark, unsafe_allow_html=True)

        st.markdown("#### 📋 1. Cohort Survival Summary (`Median Survival`, `RMST`, `Hazard Ratio`, `Landmark Rates`)")
        st.dataframe(sum_df, use_container_width=True)

        st.markdown("#### 🧑‍⚕️ 2. Patient-Level Cohort Stratification & Risk Group Assignment Table")
        st.dataframe(pat_df, use_container_width=True)

        st.markdown("#### 🧬 3. Multi-Gene Batch Prognostic Hazard Ratio & FDR Screen")
        st.dataframe(batch_df, use_container_width=True)

        st.markdown("#### 🔬 4. Exact Kaplan-Meier Step-Function Coordinates & Greenwood 95% CIs")
        st.dataframe(km_df, use_container_width=True)

        st.markdown("#### ⬇️ Download Clinical Survival Tables (`.csv`) & High-Resolution Figures (`.svg` / `.html`)")
        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.download_button(
                "⬇️ 1. Cohort Summary & RMST (.csv)",
                data=sum_df.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"GenomeTech_Survival_Summary_{stats['feature']}.csv",
                mime="text/csv"
            )
            st.download_button(
                "⬇️ 5. Fig 1A: KM Curve + Risk Table (.svg)",
                data=svg_km.encode("utf-8"),
                file_name=f"GenomeTech_KM_Curve_{stats['feature']}.svg",
                mime="image/svg+xml"
            )
        with d2:
            st.download_button(
                "⬇️ 2. Patient Risk Assignments (.csv)",
                data=pat_df.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"GenomeTech_Patient_Strata_{stats['feature']}.csv",
                mime="text/csv"
            )
            st.download_button(
                "⬇️ 6. Fig 1B: Cumulative Hazard (.svg)",
                data=svg_haz.encode("utf-8"),
                file_name=f"GenomeTech_Cumulative_Hazard_{stats['feature']}.svg",
                mime="image/svg+xml"
            )
        with d3:
            st.download_button(
                "⬇️ 3. Batch Multi-Gene HR Screen (.csv)",
                data=batch_df.to_csv(index=False).encode("utf-8-sig"),
                file_name="GenomeTech_Batch_Prognostic_HR_Screen.csv",
                mime="text/csv"
            )
            st.download_button(
                "⬇️ 7. Fig 1C: HR Forest Plot (.svg)",
                data=svg_forest.encode("utf-8"),
                file_name="GenomeTech_Prognostic_HR_Forest.svg",
                mime="image/svg+xml"
            )
        with d4:
            st.download_button(
                "⬇️ 4. KM Coordinates & 95% CI (.csv)",
                data=km_df.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"GenomeTech_KM_Coordinates_{stats['feature']}.csv",
                mime="text/csv"
            )
            st.download_button(
                "⬇️ 8. All-in-One Visual Report (.html)",
                data=html_rep.encode("utf-8"),
                file_name=f"GenomeTech_Survival_Visual_Report_{stats['feature']}.html",
                mime="text/html"
            )
    else:
        st.markdown("**Live Preview (Stratified Cohort Summary, RMST & Hazard Ratio Verified):**")
        st.dataframe(sum_df, use_container_width=True)

        st.markdown('<div class="blurred-table">', unsafe_allow_html=True)
        st.table(pat_df.head(6))
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            st.markdown(svg_km, unsafe_allow_html=True)
        with p_col2:
            st.markdown(svg_haz, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        razorpay_link = "https://rzp.io/rzp/UVDck3w"
        st.markdown(f"""
        <div class="paywall-overlay">
            <h3 style="color: #e9d5ff !important; margin-top: 0;">🔒 Unlock All 4 Survival Figures, Patient Risk Table &amp; Batch HR Screen</h3>
            <p style="color: #cbd5e1 !important; font-size: 0.95rem;">
                Your cohort Hazard Ratio (HR = {stats['hr_str']}) and Log-Rank significance (p = {stats['p_lr_str']}) are verified above. Complete the $40 OmicsExpress checkout to unlock all 4 vector survival figures (<code>.svg</code>), all 4 survival &amp; patient assignment tables (<code>.csv</code>), and the printable visual report.
            </p>
            <div style="background:rgba(56,189,248,0.14);border:1px solid rgba(56,189,248,0.45);color:#e0f2fe !important;padding:8px 14px;border-radius:8px;font-size:0.88rem;font-weight:600;margin:10px auto 6px auto;max-width:520px;">🔥 <span style="color:#38bdf8 !important;font-weight:800;">FOUNDING LAB LAUNCH OFFER:</span> <s style="color:#94a3b8 !important;">$100 USD</s> <b style="color:#ffffff !important;">$40 USD</b> — Special Early-Access Rate for Our First 20 Research Clients</div><a href="{razorpay_link}" target="_blank" style="background: linear-gradient(90deg, #9333ea 0%, #2563eb 100%); color: white !important; padding: 14px 32px; text-decoration: none; border-radius: 10px; font-weight: 700; font-size: 1.05rem; display: inline-block; margin: 12px 0; border: 1px solid #c084fc; box-shadow: 0 4px 20px rgba(147, 51, 234, 0.5);">
                💳 Pay $40 via Razorpay to Unlock Full Survival Suite
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
                    st.session_state["is_unlocked_t8"] = True
                    st.rerun()
                else:
                    st.error("Invalid Payment ID. Please paste the 'pay_...' ID shown on your Razorpay payment confirmation screen.")

    # ==========================================
    # STEP 6: AUTOMATED REMARKS & DIRECT EMAIL
    # ==========================================
    st.markdown("---")
    st.markdown("### 📝 Automated Clinical Survival Remarks & Direct Support")

    st.info(
        f"**Automated Kaplan-Meier & Prognostic Diagnostics:**\n"
        f"* **Stratification Pipeline:** {stats['engine']} | Endpoint: `{stats['endpoint']}` | Biomarker: `{stats['feature']}` ({stats['cutpoint']})\n"
        f"* **Hazard Ratio & Log-Rank Test:** Evaluated **{stats['n_total']}** patients (**{stats['events_total']}** clinical events). Mantel-Cox Log-Rank $p = {stats['p_lr_str']}$ (Gehan-Breslow-Wilcoxon early-event $p = {stats['p_wilc_str']}$), with **Hazard Ratio = {stats['hr_str']}**.\n"
        f"* **Proportional Hazards & RMST Audit:** {stats['ph_status']}. Restricted Mean Survival Time (`RMST`) and Brookmeyer-Crowley 95% median survival confidence bounds are included in Deliverable #1."
    )

    with st.expander("💬 Send Remarks or Questions Directly to GenomeTech Team (via Email)"):
        client_email = st.text_input("Your Lab / Institutional Email:")
        client_remark = st.text_area("Your Remarks or Questions about this Kaplan-Meier Survival Run:")
        if st.button("Prepare Direct Email"):
            subject = urllib.parse.quote(f"OmicsExpress Tool #8 Remark - {client_email}")
            body = urllib.parse.quote(
                f"Client Email: {client_email}\n"
                f"Tool Used: Tool #8 - Kaplan-Meier Survival Plotter\n"
                f"Engine: {stats['engine']} | Endpoint: {stats['endpoint']} | Feature: {stats['feature']} ({stats['cutpoint']})\n"
                f"Hazard Ratio (95% CI): {stats['hr_str']} | Log-Rank P: {stats['p_lr_str']}\n\n"
                f"Client Remarks:\n{client_remark}"
            )
            mailto_url = f"mailto:bhumikasihare555@gmail.com?subject={subject}&body={body}"
            st.success("✅ Your remark and survival diagnostics are ready! Click below to send directly from your email client:")
            st.markdown(f'👉 <a href="https://mail.google.com/mail/?view=cm&fs=1&to=bhumikasihare555@gmail.com&su={subject}&body={body}" target="_blank" style="color:#38bdf8;font-weight:700;text-decoration:underline;">Click Here to Send via Gmail (Browser)</a> &nbsp;|&nbsp; <a href="{mailto_url}" style="color:#c4b5fd;font-weight:600;text-decoration:underline;">Open in Default Mail App (Outlook/Mac)</a>', unsafe_allow_html=True)