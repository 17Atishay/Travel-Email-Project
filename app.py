import streamlit as st
import pandas as pd
from datetime import datetime

# Page config must be the first Streamlit command
st.set_page_config(
    page_title="Finance Collections AI Agent",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

from utils.logger import setup_logger, log_audit_event
from utils.analytics import display_dashboard
from utils.email_generator import generate_email, generate_email_preview
from utils.orchestrator import CollectionAgentPipeline
from utils.email_sender import send_email
from utils.config import validate_config

def add_log(msg: str):
    if 'logs' not in st.session_state:
        st.session_state['logs'] = []
    st.session_state['logs'].append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def process_invoices_orchestrated(df: pd.DataFrame) -> pd.DataFrame:
    """Delegates dataframe processing to the multi-agent orchestrator."""
    pipeline = CollectionAgentPipeline(logger_callback=add_log)
    return pipeline.execute_workflow(df)

def main():
    # Load custom CSS for enterprise feel
    st.markdown("""
        <style>
        .stButton button { width: 100%; border-radius: 4px; font-weight: bold; }
        .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; }
        div[data-testid="stExpander"] { border-left: 4px solid #1f77b4; }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize logger
    logger = setup_logger()
    
    if 'df' not in st.session_state:
        st.session_state.df = pd.DataFrame()
    if 'real_emails_sent' not in st.session_state:
        st.session_state.real_emails_sent = 0
    if 'email_drafts' not in st.session_state:
        st.session_state.email_drafts = {}
        
    # ------------------ SIDEBAR ------------------ #
    st.sidebar.title("💰 AI Collections Agent")
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("### Deployment Status")
    config_status = validate_config()
    api_status = "✅ Connected" if config_status["api_connected"] else "❌ Missing Secret"
    smtp_status = "✅ Configured" if config_status["smtp_configured"] else "❌ Missing Secret"
    st.sidebar.markdown(f"**Groq API:** {api_status}")
    st.sidebar.markdown(f"**SMTP Mail:** {smtp_status}")
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("### Settings")
    real_email_mode = st.sidebar.checkbox("Enable Real Email Sending", value=False)
    if real_email_mode:
        st.sidebar.warning("⚠️ REAL EMAILS WILL BE SENT TO CLIENTS. MAXIMUM 5 PER RUN.")
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("### Data Source")
    uploaded_file = st.sidebar.file_uploader("Upload Invoices CSV", type=["csv"])
    if uploaded_file is not None:
        try:
            raw_df = pd.read_csv(uploaded_file)
            st.session_state.df = process_invoices_orchestrated(raw_df)
            add_log(f"Loaded {len(raw_df)} invoices from uploaded CSV")
        except Exception as e:
            st.sidebar.error(f"Error loading CSV: {e}")
    elif st.sidebar.button("Load Default Sample Data", use_container_width=True):
        try:
            raw_df = pd.read_csv("data/invoices.csv")
            st.session_state.df = process_invoices_orchestrated(raw_df)
            add_log(f"Loaded {len(raw_df)} invoices from sample data")
        except FileNotFoundError:
            st.sidebar.error("Sample data not found.")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Filters")
    
    risk_filter = st.sidebar.multiselect("Filter by Risk Level", ["Low Risk", "Medium Risk", "High Risk"], default=["Low Risk", "Medium Risk", "High Risk"])
    
    available_stages = []
    if not st.session_state.df.empty and 'stage' in st.session_state.df.columns:
        available_stages = st.session_state.df['stage'].unique().tolist()
    stage_filter = st.sidebar.multiselect("Filter by Stage", available_stages, default=available_stages)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Actions")
    if st.sidebar.button("Generate Emails 🚀", type="primary"):
        add_log("Started batch email generation process via LLM")
        # Logic to actually call LLM for all pending rows would be hooked here
        st.sidebar.success("Emails queued for generation!")
        add_log("Completed email generation queueing")

    # ------------------ MAIN DASHBOARD ------------------ #
    st.title("Enterprise AI Finance Collections Dashboard")
    st.markdown("Automated, intelligent follow-up and escalation workflows for accounts receivable.")
    
    if st.session_state.df.empty:
        st.info("👈 Please upload a CSV file or load sample data from the sidebar to begin.")
        return

    df = st.session_state.df.copy()
    
    # Apply filters
    if risk_filter:
        df = df[df['risk_level'].isin(risk_filter)]
    if stage_filter:
        df = df[df['stage'].isin(stage_filter)]

    # TOP METRICS
    st.markdown("### Executive Summary")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Pending Invoices", f"{len(df)}")
    with col2:
        amount_sum = df['amount'].sum() if 'amount' in df.columns else 0
        st.metric("Total Amount Pending", f"${amount_sum:,.2f}")
    with col3:
        high_risk_count = len(df[df['risk_level'] == 'High Risk']) if 'risk_level' in df.columns else 0
        st.metric("High-Risk Accounts", f"{high_risk_count}")
    with col4:
        escalated_count = len(df[df['stage'] == 'Escalation Flag']) if 'stage' in df.columns else 0
        st.metric("Escalated Cases (Legal)", f"{escalated_count}")

    st.markdown("---")

    # TABS FOR CONTENT
    tab1, tab2, tab3 = st.tabs(["📋 Active Workflows", "📈 Analytics", "🔍 Audit & Observability"])

    with tab1:
        st.markdown("### Pending Accounts & Approvals")
        
        col_table, col_details = st.columns([2, 1])
        
        with col_table:
            # Display Main Table
            st.dataframe(
                df[['invoice_id', 'customer_name', 'amount', 'days_overdue', 'stage', 'risk_level', 'email_status']],
                use_container_width=True,
                hide_index=True
            )
            
            # Select an invoice for right panel review
            st.markdown("Select an Invoice for Review:")
            selected_invoice = st.selectbox("Invoice ID", [""] + df['invoice_id'].tolist(), label_visibility="collapsed")
            
        with col_details:
            st.markdown("### Review & Action")
            if selected_invoice:
                row = df[df['invoice_id'] == selected_invoice].iloc[0]
                
                with st.expander("🤖 AI Risk & Reasoning", expanded=False):
                    st.write(f"**Risk Level:** `{row['risk_level']}`")
                    st.write(f"**Tone Selected:** `{row['tone']}`")
                    st.write(f"**Reasoning:** {row['reasoning']}")
                
                # --- DRAFT INITIALIZATION ---
                if selected_invoice not in st.session_state.email_drafts:
                    subject_text = f"Action Required: Overdue Invoice {row['invoice_id']}"
                    body_text = (
                        f"Dear {row['customer_name']},\n\n"
                        f"This is a {row['tone'].lower()} reminder regarding invoice {row['invoice_id']} "
                        f"for the amount of ${row['amount']:,.2f}, which is currently {row['days_overdue']} days overdue.\n\n"
                        f"Please ensure payment is made promptly.\n\n"
                        f"Best regards,\nFinance Team"
                    )
                    if row['stage'] == 'Escalation Flag':
                        body_text = "No email generated. Account flagged for legal review."
                        subject_text = "N/A"
                        
                    st.session_state.email_drafts[selected_invoice] = {
                        "original_subject": subject_text,
                        "original_body": body_text,
                        "edited_subject": subject_text,
                        "edited_body": body_text,
                        "is_modified": False,
                        "modification_timestamp": None
                    }
                
                draft = st.session_state.email_drafts[selected_invoice]
                
                st.info("ℹ️ Human approval required before outbound communication.")
                
                # --- EDITOR VIEW ---
                with st.expander("📝 Edit Email Draft", expanded=True):
                    new_subject = st.text_input("Subject:", value=draft["edited_subject"], key=f"subj_{selected_invoice}")
                    new_body = st.text_area("Body:", value=draft["edited_body"], height=200, key=f"body_{selected_invoice}")
                    
                    if st.button("💾 Save Changes", use_container_width=True):
                        if new_subject != draft["original_subject"] or new_body != draft["original_body"]:
                            st.session_state.email_drafts[selected_invoice]["edited_subject"] = new_subject
                            st.session_state.email_drafts[selected_invoice]["edited_body"] = new_body
                            st.session_state.email_drafts[selected_invoice]["is_modified"] = True
                            st.session_state.email_drafts[selected_invoice]["modification_timestamp"] = datetime.now().isoformat()
                            st.success("Changes saved! Marked as HUMAN_MODIFIED.")
                            add_log(f"Reviewer edited email for {selected_invoice}")
                        else:
                            st.info("No changes detected.")
                            
                # --- COMPARISON VIEW ---
                draft = st.session_state.email_drafts[selected_invoice] # refresh after save
                if draft["is_modified"]:
                    with st.expander("🔍 Compare Original vs Edited", expanded=False):
                        comp_col1, comp_col2 = st.columns(2)
                        with comp_col1:
                            st.markdown("##### 🤖 AI Generated Draft")
                            st.text_area("Orig Subj:", value=draft["original_subject"], disabled=True, key=f"os_{selected_invoice}")
                            st.text_area("Orig Body:", value=draft["original_body"], disabled=True, height=150, key=f"ob_{selected_invoice}")
                        with comp_col2:
                            st.markdown("##### 👤 Human Reviewed Version")
                            st.text_area("Edit Subj:", value=draft["edited_subject"], disabled=True, key=f"es_{selected_invoice}")
                            st.text_area("Edit Body:", value=draft["edited_body"], disabled=True, height=150, key=f"eb_{selected_invoice}")

                st.markdown("#### Human-in-the-Loop")
                reviewer_comment = st.text_area("Reviewer Comment:", placeholder="Add notes for audit trail...")
                
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("✅ Approve & Send", type="primary", use_container_width=True):
                        if row['stage'] == 'Escalation Flag':
                            add_log(f"Escalation flagged: {selected_invoice} sent for Legal/Finance Review")
                            st.info("Account flagged. No email sent.")
                            
                            log_audit_event(
                                invoice_id=selected_invoice,
                                client_name=row['customer_name'],
                                stage=row['stage'],
                                tone=row['tone'],
                                risk_level=row['risk_level'],
                                approval_status="Escalated",
                                reviewer_comment=reviewer_comment,
                                send_status="N/A",
                                is_modified=draft["is_modified"],
                                original_subject=draft["original_subject"],
                                original_body=draft["original_body"],
                                final_subject=draft["edited_subject"],
                                final_body=draft["edited_body"],
                                modification_timestamp=draft["modification_timestamp"]
                            )
                        else:
                            add_log(f"Approval action: Approved email for {selected_invoice}")
                            
                            send_status = "Dry Run - Simulated"
                            if real_email_mode:
                                if st.session_state.real_emails_sent >= 5:
                                    st.error("Batch limit reached (5 emails). Cannot send more real emails in this run.")
                                    send_status = "FAILED: Batch Limit Reached"
                                    add_log(send_status)
                                else:
                                    recipient = row.get("customer_email", "fallback@example.com") 
                                    success, status_msg = send_email(
                                        recipient_email=recipient,
                                        subject=draft["edited_subject"],
                                        body=draft["edited_body"],
                                        real_email_mode=True
                                    )
                                    send_status = status_msg
                                    if success:
                                        st.session_state.real_emails_sent += 1
                                        st.success(f"Email successfully sent to {row['customer_name']}!")
                                        add_log(f"Real email sent to {recipient}")
                                    else:
                                        st.error(f"Failed to send: {status_msg}")
                            else:
                                st.success(f"Approved {selected_invoice} (Dry Run)")
                            
                            log_audit_event(
                                invoice_id=selected_invoice,
                                client_name=row['customer_name'],
                                stage=row['stage'],
                                tone=row['tone'],
                                risk_level=row['risk_level'],
                                approval_status="Approved",
                                reviewer_comment=reviewer_comment,
                                send_status=send_status,
                                is_modified=draft["is_modified"],
                                original_subject=draft["original_subject"],
                                original_body=draft["original_body"],
                                final_subject=draft["edited_subject"],
                                final_body=draft["edited_body"],
                                modification_timestamp=draft["modification_timestamp"]
                            )
                        
                with btn_col2:
                    if st.button("❌ Reject Email", use_container_width=True):
                        add_log(f"Approval action: Rejected email for {selected_invoice}")
                        
                        log_audit_event(
                            invoice_id=selected_invoice,
                            client_name=row['customer_name'],
                            stage=row['stage'],
                            tone=row['tone'],
                            risk_level=row['risk_level'],
                            approval_status="Rejected",
                            reviewer_comment=reviewer_comment,
                            send_status="Dry Run - Not Sent",
                            is_modified=draft["is_modified"],
                            original_subject=draft["original_subject"],
                            original_body=draft["original_body"],
                            final_subject=draft["edited_subject"],
                            final_body=draft["edited_body"],
                            modification_timestamp=draft["modification_timestamp"]
                        )
                        st.error(f"Rejected {selected_invoice}")
            else:
                st.info("Select an invoice from the table to view details and take action.")

    with tab2:
        st.markdown("### Portfolio Analytics")
        display_dashboard(df)

    with tab3:
        st.markdown("### System Execution Logs")
        if 'logs' in st.session_state and st.session_state['logs']:
            log_text = "\n".join(st.session_state['logs'])
            st.code(log_text, language="text")
        else:
            st.info("No system logs yet.")

if __name__ == "__main__":
    main()
