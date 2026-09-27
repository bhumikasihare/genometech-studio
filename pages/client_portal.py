import streamlit as st
import pandas as pd
import requests
import json

st.set_page_config(
    page_title="Client Portal | GenomeTech Studio",
    page_icon="🧬",
    layout="wide"
)

st.markdown("""
<style>
    .stApp {
        background: radial-gradient(circle at top right, #1e1b4b 0%, #0f172a 60%, #020617 100%);
        color: #f1f5f9 !important;
        font-family: 'Inter', sans-serif;
    }
    .portal-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Your saved backend endpoints
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSsQkADNSxfsePaLn1b4RPN018cIyO8bHnfRtmIYGAawnRtgjBGhWhM35GMRhNrVvfcf3wZE7indbHl/pub?output=csv"
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbz-pKMSgW-i32k9XAYEPaybbE5V4MV9Pm2boob3PFW10JwqahSPZjlFD1nIoS31KtLt/exec"

# Navigation header back to home website
if st.button("← Back to GenomeTech Studio"):
    st.query_params.clear()
    st.switch_page("app.py")

st.markdown("""
<div style="text-align: center; padding: 1.5rem 0;">
    <span style="background: rgba(59, 130, 246, 0.2); color: #60a5fa; padding: 4px 14px; border-radius: 999px; font-size: 0.8rem; font-weight: bold; border: 1px solid rgba(59, 130, 246, 0.4);">SECURE CLIENT PORTAL</span>
    <h1 style="color: white; margin-top: 10px;">Research Project Dashboard</h1>
    <p style="color: #94a3b8; max-width: 600px; margin: 0 auto;">Log in with your registered research email and client ID to track live pipeline progress, download deliverables, and request revisions.</p>
</div>
""", unsafe_allow_html=True)

# --- SESSION STATE & LOGIN CHECK ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.client_email = ""
    st.session_state.client_id = ""

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="portal-card">', unsafe_allow_html=True)
        st.markdown("### 🔐 Client Sign In")
        
        login_email = st.text_input("Research Email Address", placeholder="pi@university.edu")
        login_client_id = st.text_input("Client ID (e.g. GT-CLIENT-101)", placeholder="GT-CLIENT-...")
        
        if st.button("Access Portal Dashboard", use_container_width=True):
            if login_email and login_client_id:
                try:
                    df = pd.read_csv(CSV_URL)
                    # Clean column names to avoid whitespace issues
                    df.columns = df.columns.str.strip()
                    
                    # Match email and client ID
                    match = df[(df['Client Email'].str.strip().str.lower() == login_email.strip().lower()) & 
                               (df['Client ID'].str.strip() == login_client_id.strip())]
                    
                    if not match.empty:
                        st.session_state.logged_in = True
                        st.session_state.client_email = login_email.strip()
                        st.session_state.client_id = login_client_id.strip()
                        st.rerun()
                    else:
                        st.error("No active projects found matching this Email and Client ID. Please check your credentials.")
                except Exception as e:
                    st.error(f"Could not connect to database sheet. Please try again shortly. (Error: {e})")
            else:
                st.warning("Please fill in both your email and client ID.")
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- LOGGED IN DASHBOARD ---
    st.success(f"Welcome back! Authenticated as: **{st.session_state.client_email}** ({st.session_state.client_id})")
    
    if st.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    try:
        df = pd.read_csv(CSV_URL)
        df.columns = df.columns.str.strip()
        
        # Get all projects for this client
        client_projects = df[df['Client ID'].str.strip() == st.session_state.client_id]
        
        if client_projects.empty:
            st.warning("No projects currently logged for this Client ID.")
        else:
            # Project Selector if they have multiple project IDs
            project_ids = client_projects['Project ID'].astype(str).tolist()
            selected_proj_id = st.selectbox("Select Project ID:", project_ids)
            
            # Filter row for selected project
            proj_data = client_projects[client_projects['Project ID'].astype(str) == selected_proj_id].iloc[0]
            
            # Read metrics from sheet
            tier_name = proj_data.get('Tier Selected', 'Custom Pipeline')
            modules = proj_data.get('Modules Chosen', 'N/A')
            status = proj_data.get('Status', 'Pending')
            progress = int(proj_data.get('Progress Percent', 0))
            init_link = proj_data.get('Initial Deliverables Link', '')
            pay_70_link = proj_data.get('Remaining Payment (70%) Link', '')
            pay_70_status = str(proj_data.get('70% Payment Status', 'Unpaid')).strip()
            final_link = proj_data.get('Final Deliverables Link', '')
            redo_link = proj_data.get('Redo Deliverable Link', '')
            
            # --- DASHBOARD LAYOUT ---
            st.markdown(f"""
            <div class="portal-card">
                <h3>📁 Active Project: <span style="color: #38bdf8;">{selected_proj_id}</span></h3>
                <p><b>Tier:</b> {tier_name} | <b>Modules:</b> {modules}</p>
                <hr style="border-color: rgba(255,255,255,0.1); margin: 1rem 0;">
                <p><b>Current Workflow Status:</b> <span style="background: rgba(16,185,129,0.2); color: #34d399; padding: 2px 10px; border-radius: 99px; font-size: 0.85rem;">{status}</span></p>
            </div>
            """, unsafe_allow_html=True)
            
            # Progress Bar
            st.markdown(f"#### Pipeline Progress ({progress}%)")
            st.progress(progress / 100.0)
            
            col_a, col_b = st.columns(2, gap="large")
            
            with col_a:
                st.markdown("### 🔍 Initial Previews & Reports")
                if pd.notna(init_link) and str(init_link).startswith("http"):
                    st.markdown(f"[📥 Download Initial QC / Preview Package]({init_link})")
                else:
                    st.info("Initial previews will appear here once work begins.")
                
                # 70% Payment Gate
                st.markdown("### 💳 Final Payment (70%)")
                if pay_70_status.lower() == "paid":
                    st.success("✅ Remaining 70% payment received! Full files unlocked below.")
                else:
                    st.warning("⚠️ Remaining 70% balance pending. Unlock your final publication-ready figures & data tables below.")
                    if pd.notna(pay_70_link) and str(pay_70_link).startswith("http"):
                        st.markdown(f"[Proceed to Secure 70% Razorpay Checkout]({pay_70_link})")
                    else:
                        st.info("Payment link will be activated by admin upon reaching 100% completion.")
                        
                # Final Deliverables Unlock
                st.markdown("### 📦 Final Deliverables")
                if pay_70_status.lower() == "paid" or progress == 100:
                    if pd.notna(final_link) and str(final_link).startswith("http"):
                        st.markdown(f"🎉 **[Download Final Cleaned CSVs & Vector SVG Package]({final_link})**")
                    else:
                        st.info("Final files are being prepared for release.")
                else:
                    st.markdown("*Locked until 70% balance is settled.*")

            with col_b:
                # Redo Request Section
                st.markdown("### 🔄 Request Revision / Redo")
                st.markdown("Need modifications on formula or math parts? Submit your revision notes below:")
                
                redo_choice = st.radio("Do you need changes?", ["No", "Yes"], key=f"redo_{selected_proj_id}")
                
                if redo_choice == "Yes":
                    redo_notes = st.text_area("Describe required revisions:", placeholder="Please adjust statistical thresholds or filter parameters...")
                    if st.button("Submit Redo Request"):
                        if redo_notes:
                            payload = {
                                "clientEmail": st.session_state.client_email,
                                "projectID": selected_proj_id,
                                "action": "redo_request",
                                "redoText": redo_notes
                            }
                            try:
                                res = requests.post(WEB_APP_URL, json=payload)
                                if res.status_code == 200:
                                    st.success("Revision request submitted successfully! Status updated to 'Recheck Requested'.")
                                else:
                                    st.error("Failed to submit request to server.")
                            except Exception as e:
                                st.error(f"Network error: {e}")
                        else:
                            st.warning("Please enter your revision notes.")
                
                if pd.notna(redo_link) and str(redo_link).startswith("http"):
                    st.markdown(f"🛠️ **[Download Rechecked / Revised Deliverable]({redo_link})**")

                st.markdown("---")
                
                # Feedback Section
                st.markdown("### 💬 Client Feedback & Ideas")
                feedback_text = st.text_area("How did we do? Any ideas for better work or new features?", placeholder="Leave your feedback here...", key=f"feed_{selected_proj_id}")
                if st.button("Submit Feedback"):
                    if feedback_text:
                        payload = {
                            "clientEmail": st.session_state.client_email,
                            "projectID": selected_proj_id,
                            "action": "client_feedback",
                            "feedbackText": feedback_text
                        }
                        try:
                            res = requests.post(WEB_APP_URL, json=payload)
                            if res.status_code == 200:
                                st.success("Thank you! Your feedback has been recorded.")
                            else:
                                st.error("Failed to send feedback.")
                        except Exception as e:
                            st.error(f"Network error: {e}")
                    else:
                        st.warning("Please type your feedback before submitting.")

    except Exception as e:
        st.error(f"Error loading project dashboard data: {e}")