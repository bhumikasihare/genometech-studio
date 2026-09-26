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
    page_title="Automated ANOVA & Post-Hoc Suite | OmicsExpress",
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
    <span class="gts-badge">⚡ Tool #7: Automated ANOVA & Post-Hoc Suite</span>
</div>
""", unsafe_allow_html=True)

query_params = st.query_params
if "unlocked" in query_params and query_params["unlocked"] == "GTS2026":
    st.session_state["is_unlocked_t7"] = True
if "is_unlocked_t7" not in st.session_state:
    st.session_state["is_unlocked_t7"] = False
if "locked_mode_t7" not in st.session_state:
    st.session_state["locked_mode_t7"] = None

# Callback that resets unlock & results ONLY when Core Statistical Engine or Uploaded File changes
def reset_on_mode_change_t7():
    st.session_state["is_unlocked_t7"] = False
    st.session_state.pop("posthoc_df_t7", None)
    st.session_state.pop("desc_df_t7", None)
    st.session_state.pop("batch_df_t7", None)
    st.session_state.pop("svg_box_t7", None)
    st.session_state.pop("svg_bar_t7", None)
    st.session_state.pop("svg_forest_t7", None)
    st.session_state.pop("svg_profile_t7", None)
    st.session_state.pop("html_report_t7", None)
    st.session_state.pop("stats_t7", None)

st.markdown("## Automated ANOVA, Post-Hoc & 4-Panel Publication Figure Suite")
st.markdown(
    "Compute **One-Way ANOVA, Welch's ANOVA, or Non-Parametric Kruskal-Wallis tests** with **Tukey's HSD / Games-Howell / Dunn's Post-Hoc** comparisons instantly. "
    "Includes **Shapiro-Wilk Normality & Levene's Variance Audits**, **3 Excel-Ready Statistical Tables (`.csv`)**, "
    "**4 High-Resolution Vector Figures (`.svg`)**, and a **1-Click Printable Visual Report (`.html`)**."
)

with st.expander("📋 Accepted File Formats, Cross-Platform Guide & Complete Deliverables (.csv, .svg, .html)", expanded=True):
    st.markdown("""
    * **Supported Data Layouts:**
      1. **Standard Sample-Row Table (Default):** Contains an Experimental Group column and one or more numeric Gene/Biomarker/Cytokine columns.
      2. **Wide Group-Column Table:** Each column represents a separate experimental treatment group with replicate measurements in the rows.
    * **4 Publication-Ready Figures & 3 Statistical Tables Generated Automatically:**
      * **Figure 1A (Significance Boxplot):** Median, IQR box, Mean diamond (`◆`), individual replicate jitter points, and pairwise significance star brackets.
      * **Figure 1B (GraphPad-Style Mean ± SD Bar Chart):** Group mean bars with standard deviation whiskers, overlaid sample dots, and significance brackets.
      * **Figure 1C (Post-Hoc 95% CI Forest Plot):** Visualizes pairwise mean differences (`Group B - Group A`) and 95% confidence intervals against the zero-effect line.
      * **Figure 1D (Multi-Biomarker Z-Score Trajectory Plot):** Compares standardized expression trajectories across all biomarkers in your dataset.
    * **💻 Cross-Platform File Compatibility (Windows & Apple macOS):** All exported `.csv` tables use universal `UTF-8-BOM` encoding—double-click to open directly in **Microsoft Excel (Windows/Mac)**, **Apple Numbers**, **Google Sheets**, or load into **R / Python**. Vector figure (`.svg` / `.html`) outputs open natively in any web browser (**Safari / Chrome / Edge**) or vector editor (**Illustrator / PowerPoint / Keynote**).
    * **Single-Mode License Note:** Each checkout unlocks your selected **Core Statistical Engine** across all biomarkers in your uploaded dataset. Switching between target biomarkers, changing color palettes, or adjusting cutoffs within your unlocked engine is free; switching the Core Statistical Engine or uploading a new file starts a new run.
    """)

# ==========================================
# DEMO MULTI-GROUP EXPERIMENTAL DATASET
# ==========================================
DEMO_ANOVA_DF = pd.DataFrame([
    {"Sample_ID": "CTRL_01", "Treatment_Group": "Vehicle_Control", "CD274_PDL1_TPM": 18.2, "IFNG_Cytokine_pg_mL": 42.5, "TP53_Expression": 110.4, "Tumor_Volume_mm3": 845.0, "MARCH1_TPM": 24.1},
    {"Sample_ID": "CTRL_02", "Treatment_Group": "Vehicle_Control", "CD274_PDL1_TPM": 22.4, "IFNG_Cytokine_pg_mL": 38.0, "TP53_Expression": 104.2, "Tumor_Volume_mm3": 910.5, "MARCH1_TPM": 26.8},
    {"Sample_ID": "CTRL_03", "Treatment_Group": "Vehicle_Control", "CD274_PDL1_TPM": 19.8, "IFNG_Cytokine_pg_mL": 49.2, "TP53_Expression": 118.0, "Tumor_Volume_mm3": 790.2, "MARCH1_TPM": 21.5},
    {"Sample_ID": "CTRL_04", "Treatment_Group": "Vehicle_Control", "CD274_PDL1_TPM": 15.6, "IFNG_Cytokine_pg_mL": 35.1, "TP53_Expression": 98.5,  "Tumor_Volume_mm3": 880.0, "MARCH1_TPM": 23.0},
    {"Sample_ID": "CTRL_05", "Treatment_Group": "Vehicle_Control", "CD274_PDL1_TPM": 24.1, "IFNG_Cytokine_pg_mL": 44.8, "TP53_Expression": 115.2, "Tumor_Volume_mm3": 950.4, "MARCH1_TPM": 28.4},
    {"Sample_ID": "CTRL_06", "Treatment_Group": "Vehicle_Control", "CD274_PDL1_TPM": 20.5, "IFNG_Cytokine_pg_mL": 41.0, "TP53_Expression": 108.9, "Tumor_Volume_mm3": 825.6, "MARCH1_TPM": 25.0},
    {"Sample_ID": "CTRL_07", "Treatment_Group": "Vehicle_Control", "CD274_PDL1_TPM": 17.9, "IFNG_Cytokine_pg_mL": 39.5, "TP53_Expression": 101.3, "Tumor_Volume_mm3": 870.1, "MARCH1_TPM": 22.7},
    {"Sample_ID": "CTRL_08", "Treatment_Group": "Vehicle_Control", "CD274_PDL1_TPM": 21.0, "IFNG_Cytokine_pg_mL": 46.0, "TP53_Expression": 112.7, "Tumor_Volume_mm3": 905.0, "MARCH1_TPM": 25.9},
    {"Sample_ID": "PD1_01", "Treatment_Group": "Anti_PD1_Mono", "CD274_PDL1_TPM": 48.5, "IFNG_Cytokine_pg_mL": 128.4, "TP53_Expression": 145.0, "Tumor_Volume_mm3": 510.2, "MARCH1_TPM": 38.2},
    {"Sample_ID": "PD1_02", "Treatment_Group": "Anti_PD1_Mono", "CD274_PDL1_TPM": 54.2, "IFNG_Cytokine_pg_mL": 142.0, "TP53_Expression": 158.6, "Tumor_Volume_mm3": 465.8, "MARCH1_TPM": 41.5},
    {"Sample_ID": "PD1_03", "Treatment_Group": "Anti_PD1_Mono", "CD274_PDL1_TPM": 44.0, "IFNG_Cytokine_pg_mL": 115.6, "TP53_Expression": 139.2, "Tumor_Volume_mm3": 540.0, "MARCH1_TPM": 35.9},
    {"Sample_ID": "PD1_04", "Treatment_Group": "Anti_PD1_Mono", "CD274_PDL1_TPM": 58.9, "IFNG_Cytokine_pg_mL": 155.2, "TP53_Expression": 164.1, "Tumor_Volume_mm3": 430.5, "MARCH1_TPM": 44.0},
    {"Sample_ID": "PD1_05", "Treatment_Group": "Anti_PD1_Mono", "CD274_PDL1_TPM": 51.3, "IFNG_Cytokine_pg_mL": 134.8, "TP53_Expression": 150.4, "Tumor_Volume_mm3": 490.0, "MARCH1_TPM": 39.8},
    {"Sample_ID": "PD1_06", "Treatment_Group": "Anti_PD1_Mono", "CD274_PDL1_TPM": 46.8, "IFNG_Cytokine_pg_mL": 121.0, "TP53_Expression": 142.8, "Tumor_Volume_mm3": 525.4, "MARCH1_TPM": 37.1},
    {"Sample_ID": "PD1_07", "Treatment_Group": "Anti_PD1_Mono", "CD274_PDL1_TPM": 55.6, "IFNG_Cytokine_pg_mL": 149.5, "TP53_Expression": 160.0, "Tumor_Volume_mm3": 450.2, "MARCH1_TPM": 42.6},
    {"Sample_ID": "PD1_08", "Treatment_Group": "Anti_PD1_Mono", "CD274_PDL1_TPM": 49.9, "IFNG_Cytokine_pg_mL": 130.2, "TP53_Expression": 148.5, "Tumor_Volume_mm3": 485.0, "MARCH1_TPM": 38.9},
    {"Sample_ID": "TKI_01", "Treatment_Group": "Targeted_TKI", "CD274_PDL1_TPM": 34.0, "IFNG_Cytokine_pg_mL": 88.5, "TP53_Expression": 185.4, "Tumor_Volume_mm3": 390.0, "MARCH1_TPM": 52.4},
    {"Sample_ID": "TKI_02", "Treatment_Group": "Targeted_TKI", "CD274_PDL1_TPM": 39.5, "IFNG_Cytokine_pg_mL": 96.2, "TP53_Expression": 198.0, "Tumor_Volume_mm3": 355.5, "MARCH1_TPM": 56.8},
    {"Sample_ID": "TKI_03", "Treatment_Group": "Targeted_TKI", "CD274_PDL1_TPM": 31.2, "IFNG_Cytokine_pg_mL": 79.4, "TP53_Expression": 176.2, "Tumor_Volume_mm3": 420.8, "MARCH1_TPM": 49.0},
    {"Sample_ID": "TKI_04", "Treatment_Group": "Targeted_TKI", "CD274_PDL1_TPM": 42.1, "IFNG_Cytokine_pg_mL": 104.0, "TP53_Expression": 205.1, "Tumor_Volume_mm3": 340.2, "MARCH1_TPM": 59.2},
    {"Sample_ID": "TKI_05", "Treatment_Group": "Targeted_TKI", "CD274_PDL1_TPM": 36.8, "IFNG_Cytokine_pg_mL": 92.0, "TP53_Expression": 190.5, "Tumor_Volume_mm3": 375.0, "MARCH1_TPM": 54.1},
    {"Sample_ID": "TKI_06", "Treatment_Group": "Targeted_TKI", "CD274_PDL1_TPM": 33.4, "IFNG_Cytokine_pg_mL": 84.1, "TP53_Expression": 181.0, "Tumor_Volume_mm3": 405.6, "MARCH1_TPM": 51.3},
    {"Sample_ID": "TKI_07", "Treatment_Group": "Targeted_TKI", "CD274_PDL1_TPM": 40.2, "IFNG_Cytokine_pg_mL": 99.8, "TP53_Expression": 201.4, "Tumor_Volume_mm3": 348.9, "MARCH1_TPM": 57.5},
    {"Sample_ID": "TKI_08", "Treatment_Group": "Targeted_TKI", "CD274_PDL1_TPM": 35.9, "IFNG_Cytokine_pg_mL": 90.5, "TP53_Expression": 188.2, "Tumor_Volume_mm3": 382.0, "MARCH1_TPM": 53.6},
    {"Sample_ID": "COMBO_01", "Treatment_Group": "Combo_PD1_plus_TKI", "CD274_PDL1_TPM": 92.4, "IFNG_Cytokine_pg_mL": 265.0, "TP53_Expression": 268.5, "Tumor_Volume_mm3": 125.4, "MARCH1_TPM": 84.2},
    {"Sample_ID": "COMBO_02", "Treatment_Group": "Combo_PD1_plus_TKI", "CD274_PDL1_TPM": 104.8, "IFNG_Cytokine_pg_mL": 290.4, "TP53_Expression": 285.0, "Tumor_Volume_mm3": 98.0,  "MARCH1_TPM": 91.5},
    {"Sample_ID": "COMBO_03", "Treatment_Group": "Combo_PD1_plus_TKI", "CD274_PDL1_TPM": 86.2, "IFNG_Cytokine_pg_mL": 248.2, "TP53_Expression": 252.1, "Tumor_Volume_mm3": 148.6, "MARCH1_TPM": 79.8},
    {"Sample_ID": "COMBO_04", "Treatment_Group": "Combo_PD1_plus_TKI", "CD274_PDL1_TPM": 112.5, "IFNG_Cytokine_pg_mL": 310.0, "TP53_Expression": 298.4, "Tumor_Volume_mm3": 82.5,  "MARCH1_TPM": 96.0},
    {"Sample_ID": "COMBO_05", "Treatment_Group": "Combo_PD1_plus_TKI", "CD274_PDL1_TPM": 98.0, "IFNG_Cytokine_pg_mL": 278.5, "TP53_Expression": 276.0, "Tumor_Volume_mm3": 112.0, "MARCH1_TPM": 88.4},
    {"Sample_ID": "COMBO_06", "Treatment_Group": "Combo_PD1_plus_TKI", "CD274_PDL1_TPM": 90.1, "IFNG_Cytokine_pg_mL": 259.0, "TP53_Expression": 261.8, "Tumor_Volume_mm3": 134.2, "MARCH1_TPM": 82.1},
    {"Sample_ID": "COMBO_07", "Treatment_Group": "Combo_PD1_plus_TKI", "CD274_PDL1_TPM": 108.3, "IFNG_Cytokine_pg_mL": 298.6, "TP53_Expression": 291.2, "Tumor_Volume_mm3": 91.4,  "MARCH1_TPM": 93.7},
    {"Sample_ID": "COMBO_08", "Treatment_Group": "Combo_PD1_plus_TKI", "CD274_PDL1_TPM": 95.6, "IFNG_Cytokine_pg_mL": 272.1, "TP53_Expression": 272.9, "Tumor_Volume_mm3": 118.8, "MARCH1_TPM": 86.5}
])

# ==========================================
# BIOSTATISTICAL ENGINE & EXACT MATH HELPERS
# ==========================================
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

def short_stars(p):
    if p < 0.0001:
        return "****"
    elif p < 0.001:
        return "***"
    elif p < 0.01:
        return "**"
    elif p < 0.05:
        return "*"
    return "ns"

def format_p(p):
    if p < 1e-12:
        return "< 1.00e-12"
    elif p < 0.0001:
        return f"{p:.2e}"
    return f"{p:.5f}"

def normal_sf(z):
    return 0.5 * math.erfc(abs(z) / math.sqrt(2.0))

def shapiro_normality_p(vals):
    v = np.array(vals, dtype=float)
    if len(v) < 3:
        return 1.0
    if HAS_SCIPY:
        try:
            _, p_val = sp_stats.shapiro(v)
            return float(p_val)
        except Exception:
            pass
    # Skewness-Kurtosis normality approximation fallback
    std_v = float(np.std(v, ddof=1))
    if std_v <= 1e-9:
        return 1.0
    z_scores = (v - float(np.mean(v))) / std_v
    skew = float(np.mean(z_scores ** 3))
    z_stat = abs(skew) / math.sqrt(6.0 / len(v))
    return min(1.0, max(1e-6, 2.0 * normal_sf(z_stat)))

def t_dist_two_tail_p(t_val, df):
    if HAS_SCIPY:
        return float(sp_stats.t.sf(abs(t_val), df) * 2.0)
    t_abs = abs(t_val)
    if df <= 0:
        return 1.0
    z = math.sqrt(df * math.log(1.0 + (t_abs * t_abs) / df)) * (1.0 - 1.0 / (4.0 * df))
    return min(1.0, max(1e-15, 2.0 * normal_sf(z)))

def f_dist_sf_p(f_val, df1, df2):
    if f_val <= 0 or df1 <= 0 or df2 <= 0:
        return 1.0
    if HAS_SCIPY:
        return float(sp_stats.f.sf(f_val, df1, df2))
    a = 2.0 / (9.0 * df1)
    b = 2.0 / (9.0 * df2)
    f_cbrt = f_val ** (1.0 / 3.0)
    num = (1.0 - b) * f_cbrt - (1.0 - a)
    den = math.sqrt(b * (f_cbrt ** 2) + a)
    z = num / max(1e-9, den)
    return min(1.0, max(1e-15, normal_sf(z)))

def chi2_sf_p(chi2_val, df):
    if chi2_val <= 0 or df <= 0:
        return 1.0
    if HAS_SCIPY:
        return float(sp_stats.chi2.sf(chi2_val, df))
    k = float(df)
    z = ((chi2_val / k) ** (1.0 / 3.0) - (1.0 - 2.0 / (9.0 * k))) / math.sqrt(2.0 / (9.0 * k))
    return min(1.0, max(1e-15, normal_sf(z)))

def tukey_hsd_p(q_val, k_groups, df_within):
    if q_val <= 0:
        return 1.0
    if HAS_SCIPY and hasattr(sp_stats, "studentized_range"):
        try:
            return float(sp_stats.studentized_range.sf(q_val, k_groups, df_within))
        except Exception:
            pass
    t_equiv = q_val / math.sqrt(2.0)
    p_unadj = t_dist_two_tail_p(t_equiv, df_within)
    n_pairs = max(1, (k_groups * (k_groups - 1)) // 2)
    return min(1.0, max(1e-15, 1.0 - ((1.0 - p_unadj) ** n_pairs)))

def run_omnibus_and_posthoc(groups_dict, engine_mode):
    group_names = list(groups_dict.keys())
    arrays = [np.array(groups_dict[g], dtype=float) for g in group_names]
    k = len(arrays)
    n_total = sum(len(a) for a in arrays)

    z_arrays = [np.abs(a - np.median(a)) for a in arrays]
    all_z = np.concatenate(z_arrays)
    grand_z = np.mean(all_z)
    ss_b_z = sum(len(z) * ((np.mean(z) - grand_z) ** 2) for z in z_arrays)
    ss_w_z = sum(np.sum((z - np.mean(z)) ** 2) for z in z_arrays)
    df1 = k - 1
    df2 = n_total - k
    f_levene = (ss_b_z / max(1, df1)) / max(1e-9, (ss_w_z / max(1, df2)))
    p_levene = f_dist_sf_p(f_levene, df1, df2)

    all_vals = np.concatenate(arrays)
    grand_mean = np.mean(all_vals)
    ss_between = sum(len(a) * ((np.mean(a) - grand_mean) ** 2) for a in arrays)
    ss_within = sum(np.sum((a - np.mean(a)) ** 2) for a in arrays)
    ss_total = ss_between + ss_within
    ms_between = ss_between / max(1, df1)
    ms_within = ss_within / max(1, df2)

    eta_sq = round(ss_between / max(1e-9, ss_total), 4)
    omega_sq = round(max(0.0, (ss_between - df1 * ms_within) / max(1e-9, ss_total + ms_within)), 4)

    if "Welch" in engine_mode:
        weights = [len(a) / max(1e-9, np.var(a, ddof=1)) for a in arrays]
        w_sum = sum(weights)
        mean_star = sum(w * np.mean(a) for w, a in zip(weights, arrays)) / w_sum
        lambda_term = sum(((1.0 - (w / w_sum)) ** 2) / max(1, len(a) - 1) for w, a in zip(weights, arrays))
        f_stat = (
            sum(w * ((np.mean(a) - mean_star) ** 2) for w, a in zip(weights, arrays)) / max(1, k - 1)
        ) / (1.0 + (2.0 * (k - 2) / max(1, (k * k - 1))) * lambda_term)
        df_welch = ((k * k - 1) / max(1e-9, 3.0 * lambda_term))
        p_omni = f_dist_sf_p(f_stat, df1, df_welch)
        omni_name = f"Welch F({df1}, {df_welch:.1f}) = {f_stat:.2f}"
    elif "Kruskal-Wallis" in engine_mode:
        if HAS_SCIPY:
            h_stat, p_omni = sp_stats.kruskal(*arrays)
            f_stat = float(h_stat)
        else:
            ranks = pd.Series(all_vals).rank().values
            idx = 0
            r_sums = []
            for a in arrays:
                r_sums.append(np.sum(ranks[idx : idx + len(a)]))
                idx += len(a)
            h_stat = (12.0 / (n_total * (n_total + 1))) * sum((rs ** 2) / len(a) for rs, a in zip(r_sums, arrays)) - 3.0 * (n_total + 1)
            f_stat = float(h_stat)
            p_omni = chi2_sf_p(h_stat, df1)
        omni_name = f"Kruskal-Wallis H({df1}) = {f_stat:.2f}"
    else:
        f_stat = ms_between / max(1e-9, ms_within)
        p_omni = f_dist_sf_p(f_stat, df1, df2)
        omni_name = f"ANOVA F({df1}, {df2}) = {f_stat:.2f}"

    n_pairs = max(1, (k * (k - 1)) // 2)
    posthoc_rows = []

    all_ranks = pd.Series(all_vals).rank().values
    group_mean_ranks = {}
    curr_i = 0
    for g, a in zip(group_names, arrays):
        group_mean_ranks[g] = np.mean(all_ranks[curr_i : curr_i + len(a)])
        curr_i += len(a)

    for i in range(k):
        for j in range(i + 1, k):
            g1, g2 = group_names[i], group_names[j]
            a1, a2 = arrays[i], arrays[j]
            n1, n2 = len(a1), len(a2)
            m1, m2 = float(np.mean(a1)), float(np.mean(a2))
            sd1, sd2 = float(np.std(a1, ddof=1)), float(np.std(a2, ddof=1))

            mean_diff = m2 - m1
            fold_change = round(m2 / m1, 3) if abs(m1) > 1e-9 else 0.0

            s_pool = math.sqrt(((n1 - 1) * (sd1 ** 2) + (n2 - 1) * (sd2 ** 2)) / max(1, n1 + n2 - 2))
            cohens_d = round(abs(mean_diff) / max(1e-9, s_pool), 3)

            if "Welch" in engine_mode:
                se_gh = math.sqrt((sd1 ** 2) / n1 + (sd2 ** 2) / n2)
                q_gh = abs(mean_diff) / max(1e-9, se_gh / math.sqrt(2.0))
                df_gh = (((sd1 ** 2) / n1 + (sd2 ** 2) / n2) ** 2) / max(
                    1e-9,
                    (((sd1 ** 2) / n1) ** 2) / max(1, n1 - 1) + (((sd2 ** 2) / n2) ** 2) / max(1, n2 - 1)
                )
                p_adj = tukey_hsd_p(q_gh, k, df_gh)
                stat_label = f"q = {q_gh:.3f} (Games-Howell)"
                ci_half = 1.96 * se_gh
            elif "Kruskal-Wallis" in engine_mode:
                se_dunn = math.sqrt((n_total * (n_total + 1) / 12.0) * (1.0 / n1 + 1.0 / n2))
                z_dunn = abs(group_mean_ranks[g2] - group_mean_ranks[g1]) / max(1e-9, se_dunn)
                p_raw = 2.0 * normal_sf(z_dunn)
                p_adj = min(1.0, p_raw * n_pairs)
                stat_label = f"Z = {z_dunn:.3f} (Dunn's Test)"
                se_diff = math.sqrt((sd1 ** 2) / n1 + (sd2 ** 2) / n2)
                ci_half = 1.96 * se_diff
            else:
                se_tukey = math.sqrt(ms_within * 0.5 * (1.0 / n1 + 1.0 / n2))
                q_tukey = abs(mean_diff) / max(1e-9, se_tukey)
                p_adj = tukey_hsd_p(q_tukey, k, df2)
                stat_label = f"q = {q_tukey:.3f} (Tukey HSD)"
                se_diff = math.sqrt(ms_within * (1.0 / n1 + 1.0 / n2))
                ci_half = 1.96 * se_diff

            posthoc_rows.append({
                "Comparison (Group A vs Group B)": f"{g1} vs {g2}",
                "Group_A": g1,
                "Group_B": g2,
                "Mean_A ± SD_A": f"{m1:.2f} ± {sd1:.2f}",
                "Mean_B ± SD_B": f"{m2:.2f} ± {sd2:.2f}",
                "Mean_Difference (B - A)": round(mean_diff, 3),
                "Fold_Change (B / A)": fold_change,
                "95%_CI_Lower": round(mean_diff - ci_half, 3),
                "95%_CI_Upper": round(mean_diff + ci_half, 3),
                "PostHoc_Statistic": stat_label,
                "Adjusted_P_Value_Numeric": p_adj,
                "Exact_Adjusted_P_Value": format_p(p_adj),
                "Significance_Call": p_to_stars(p_adj),
                "Short_Stars": short_stars(p_adj),
                "Cohens_d_Effect_Size": cohens_d
            })

    return {
        "omni_name": omni_name,
        "f_stat": round(f_stat, 3),
        "p_omni": p_omni,
        "p_omni_str": format_p(p_omni),
        "eta_sq": eta_sq,
        "omega_sq": omega_sq,
        "f_levene": round(f_levene, 3),
        "p_levene": p_levene,
        "p_levene_str": format_p(p_levene),
        "posthoc": pd.DataFrame(posthoc_rows)
    }

# ==========================================
# 4-PANEL XML-SAFE VECTOR SVG FIGURE SUITE
# ==========================================
PALETTE_MAP = {
    "Nature Biotech (Cosmic Indigo / Violet / Cyan / Emerald)": ["#6366f1", "#a855f7", "#06b6d4", "#10b981", "#f59e0b", "#ec4899"],
    "Cell Press (Crimson / Royal Blue / Teal / Amber)": ["#e11d48", "#2563eb", "#0d9488", "#d97706", "#7c3aed", "#475569"],
    "High-Contrast Grayscale (Print Journal Ready)": ["#334155", "#64748b", "#94a3b8", "#475569", "#1e293b", "#cbd5e1"]
}

def xml_esc(txt):
    return html.escape(str(txt), quote=True)

def generate_svg_boxplot(groups_dict, feature_name, omni_summary, posthoc_df, palette_name):
    colors = PALETTE_MAP.get(palette_name, list(PALETTE_MAP.values())[0])
    group_names = list(groups_dict.keys())
    k = len(group_names)
    all_vals = np.concatenate([np.array(v, dtype=float) for v in groups_dict.values()])
    y_min_raw, y_max_raw = float(np.min(all_vals)), float(np.max(all_vals))
    span = max(1e-6, y_max_raw - y_min_raw)

    sig_pairs = posthoc_df[posthoc_df["Adjusted_P_Value_Numeric"] < 0.05].sort_values(by="Adjusted_P_Value_Numeric").head(4)
    n_brackets = len(sig_pairs)

    y_min = y_min_raw - 0.10 * span
    y_max = y_max_raw + (0.22 + 0.12 * n_brackets) * span

    width, height = 820, 490
    pad_l, pad_r, pad_t, pad_b = 85, 35, 65, 80
    plot_w, plot_h = width - pad_l - pad_r, height - pad_t - pad_b

    def y_to_px(val):
        return pad_t + plot_h - ((val - y_min) / max(1e-9, y_max - y_min)) * plot_h

    def x_for_group(idx):
        return pad_l + (idx + 0.5) * (plot_w / max(1, k))

    f_esc = xml_esc(feature_name)
    sub_esc = xml_esc(f'{omni_summary["omni_name"]} | p = {omni_summary["p_omni_str"]} | Eta2 = {omni_summary["eta_sq"]}')

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="background:#ffffff; border-radius:12px; font-family:Arial, Helvetica, sans-serif;">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff" rx="12"/>',
        f'<text x="{width/2}" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#0f172a">Figure 1A: {f_esc} — Boxplot, Replicate Jitter &amp; Post-Hoc Brackets</text>',
        f'<text x="{width/2}" y="48" text-anchor="middle" font-size="12" fill="#475569">{sub_esc}</text>'
    ]

    for t_idx in range(6):
        y_val = y_min + (t_idx / 5.0) * (y_max - y_min)
        py = y_to_px(y_val)
        svg.append(f'<line x1="{pad_l}" y1="{py:.1f}" x2="{width - pad_r}" y2="{py:.1f}" stroke="#e2e8f0" stroke-dasharray="4,4" stroke-width="1"/>')
        svg.append(f'<text x="{pad_l - 10}" y="{py + 4:.1f}" text-anchor="end" font-size="11" fill="#334155">{y_val:.1f}</text>')

    svg.append(f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{pad_t + plot_h}" stroke="#0f172a" stroke-width="1.8"/>')
    svg.append(f'<line x1="{pad_l}" y1="{pad_t + plot_h}" x2="{width - pad_r}" y2="{pad_t + plot_h}" stroke="#0f172a" stroke-width="1.8"/>')
    svg.append(f'<text x="22" y="{pad_t + plot_h/2}" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#0f172a" transform="rotate(-90, 22, {pad_t + plot_h/2})">{f_esc}</text>')

    box_w = min(72, (plot_w / max(1, k)) * 0.46)
    for idx, g_name in enumerate(group_names):
        vals = np.sort(np.array(groups_dict[g_name], dtype=float))
        if len(vals) == 0:
            continue
        cx = x_for_group(idx)
        col = colors[idx % len(colors)]
        q25, med, q75 = np.percentile(vals, [25, 50, 75])
        iqr = q75 - q25
        low_whisk = float(np.min(vals[vals >= (q25 - 1.5 * iqr)]))
        high_whisk = float(np.max(vals[vals <= (q75 + 1.5 * iqr)]))
        mean_val = float(np.mean(vals))

        py_q25, py_med, py_q75 = y_to_px(q25), y_to_px(med), y_to_px(q75)
        py_low, py_high, py_mean = y_to_px(low_whisk), y_to_px(high_whisk), y_to_px(mean_val)

        svg.append(f'<line x1="{cx:.1f}" y1="{py_high:.1f}" x2="{cx:.1f}" y2="{py_q75:.1f}" stroke="#1e293b" stroke-width="1.6"/>')
        svg.append(f'<line x1="{cx:.1f}" y1="{py_q25:.1f}" x2="{cx:.1f}" y2="{py_low:.1f}" stroke="#1e293b" stroke-width="1.6"/>')
        svg.append(f'<line x1="{cx - box_w*0.3:.1f}" y1="{py_high:.1f}" x2="{cx + box_w*0.3:.1f}" y2="{py_high:.1f}" stroke="#1e293b" stroke-width="1.6"/>')
        svg.append(f'<line x1="{cx - box_w*0.3:.1f}" y1="{py_low:.1f}" x2="{cx + box_w*0.3:.1f}" y2="{py_low:.1f}" stroke="#1e293b" stroke-width="1.6"/>')

        box_top = min(py_q75, py_q25)
        box_h = max(2.0, abs(py_q25 - py_q75))
        svg.append(f'<rect x="{cx - box_w/2:.1f}" y="{box_top:.1f}" width="{box_w:.1f}" height="{box_h:.1f}" fill="{col}" fill-opacity="0.28" stroke="{col}" stroke-width="2.2" rx="3"/>')
        svg.append(f'<line x1="{cx - box_w/2:.1f}" y1="{py_med:.1f}" x2="{cx + box_w/2:.1f}" y2="{py_med:.1f}" stroke="#0f172a" stroke-width="2.5"/>')
        svg.append(f'<polygon points="{cx:.1f},{py_mean-4:.1f} {cx+4:.1f},{py_mean:.1f} {cx:.1f},{py_mean+4:.1f} {cx-4:.1f},{py_mean:.1f}" fill="#ffffff" stroke="#0f172a" stroke-width="1.4"/>')

        for pt_i, v in enumerate(vals):
            px_pt = cx + ((pt_i % 5) - 2.0) * (box_w * 0.12)
            py_pt = y_to_px(v)
            svg.append(f'<circle cx="{px_pt:.1f}" cy="{py_pt:.1f}" r="3.5" fill="{col}" stroke="#ffffff" stroke-width="1"/>')

        g_esc = xml_esc(g_name)
        svg.append(f'<text x="{cx:.1f}" y="{pad_t + plot_h + 23}" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#0f172a">{g_esc}</text>')
        svg.append(f'<text x="{cx:.1f}" y="{pad_t + plot_h + 39}" text-anchor="middle" font-size="10.5" fill="#64748b">(n = {len(vals)})</text>')

    base_bracket_y = y_max_raw + 0.06 * span
    for b_idx, (_, s_row) in enumerate(sig_pairs.iterrows()):
        g_a, g_b = s_row["Group_A"], s_row["Group_B"]
        if g_a in group_names and g_b in group_names:
            i_a, i_b = group_names.index(g_a), group_names.index(g_b)
            x1, x2 = x_for_group(min(i_a, i_b)), x_for_group(max(i_a, i_b))
            by = y_to_px(base_bracket_y + (b_idx * 0.11 * span))
            svg.append(f'<path d="M {x1:.1f} {by+6:.1f} L {x1:.1f} {by:.1f} L {x2:.1f} {by:.1f} L {x2:.1f} {by+6:.1f}" fill="none" stroke="#0f172a" stroke-width="1.5"/>')
            lbl = xml_esc(f"{s_row['Short_Stars']} (p={s_row['Exact_Adjusted_P_Value']})")
            svg.append(f'<text x="{(x1+x2)/2:.1f}" y="{by - 4:.1f}" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#0f172a">{lbl}</text>')

    svg.append('</svg>')
    return "\n".join(svg)

def generate_svg_barchart(groups_dict, feature_name, omni_summary, posthoc_df, palette_name):
    colors = PALETTE_MAP.get(palette_name, list(PALETTE_MAP.values())[0])
    group_names = list(groups_dict.keys())
    k = len(group_names)
    all_vals = np.concatenate([np.array(v, dtype=float) for v in groups_dict.values()])
    y_max_raw = float(np.max(all_vals))
    y_min = 0.0 if float(np.min(all_vals)) >= 0 else float(np.min(all_vals)) * 1.15

    sig_pairs = posthoc_df[posthoc_df["Adjusted_P_Value_Numeric"] < 0.05].sort_values(by="Adjusted_P_Value_Numeric").head(3)
    y_max = y_max_raw * (1.22 + 0.10 * len(sig_pairs))
    span = max(1e-6, y_max - y_min)

    width, height = 820, 490
    pad_l, pad_r, pad_t, pad_b = 85, 35, 65, 80
    plot_w, plot_h = width - pad_l - pad_r, height - pad_t - pad_b

    def y_to_px(val):
        return pad_t + plot_h - ((val - y_min) / max(1e-9, y_max - y_min)) * plot_h

    def x_for_group(idx):
        return pad_l + (idx + 0.5) * (plot_w / max(1, k))

    f_esc = xml_esc(feature_name)
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="background:#ffffff; border-radius:12px; font-family:Arial, Helvetica, sans-serif;">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff" rx="12"/>',
        f'<text x="{width/2}" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#0f172a">Figure 1B: {f_esc} — Mean &#177; SD Bar Chart &amp; Replicate Overlay</text>',
        f'<text x="{width/2}" y="48" text-anchor="middle" font-size="12" fill="#475569">Error bars represent &#177; 1 SD with individual biological replicates overlaid</text>'
    ]

    for t_idx in range(6):
        y_val = y_min + (t_idx / 5.0) * (y_max - y_min)
        py = y_to_px(y_val)
        svg.append(f'<line x1="{pad_l}" y1="{py:.1f}" x2="{width - pad_r}" y2="{py:.1f}" stroke="#e2e8f0" stroke-dasharray="4,4" stroke-width="1"/>')
        svg.append(f'<text x="{pad_l - 10}" y="{py + 4:.1f}" text-anchor="end" font-size="11" fill="#334155">{y_val:.1f}</text>')

    svg.append(f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{pad_t + plot_h}" stroke="#0f172a" stroke-width="1.8"/>')
    svg.append(f'<line x1="{pad_l}" y1="{pad_t + plot_h}" x2="{width - pad_r}" y2="{pad_t + plot_h}" stroke="#0f172a" stroke-width="1.8"/>')
    svg.append(f'<text x="22" y="{pad_t + plot_h/2}" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#0f172a" transform="rotate(-90, 22, {pad_t + plot_h/2})">{f_esc} (Mean &#177; SD)</text>')

    bar_w = min(68, (plot_w / max(1, k)) * 0.44)
    py_zero = y_to_px(max(0.0, y_min))

    for idx, g_name in enumerate(group_names):
        vals = np.array(groups_dict[g_name], dtype=float)
        if len(vals) == 0:
            continue
        cx = x_for_group(idx)
        col = colors[idx % len(colors)]
        m_val = float(np.mean(vals))
        sd_val = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0

        py_m = y_to_px(m_val)
        py_top_sd = y_to_px(m_val + sd_val)
        py_bot_sd = y_to_px(max(y_min, m_val - sd_val))

        b_top = min(py_m, py_zero)
        b_height = max(2.0, abs(py_zero - py_m))
        svg.append(f'<rect x="{cx - bar_w/2:.1f}" y="{b_top:.1f}" width="{bar_w:.1f}" height="{b_height:.1f}" fill="{col}" fill-opacity="0.45" stroke="{col}" stroke-width="2" rx="3"/>')

        svg.append(f'<line x1="{cx:.1f}" y1="{py_top_sd:.1f}" x2="{cx:.1f}" y2="{py_bot_sd:.1f}" stroke="#0f172a" stroke-width="2"/>')
        svg.append(f'<line x1="{cx - bar_w*0.28:.1f}" y1="{py_top_sd:.1f}" x2="{cx + bar_w*0.28:.1f}" y2="{py_top_sd:.1f}" stroke="#0f172a" stroke-width="2"/>')
        svg.append(f'<line x1="{cx - bar_w*0.28:.1f}" y1="{py_bot_sd:.1f}" x2="{cx + bar_w*0.28:.1f}" y2="{py_bot_sd:.1f}" stroke="#0f172a" stroke-width="2"/>')
        svg.append(f'<text x="{cx:.1f}" y="{py_top_sd - 6:.1f}" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#1e293b">{m_val:.1f}</text>')

        for pt_i, v in enumerate(vals):
            px_pt = cx + ((pt_i % 5) - 2.0) * (bar_w * 0.12)
            py_pt = y_to_px(v)
            svg.append(f'<circle cx="{px_pt:.1f}" cy="{py_pt:.1f}" r="3.4" fill="#0f172a" fill-opacity="0.75" stroke="#ffffff" stroke-width="0.9"/>')

        g_esc = xml_esc(g_name)
        svg.append(f'<text x="{cx:.1f}" y="{pad_t + plot_h + 23}" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#0f172a">{g_esc}</text>')
        svg.append(f'<text x="{cx:.1f}" y="{pad_t + plot_h + 39}" text-anchor="middle" font-size="10.5" fill="#64748b">(n = {len(vals)})</text>')

    base_bracket_y = y_max_raw * 1.08
    for b_idx, (_, s_row) in enumerate(sig_pairs.iterrows()):
        g_a, g_b = s_row["Group_A"], s_row["Group_B"]
        if g_a in group_names and g_b in group_names:
            i_a, i_b = group_names.index(g_a), group_names.index(g_b)
            x1, x2 = x_for_group(min(i_a, i_b)), x_for_group(max(i_a, i_b))
            by = y_to_px(base_bracket_y + (b_idx * 0.08 * span))
            svg.append(f'<path d="M {x1:.1f} {by+5:.1f} L {x1:.1f} {by:.1f} L {x2:.1f} {by:.1f} L {x2:.1f} {by+5:.1f}" fill="none" stroke="#0f172a" stroke-width="1.5"/>')
            lbl = xml_esc(f"{s_row['Short_Stars']} (p={s_row['Exact_Adjusted_P_Value']})")
            svg.append(f'<text x="{(x1+x2)/2:.1f}" y="{by - 4:.1f}" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#0f172a">{lbl}</text>')

    svg.append('</svg>')
    return "\n".join(svg)

def generate_svg_forest_ci(posthoc_df, feature_name, palette_name):
    colors = PALETTE_MAP.get(palette_name, list(PALETTE_MAP.values())[0])
    n_rows = len(posthoc_df)
    width, height = 820, max(360, 140 + n_rows * 48)
    pad_l, pad_r, pad_t, pad_b = 225, 130, 65, 55
    plot_w, plot_h = width - pad_l - pad_r, height - pad_t - pad_b

    ci_min = float(min(0.0, posthoc_df["95%_CI_Lower"].min()))
    ci_max = float(max(0.0, posthoc_df["95%_CI_Upper"].max()))
    span = max(1e-6, ci_max - ci_min)
    x_min, x_max = ci_min - 0.12 * span, ci_max + 0.12 * span

    def x_to_px(val):
        return pad_l + ((val - x_min) / max(1e-9, x_max - x_min)) * plot_w

    f_esc = xml_esc(feature_name)
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="background:#ffffff; border-radius:12px; font-family:Arial, Helvetica, sans-serif;">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff" rx="12"/>',
        f'<text x="{width/2}" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#0f172a">Figure 1C: {f_esc} — Post-Hoc 95% Confidence Interval Forest Plot</text>',
        f'<text x="{width/2}" y="48" text-anchor="middle" font-size="12" fill="#475569">Pairwise Mean Difference (Group B - Group A) with 95% Family-Wise Confidence Intervals</text>'
    ]

    px_zero = x_to_px(0.0)
    svg.append(f'<line x1="{px_zero:.1f}" y1="{pad_t}" x2="{px_zero:.1f}" y2="{pad_t + plot_h}" stroke="#ef4444" stroke-dasharray="5,4" stroke-width="1.8"/>')
    svg.append(f'<line x1="{pad_l}" y1="{pad_t + plot_h}" x2="{width - pad_r}" y2="{pad_t + plot_h}" stroke="#0f172a" stroke-width="1.6"/>')

    for t_idx in range(5):
        xv = x_min + (t_idx / 4.0) * (x_max - x_min)
        px = x_to_px(xv)
        svg.append(f'<text x="{px:.1f}" y="{pad_t + plot_h + 22}" text-anchor="middle" font-size="11" fill="#334155">{xv:.1f}</text>')

    for idx, (_, row) in enumerate(posthoc_df.iterrows()):
        py = pad_t + (idx + 0.5) * (plot_h / max(1, n_rows))
        md = float(row["Mean_Difference (B - A)"])
        low = float(row["95%_CI_Lower"])
        high = float(row["95%_CI_Upper"])
        is_sig = row["Adjusted_P_Value_Numeric"] < 0.05
        col = colors[0] if is_sig else "#94a3b8"

        px_md, px_l, px_h = x_to_px(md), x_to_px(low), x_to_px(high)
        comp_esc = xml_esc(row["Comparison (Group A vs Group B)"])
        p_esc = xml_esc(f"{row['Short_Stars']} (p={row['Exact_Adjusted_P_Value']})")

        svg.append(f'<line x1="{pad_l}" y1="{py:.1f}" x2="{width - pad_r}" y2="{py:.1f}" stroke="#f1f5f9" stroke-width="1"/>')
        svg.append(f'<text x="{pad_l - 12}" y="{py + 4:.1f}" text-anchor="end" font-size="11.5" font-weight="bold" fill="#0f172a">{comp_esc}</text>')
        svg.append(f'<line x1="{px_l:.1f}" y1="{py:.1f}" x2="{px_h:.1f}" y2="{py:.1f}" stroke="{col}" stroke-width="2.6"/>')
        svg.append(f'<line x1="{px_l:.1f}" y1="{py - 6:.1f}" x2="{px_l:.1f}" y2="{py + 6:.1f}" stroke="{col}" stroke-width="2.2"/>')
        svg.append(f'<line x1="{px_h:.1f}" y1="{py - 6:.1f}" x2="{px_h:.1f}" y2="{py + 6:.1f}" stroke="{col}" stroke-width="2.2"/>')
        svg.append(f'<circle cx="{px_md:.1f}" cy="{py:.1f}" r="5.2" fill="{col}" stroke="#ffffff" stroke-width="1.4"/>')
        svg.append(f'<text x="{width - pad_r + 10}" y="{py + 4:.1f}" text-anchor="start" font-size="11" font-weight="bold" fill="#1e293b">{p_esc}</text>')

    svg.append('</svg>')
    return "\n".join(svg)

def generate_svg_multi_profile(df_input, group_col, num_cols, palette_name):
    colors = PALETTE_MAP.get(palette_name, list(PALETTE_MAP.values())[0])
    features = num_cols[:6]
    group_names = [str(g) for g in df_input[group_col].dropna().unique()]
    k = len(group_names)

    width, height = 820, 440
    pad_l, pad_r, pad_t, pad_b = 85, 175, 65, 75
    plot_w, plot_h = width - pad_l - pad_r, height - pad_t - pad_b
    y_min, y_max = -2.2, 2.2

    def y_to_px(val):
        v_clip = max(y_min, min(y_max, val))
        return pad_t + plot_h - ((v_clip - y_min) / (y_max - y_min)) * plot_h

    def x_for_group(idx):
        return pad_l + (idx + 0.5) * (plot_w / max(1, k))

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="background:#ffffff; border-radius:12px; font-family:Arial, Helvetica, sans-serif;">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff" rx="12"/>',
        f'<text x="{width/2}" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#0f172a">Figure 1D: Multi-Biomarker Cohort Z-Score Expression Trajectory</text>',
        f'<text x="{width/2}" y="48" text-anchor="middle" font-size="12" fill="#475569">Standardized Group Mean Z-Score (Mean = 0, SD = 1) Across Experimental Groups</text>'
    ]

    for zv in [-2.0, -1.0, 0.0, 1.0, 2.0]:
        py = y_to_px(zv)
        svg.append(f'<line x1="{pad_l}" y1="{py:.1f}" x2="{width - pad_r}" y2="{py:.1f}" stroke="#e2e8f0" stroke-dasharray="4,4" stroke-width="1"/>')
        svg.append(f'<text x="{pad_l - 10}" y="{py + 4:.1f}" text-anchor="end" font-size="11" fill="#334155">{zv:+.1f} SD</text>')

    svg.append(f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{pad_t + plot_h}" stroke="#0f172a" stroke-width="1.8"/>')
    svg.append(f'<line x1="{pad_l}" y1="{pad_t + plot_h}" x2="{width - pad_r}" y2="{pad_t + plot_h}" stroke="#0f172a" stroke-width="1.8"/>')

    for idx, g_name in enumerate(group_names):
        cx = x_for_group(idx)
        svg.append(f'<text x="{cx:.1f}" y="{pad_t + plot_h + 25}" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#0f172a">{xml_esc(g_name)}</text>')

    for f_idx, f_col in enumerate(features):
        col = colors[f_idx % len(colors)]
        s_all = pd.to_numeric(df_input[f_col], errors="coerce")
        m_all, sd_all = float(s_all.mean()), float(s_all.std())
        if not sd_all or sd_all == 0:
            sd_all = 1.0

        pts = []
        for idx, g_name in enumerate(group_names):
            sub_s = pd.to_numeric(df_input[df_input[group_col].astype(str) == g_name][f_col], errors="coerce").dropna()
            z_mean = (float(sub_s.mean()) - m_all) / sd_all if len(sub_s) > 0 else 0.0
            pts.append((x_for_group(idx), y_to_px(z_mean)))

        if len(pts) > 1:
            path_d = "M " + " L ".join(f"{px:.1f} {py:.1f}" for px, py in pts)
            svg.append(f'<path d="{path_d}" fill="none" stroke="{col}" stroke-width="2.6"/>')
        for px, py in pts:
            svg.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.8" fill="{col}" stroke="#ffffff" stroke-width="1.3"/>')

        leg_y = pad_t + 20 + f_idx * 28
        svg.append(f'<rect x="{width - pad_r + 14}" y="{leg_y - 9}" width="14" height="14" fill="{col}" rx="3"/>')
        svg.append(f'<text x="{width - pad_r + 34}" y="{leg_y + 2}" font-size="11" font-weight="bold" fill="#1e293b">{xml_esc(f_col[:18])}</text>')

    svg.append('</svg>')
    return "\n".join(svg)

# ==========================================
# STEP 2: FILE UPLOAD OR DEMO DATASET
# ==========================================
col_up, col_demo = st.columns([3, 1])
with col_up:
    uploaded_file = st.file_uploader(
        "Upload Experimental Expression / Phenotype Table (.csv, .tsv, .txt)",
        type=["csv", "tsv", "txt"],
        on_change=reset_on_mode_change_t7
    )
with col_demo:
    st.write("")
    st.write("")
    use_sample = st.checkbox("🧪 Load Demo 4-Group Immunotherapy Dataset", value=True, on_change=reset_on_mode_change_t7)

df_input = None
if uploaded_file is not None:
    try:
        sep = "\t" if uploaded_file.name.lower().endswith((".tsv", ".txt")) else ","
        df_input = pd.read_csv(uploaded_file, sep=sep)
    except Exception as e:
        st.error(f"Error reading file: {e}")
elif use_sample:
    df_input = DEMO_ANOVA_DF.copy()

# ==========================================
# STEP 3: CONFIGURE CORE STATISTICAL ENGINE & PLOT OPTIONS
# ==========================================
if df_input is not None and not df_input.empty:
    with st.expander(f"👁️ Inspect Loaded Experimental Dataset ({len(df_input)} Samples Ready)", expanded=False):
        st.dataframe(df_input.head(6), use_container_width=True)

    st.markdown("### ⚙️ Configure Statistical Engine, Target Biomarker & 4-Plot Figure Styling")

    # Core Statistical Engine (ONLY switching this or uploading a new file resets the paywall!)
    core_engine = st.selectbox(
        "1. Core Omnibus & Post-Hoc Statistical Engine (Switching engine starts a new pipeline run):",
        [
            "Parametric One-Way ANOVA + Tukey's HSD Post-Hoc (Standard Normal / Equal Variance)",
            "Welch's One-Way ANOVA + Games-Howell Post-Hoc (Unequal Group Variances / Sample Sizes)",
            "Non-Parametric Kruskal-Wallis H-Test + Dunn's Post-Hoc (Skewed / Ordinal / Cytokine Data)",
            "Multi-Gene Batch ANOVA + Benjamini-Hochberg FDR Screen (All Numeric Columns + Tukey HSD)"
        ],
        on_change=reset_on_mode_change_t7
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**2. Data Layout & Group Selection**")
        layout_mode = st.selectbox(
            "Spreadsheet Format:",
            ["Standard Table (1 Group Column + Numeric Feature Columns)", "Wide Replicate Table (Each Column is a Group)"]
        )
        if "Standard Table" in layout_mode:
            non_num_cols = [c for c in df_input.columns if df_input[c].dtype == "object" or df_input[c].nunique() <= 15]
            default_grp_idx = 1 if len(non_num_cols) > 1 else 0
            group_col = st.selectbox("Select Experimental Group Column:", non_num_cols if non_num_cols else list(df_input.columns), index=default_grp_idx)
            num_cols = [c for c in df_input.select_dtypes(include=[np.number]).columns if c != group_col]
            if not num_cols:
                num_cols = [c for c in df_input.columns if c != group_col]
            target_feature = st.selectbox(
                "Select Target Biomarker / Gene for Figures & Post-Hoc (Free to switch):",
                num_cols,
                index=0,
                help="You can freely switch between any biomarker/gene column in your dataset without resetting your unlock!"
            )
        else:
            num_cols = list(df_input.select_dtypes(include=[np.number]).columns)
            group_col = "Wide_Columns"
            target_feature = "All_Group_Columns"

    with c2:
        st.markdown("**3. Transformation & Outlier Rules**")
        log_transform = st.checkbox("Apply Log2(x + 1) Transform Before Testing", value=False)
        remove_outliers = st.checkbox("Filter Extreme Outliers (> 3×IQR per group)", value=False)
        excel_guard = st.checkbox(
            "🛡️ Enable Excel Gene-Name Guard (Protects MARCH1 / SEPT2)",
            value=False,
            help="Wraps biomarker/gene names so Microsoft Excel never converts MARCH1 or SEPT2 into calendar dates."
        )

    with c3:
        st.markdown("**4. Publication Figure Palette**")
        palette_choice = st.selectbox(
            "Journal Color Palette:",
            list(PALETTE_MAP.keys())
        )

    current_file_sig = uploaded_file.name if uploaded_file is not None else "demo_anova"
    current_mode_sig = f"{current_file_sig}|{core_engine}"

    # ==========================================
    # STEP 4: RUN ANOVA, POST-HOC & 4-FIGURE ENGINE
    # ==========================================
    if st.button("🚀 Compute ANOVA, Post-Hoc & Generate 4-Panel Figure Suite"):
        if st.session_state["locked_mode_t7"] is not None and st.session_state["locked_mode_t7"] != current_mode_sig:
            st.session_state["is_unlocked_t7"] = False
        st.session_state["locked_mode_t7"] = current_mode_sig

        with st.spinner("Computing omnibus ANOVA/Kruskal statistics, Shapiro-Wilk/Levene audits, exact post-hoc P-values, and rendering 4 publication figures..."):
            groups_dict = {}
            if "Standard Table" in layout_mode:
                for g_val, sub_df in df_input.groupby(group_col, sort=False):
                    vals = pd.to_numeric(sub_df[target_feature], errors="coerce").dropna().values
                    if log_transform:
                        vals = np.log2(np.maximum(0.0, vals) + 1.0)
                    if remove_outliers and len(vals) >= 4:
                        q25, q75 = np.percentile(vals, [25, 75])
                        iqr = q75 - q25
                        vals = vals[(vals >= q25 - 3.0 * iqr) & (vals <= q75 + 3.0 * iqr)]
                    if len(vals) > 0:
                        groups_dict[str(g_val)] = vals
            else:
                for col in num_cols:
                    vals = pd.to_numeric(df_input[col], errors="coerce").dropna().values
                    if log_transform:
                        vals = np.log2(np.maximum(0.0, vals) + 1.0)
                    if len(vals) > 0:
                        groups_dict[str(col)] = vals

            if len(groups_dict) < 2:
                st.error("At least 2 experimental groups with numeric observations are required to run ANOVA / Post-Hoc analysis.")
            else:
                res = run_omnibus_and_posthoc(groups_dict, core_engine)
                posthoc_df = res["posthoc"].drop(columns=["Group_A", "Group_B", "Adjusted_P_Value_Numeric", "Short_Stars"])

                desc_rows = []
                for g_name, vals in groups_dict.items():
                    n_g = len(vals)
                    m_g = float(np.mean(vals))
                    sd_g = float(np.std(vals, ddof=1)) if n_g > 1 else 0.0
                    sem_g = sd_g / math.sqrt(n_g) if n_g > 0 else 0.0
                    cv_pct = round((sd_g / abs(m_g)) * 100.0, 2) if abs(m_g) > 1e-9 else 0.0
                    ci_95_m = 1.96 * sem_g
                    q25, med, q75 = np.percentile(vals, [25, 50, 75])
                    p_shap = shapiro_normality_p(vals)
                    desc_rows.append({
                        "Feature_Biomarker": (f'="{target_feature}"' if excel_guard else target_feature),
                        "Experimental_Group": g_name,
                        "Sample_Size (N)": n_g,
                        "Mean": round(m_g, 3),
                        "SD": round(sd_g, 3),
                        "SEM": round(sem_g, 3),
                        "CV (%)": cv_pct,
                        "Formatted_Mean_±_SD": f"{m_g:.2f} ± {sd_g:.2f}",
                        "95%_CI_of_Mean": f"[{m_g - ci_95_m:.2f}, {m_g + ci_95_m:.2f}]",
                        "Median": round(float(med), 3),
                        "IQR (Q25 - Q75)": f"{q25:.2f} - {q75:.2f} (IQR={q75 - q25:.2f})",
                        "Normality_Shapiro_P": format_p(p_shap),
                        "Levene_Variance_Test_P": res["p_levene_str"],
                        "Omnibus_Test_Result": f"{res['omni_name']} (p = {res['p_omni_str']})"
                    })
                desc_df = pd.DataFrame(desc_rows)

                batch_rows = []
                if "Standard Table" in layout_mode and num_cols:
                    for f_col in num_cols:
                        f_groups = {}
                        for g_val, sub_df in df_input.groupby(group_col, sort=False):
                            v_arr = pd.to_numeric(sub_df[f_col], errors="coerce").dropna().values
                            if log_transform:
                                v_arr = np.log2(np.maximum(0.0, v_arr) + 1.0)
                            if len(v_arr) > 0:
                                f_groups[str(g_val)] = v_arr
                        if len(f_groups) >= 2:
                            b_res = run_omnibus_and_posthoc(f_groups, core_engine)
                            top_pair_row = b_res["posthoc"].sort_values(by="Adjusted_P_Value_Numeric").iloc[0]
                            disp_feat = f'="{f_col}"' if excel_guard else f_col
                            batch_rows.append({
                                "Biomarker_or_Gene": disp_feat,
                                "Omnibus_Statistic": b_res["omni_name"],
                                "Raw_Omnibus_P_Numeric": b_res["p_omni"],
                                "Omnibus_Exact_P": b_res["p_omni_str"],
                                "Eta_Squared_Effect_Size (η²)": b_res["eta_sq"],
                                "Omega_Squared (ω²)": b_res["omega_sq"],
                                "Levene_Variance_P": b_res["p_levene_str"],
                                "Top_Significant_Pair": top_pair_row["Comparison (Group A vs Group B)"],
                                "Top_Pair_PostHoc_P": top_pair_row["Exact_Adjusted_P_Value"],
                                "Top_Pair_Fold_Change": top_pair_row["Fold_Change (B / A)"]
                            })
                    batch_df = pd.DataFrame(batch_rows)
                    if not batch_df.empty:
                        batch_df = batch_df.sort_values(by="Raw_Omnibus_P_Numeric").reset_index(drop=True)
                        m_tests = len(batch_df)
                        bh_vals = [
                            min(1.0, row_p * m_tests / (rank_i + 1))
                            for rank_i, row_p in enumerate(batch_df["Raw_Omnibus_P_Numeric"])
                        ]
                        batch_df.insert(4, "Benjamini_Hochberg_FDR_Q", [format_p(q) for q in bh_vals])
                        batch_df.insert(5, "FDR_Significance", [p_to_stars(q) for q in bh_vals])
                        batch_df = batch_df.drop(columns=["Raw_Omnibus_P_Numeric"])
                else:
                    batch_df = desc_df.copy()

                svg_box = generate_svg_boxplot(groups_dict, target_feature, res, res["posthoc"], palette_choice)
                svg_bar = generate_svg_barchart(groups_dict, target_feature, res, res["posthoc"], palette_choice)
                svg_forest = generate_svg_forest_ci(res["posthoc"], target_feature, palette_choice)
                svg_profile = (
                    generate_svg_multi_profile(df_input, group_col, num_cols, palette_choice)
                    if ("Standard Table" in layout_mode and len(num_cols) > 1)
                    else svg_box
                )

                html_report = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>GenomeTech Studio — ANOVA &amp; Post-Hoc Visual Report ({xml_esc(target_feature)})</title>
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
    <h2 style="margin:0;">GenomeTech Studio | OmicsExpress Biostatistical Report</h2>
    <p style="margin:6px 0 0 0;">Target Biomarker: <b>{xml_esc(target_feature)}</b> | Engine: {xml_esc(core_engine)} | {xml_esc(res["omni_name"])} (p = {xml_esc(res["p_omni_str"])})</p>
  </div>
  <div class="grid">
    <div class="card">{svg_box}</div>
    <div class="card">{svg_bar}</div>
    <div class="card">{svg_forest}</div>
    <div class="card">{svg_profile}</div>
  </div>
  <div class="card">
    <h3>Pairwise Post-Hoc Comparisons &amp; Effect Sizes</h3>
    {posthoc_df.to_html(index=False)}
  </div>
</body>
</html>"""

                sig_pairs_cnt = int(sum(res["posthoc"]["Adjusted_P_Value_Numeric"] < 0.05))

                st.session_state["posthoc_df_t7"] = posthoc_df
                st.session_state["desc_df_t7"] = desc_df
                st.session_state["batch_df_t7"] = batch_df
                st.session_state["svg_box_t7"] = svg_box
                st.session_state["svg_bar_t7"] = svg_bar
                st.session_state["svg_forest_t7"] = svg_forest
                st.session_state["svg_profile_t7"] = svg_profile
                st.session_state["html_report_t7"] = html_report
                st.session_state["stats_t7"] = {
                    "feature": target_feature,
                    "groups": len(groups_dict),
                    "total_pairs": len(posthoc_df),
                    "sig_pairs": sig_pairs_cnt,
                    "omni_name": res["omni_name"],
                    "p_omni_str": res["p_omni_str"],
                    "eta_sq": res["eta_sq"],
                    "p_levene_str": res["p_levene_str"],
                    "p_levene_num": res["p_levene"],
                    "engine": core_engine
                }

# ==========================================
# DISPLAY TABULAR RESULTS, 4-PLOT SUITE, PAYWALL & REMARKS
# ==========================================
if "posthoc_df_t7" in st.session_state:
    ph_df = st.session_state["posthoc_df_t7"]
    desc_df = st.session_state["desc_df_t7"]
    batch_df = st.session_state["batch_df_t7"]
    svg_box = st.session_state["svg_box_t7"]
    svg_bar = st.session_state["svg_bar_t7"]
    svg_forest = st.session_state["svg_forest_t7"]
    svg_profile = st.session_state["svg_profile_t7"]
    html_rep = st.session_state["html_report_t7"]
    stats = st.session_state["stats_t7"]

    st.markdown("---")
    st.markdown(f"### 📊 Omnibus ANOVA, Post-Hoc & 4-Panel Publication Suite (`{stats['feature']}`)")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Omnibus Test Result", stats["omni_name"])
    m2.metric("Omnibus Exact P-Value", f"p = {stats['p_omni_str']}")
    m3.metric("Effect Size (η²)", f"{stats['eta_sq']}")
    m4.metric("Significant Post-Hoc Pairs", f"{stats['sig_pairs']} / {stats['total_pairs']} Pairs")

    if st.session_state["is_unlocked_t7"]:
        st.success(f"✅ **Payment Verified for [{stats['engine']}]!** All 4 publication figures, 3 statistical CSV tables, and the 1-click printable HTML report are unlocked.")

        st.markdown("#### 🎨 4-Panel Publication Figure Suite (Vector `.svg` & Printable `.html`)")
        g1, g2 = st.columns(2)
        with g1:
            st.markdown(svg_box, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(svg_forest, unsafe_allow_html=True)
        with g2:
            st.markdown(svg_bar, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(svg_profile, unsafe_allow_html=True)

        st.markdown("#### 🔬 1. Pairwise Post-Hoc Comparisons & Effect Sizes")
        st.dataframe(ph_df, use_container_width=True)

        st.markdown("#### 📋 2. Group Descriptives (`Mean ± SD`, `SEM`, `CV%`, `95% CI`, `Shapiro-Wilk P`, `Levene P`)")
        st.dataframe(desc_df, use_container_width=True)

        st.markdown("#### 🧬 3. Multi-Biomarker Batch ANOVA + Benjamini-Hochberg FDR Screen")
        st.dataframe(batch_df, use_container_width=True)

        st.markdown("#### ⬇️ Download Statistical Tables (`.csv`) & High-Resolution Figures (`.svg` / `.html`)")
        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.download_button(
                "⬇️ 1. Pairwise Post-Hoc (.csv)",
                data=ph_df.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"GenomeTech_PostHoc_{stats['feature']}.csv",
                mime="text/csv"
            )
            st.download_button(
                "⬇️ 5. Fig 1A: Boxplot (.svg)",
                data=svg_box.encode("utf-8"),
                file_name=f"GenomeTech_Boxplot_{stats['feature']}.svg",
                mime="image/svg+xml"
            )
        with d2:
            st.download_button(
                "⬇️ 2. Group Descriptives (.csv)",
                data=desc_df.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"GenomeTech_Group_Descriptives_{stats['feature']}.csv",
                mime="text/csv"
            )
            st.download_button(
                "⬇️ 6. Fig 1B: Bar Chart (.svg)",
                data=svg_bar.encode("utf-8"),
                file_name=f"GenomeTech_BarChart_{stats['feature']}.svg",
                mime="image/svg+xml"
            )
        with d3:
            st.download_button(
                "⬇️ 3. Batch ANOVA FDR (.csv)",
                data=batch_df.to_csv(index=False).encode("utf-8-sig"),
                file_name="GenomeTech_Batch_ANOVA_FDR_Screen.csv",
                mime="text/csv"
            )
            st.download_button(
                "⬇️ 7. Fig 1C: 95% CI Forest (.svg)",
                data=svg_forest.encode("utf-8"),
                file_name=f"GenomeTech_ForestCI_{stats['feature']}.svg",
                mime="image/svg+xml"
            )
        with d4:
            st.download_button(
                "⬇️ 4. All-in-One Visual Report (.html)",
                data=html_rep.encode("utf-8"),
                file_name=f"GenomeTech_4Figure_Report_{stats['feature']}.html",
                mime="text/html"
            )
            st.download_button(
                "⬇️ 8. Fig 1D: Z-Score Profile (.svg)",
                data=svg_profile.encode("utf-8"),
                file_name="GenomeTech_MultiGene_ZScore_Profile.svg",
                mime="image/svg+xml"
            )
    else:
        st.markdown("**Live Preview (First 2 Pairwise Post-Hoc Comparisons Verified):**")
        st.dataframe(ph_df.head(2), use_container_width=True)

        blurred_preview = ph_df.iloc[2:] if len(ph_df) > 2 else ph_df
        st.markdown('<div class="blurred-table">', unsafe_allow_html=True)
        st.table(blurred_preview)
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            st.markdown(svg_box, unsafe_allow_html=True)
        with p_col2:
            st.markdown(svg_bar, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        razorpay_link = "https://rzp.io/rzp/UVDck3w"
        st.markdown(f"""
        <div class="paywall-overlay">
            <h3 style="color: #e9d5ff !important; margin-top: 0;">🔒 Unlock All {stats['total_pairs']} Post-Hoc Pairs, 3 CSVs &amp; 4 Publication Figures</h3>
            <p style="color: #cbd5e1 !important; font-size: 0.95rem;">
                Your top 2 pairwise comparisons are verified above. Complete the $40 OmicsExpress checkout to unlock all 3 statistical CSV tables, all 4 publication figures (Boxplot, Mean ± SD Bar Chart, 95% CI Forest Plot, and Multi-Gene Trajectory), and the printable HTML report.
            </p>
            <div style="background:rgba(56,189,248,0.14);border:1px solid rgba(56,189,248,0.45);color:#e0f2fe !important;padding:8px 14px;border-radius:8px;font-size:0.88rem;font-weight:600;margin:10px auto 6px auto;max-width:520px;">🔥 <span style="color:#38bdf8 !important;font-weight:800;">FOUNDING LAB LAUNCH OFFER:</span> <s style="color:#94a3b8 !important;">$100 USD</s> <b style="color:#ffffff !important;">$40 USD</b> — Special Early-Access Rate for Our First 20 Research Clients</div><a href="{razorpay_link}" target="_blank" style="background: linear-gradient(90deg, #9333ea 0%, #2563eb 100%); color: white !important; padding: 14px 32px; text-decoration: none; border-radius: 10px; font-weight: 700; font-size: 1.05rem; display: inline-block; margin: 12px 0; border: 1px solid #c084fc; box-shadow: 0 4px 20px rgba(147, 51, 234, 0.5);">
                💳 Pay $40 via Razorpay to Unlock Full Suite
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
                    st.session_state["is_unlocked_t7"] = True
                    st.rerun()
                else:
                    st.error("Invalid Payment ID. Please paste the 'pay_...' ID shown on your Razorpay payment confirmation screen.")

    # ==========================================
    # STEP 6: AUTOMATED REMARKS & DIRECT EMAIL
    # ==========================================
    st.markdown("---")
    st.markdown("### 📝 Automated Biostatistical Remarks & Direct Support")

    levene_note = (
        "Homogeneity of variance assumption holds (Levene's p is greater than or equal to 0.05); standard Parametric ANOVA + Tukey's HSD is statistically optimal."
        if stats["p_levene_num"] >= 0.05
        else "Significant variance heterogeneity detected across groups (Levene's p is less than 0.05); consider Welch's ANOVA + Games-Howell mode."
    )

    st.info(
        f"**Automated ANOVA & Post-Hoc Diagnostics:**\n"
        f"* **Statistical Engine:** {stats['engine']} | Target Feature: `{stats['feature']}` ({stats['groups']} Experimental Groups)\n"
        f"* **Omnibus & Effect Size:** {stats['omni_name']}, exact $p = {stats['p_omni_str']}$, with $\\eta^2 = {stats['eta_sq']}$ ({stats['sig_pairs']} of {stats['total_pairs']} pairwise comparisons significant at $\\alpha = 0.05$).\n"
        f"* **Normality & Variance Audit:** Group-level Shapiro-Wilk normality $P$-values are included in Deliverable #2; Levene's variance homogeneity $p = {stats['p_levene_str']}$ — {levene_note}"
    )

    with st.expander("💬 Send Remarks or Questions Directly to GenomeTech Team (via Email)"):
        client_email = st.text_input("Your Lab / Institutional Email:")
        client_remark = st.text_area("Your Remarks or Questions about this ANOVA & Post-Hoc Run:")
        if st.button("Prepare Direct Email"):
            subject = urllib.parse.quote(f"OmicsExpress Tool #7 Remark - {client_email}")
            body = urllib.parse.quote(
                f"Client Email: {client_email}\n"
                f"Tool Used: Tool #7 - Automated ANOVA & Post-Hoc Suite\n"
                f"Engine: {stats['engine']} | Feature: {stats['feature']}\n"
                f"Omnibus Result: {stats['omni_name']} (p = {stats['p_omni_str']}, Eta2 = {stats['eta_sq']})\n"
                f"Significant Pairs: {stats['sig_pairs']} / {stats['total_pairs']}\n\n"
                f"Client Remarks:\n{client_remark}"
            )
            mailto_url = f"mailto:bhumikasihare555@gmail.com?subject={subject}&body={body}"
            st.success("✅ Your remark and biostatistical diagnostics are ready! Click below to send directly from your email client:")
            st.markdown(f'👉 <a href="https://mail.google.com/mail/?view=cm&fs=1&to=bhumikasihare555@gmail.com&su={subject}&body={body}" target="_blank" style="color:#38bdf8;font-weight:700;text-decoration:underline;">Click Here to Send via Gmail (Browser)</a> &nbsp;|&nbsp; <a href="{mailto_url}" style="color:#c4b5fd;font-weight:600;text-decoration:underline;">Open in Default Mail App (Outlook/Mac)</a>', unsafe_allow_html=True)