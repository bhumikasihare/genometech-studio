import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Tier 5: Microbiome 16S rRNA Pipeline | GenomeTech Studio",
    page_icon="🦠",
    layout="wide"
)

st.markdown("""
<style>
    .stApp {
        background: radial-gradient(circle at top right, #1e1b4b 0%, #0f172a 60%, #020617 100%);
        color: #f1f5f9 !important;
        font-family: 'Inter', sans-serif;
    }
    .tier-header {
        background: linear-gradient(90deg, #10b981 0%, #047857 100%);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        border: 1px solid rgba(52, 211, 153, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# Navigation header back to main app
if st.button("← Back to OmicsExpress Launchpad"):
    st.query_params.clear()
    st.switch_page("app.py")

st.markdown("""
<div class="tier-header">
    <span style="background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 999px; font-size: 0.8rem; font-weight: bold;">TIER 5 ADVANCED PIPELINE</span>
    <h1 style="color: white; margin-top: 10px;">Microbiome (16S rRNA) Profiling Suite</h1>
    <p style="color: #a7f3d0; margin: 0;">End-to-end amplicon sequencing analysis using QIIME2 pipelines, operational taxonomic unit (OTU) picking, and diversity stats.</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 2], gap="large")

with col1:
    st.markdown("### 🎛️ Select Modules")
    
    use_bundle = st.checkbox("🔥 Full Tier 5 Bundle (Save $100)", value=True, key="t5_bundle")
    
    if not use_bundle:
        inc_qiime = st.checkbox("QIIME2 Execution ($150)", value=True)
        inc_taxa = st.checkbox("Taxonomic Class. ($100)", value=True)
        inc_diversity = st.checkbox("Alpha/Beta Diversity ($80)", value=True)
        inc_abundance = st.checkbox("Abundance Charts ($70)", value=True)
        
        total_price = (150 if inc_qiime else 0) + \
                      (100 if inc_taxa else 0) + \
                      (80 if inc_diversity else 0) + \
                      (70 if inc_abundance else 0)
    else:
        total_price = 400
        st.info("Bundle active: All 4 microbiome modules included for $400.")

    st.markdown(f"### Total Investment: <span style='color: #34d399;'>${total_price} USD</span>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("**Ready to submit your FASTQ / Amplicon data?**")
    client_email = st.text_input("Your Research Email:", placeholder="microbiologist@university.edu", key="t5_email")
    
    if st.button("Proceed to Project Intake & 30% Advance ($" + str(round(total_price * 0.3, 2)) + ")", key="t5_btn"):
        if client_email:
            st.success(f"Intake reservation generated for {client_email}! Redirecting...")
            st.markdown(f"[Click here to submit dataset & requirements via Google Form](https://forms.gle/9gqcYrc3NjtAn7z59)")
        else:
            st.warning("Please enter your research email address.")

with col2:
    st.markdown("### 📊 Interactive Preview & Taxonomic Inspector")
    st.markdown("Inspect mock relative abundance and operational taxonomic unit (OTU) breakdown:")
    
    # Mock microbiome summary table
    mock_microbiome = pd.DataFrame({
        "Phylum": ["Firmicutes", "Bacteroidetes", "Actinobacteria", "Proteobacteria", "Verrucomicrobia"],
        "Dominant Genera": ["Faecalibacterium, Roseburia", "Bacteroides, Prevotella", "Bifidobacterium", "Escherichia, Klebsiella", "Akkermansia"],
        "Mean Relative Abundance (%)": [52.4, 31.8, 8.2, 5.1, 2.5],
        "Alpha Diversity (Chao1 Index)": [342.1, 289.4, 198.2, 145.0, 92.6]
    })
    
    st.dataframe(mock_microbiome, use_container_width=True)
    
    st.markdown("#### 🔬 Sample Taxonomic Barplot Preview")
    st.markdown("*(Below is a preview of the sample-wise phylum composition charts delivered with your analysis)*")
    
    # Generate mock bar chart data
    chart_data = pd.DataFrame(
        np.random.rand(5, 3) * 100,
        index=['Sample_Control_1', 'Sample_Control_2', 'Sample_Treatment_1', 'Sample_Treatment_2', 'Sample_Treatment_3'],
        columns=['Firmicutes', 'Bacteroidetes', 'Proteobacteria']
    )
    st.bar_chart(chart_data)