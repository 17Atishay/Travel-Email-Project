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
from utils.stages import calculate_escalation_stage
from utils.risk_engine import calculate_risk_score

def add_log(msg: str):
    if 'logs' not in st.session_state:
        st.session_state['logs'] = []
    st.session_state['logs'].append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def process_invoices(df: pd.DataFrame) -> pd.DataFrame:
    """Processes raw invoice dataframe and adds AI calculated fields."""
    if df.empty:
        return df
        
    add_log(f"Loaded {len(df)} invoices into the processing pipeline.")
    today = pd.to_datetime('today').normalize()
    if 'due_date' in df.columns:
        df['due_date'] = pd.to_datetime(df['due_date'])
        df['days_overdue'] = (today - df['due_date']).dt.days
        df['days_overdue'] = df['days_overdue'].apply(lambda x: max(0, x))
    
    if 'days_overdue' in df.columns:
        stage_tone_tuples = df['days_overdue'].apply(calculate_escalation_stage)
        df['stage'] = [st[0] for st in stage_tone_tuples]
        df['tone'] = [st[1] for st in stage_tone_tuples]
        add_log("Escalation stage calculated for all pending invoices.")
        
        stage_to_count = {'1st Follow-Up': 1, '2nd Follow-Up': 2, '3rd Follow-Up': 3, '4th Follow-Up': 4, 'Escalation Flag': 5}
        df['follow_up_count'] = df['stage'].map(stage_to_count).fillna(0).astype(int)
        
        if 'amount' in df.columns:
            risk_data = df.apply(lambda row: calculate_risk_score(row['days_overdue'], row['amount'], row['follow_up_count']), axis=1)
            df['risk_level'] = [r[0] for r in risk_data]
            df['reasoning'] = [r[1] for r in risk_data]
            add_log("Payment risk calculated successfully.")
        
        df = df.drop(columns=['follow_up_count'], errors='ignore')
        
    # Email status placeholder
    if 'email_status' not in df.columns:
        df['email_status'] = "Pending"
        
    return df

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
        
    # ------------------ SIDEBAR ------------------ #
    st.sidebar.title("💰 AI Collections Agent")
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("### Data Source")
    uploaded_file = st.sidebar.file_uploader("Upload Invoices CSV", type=["csv"])
    if uploaded_file is not None:
        try:
            raw_df = pd.read_csv(uploaded_file)
            st.session_state.df = process_invoices(raw_df)
            add_log(f"Loaded {len(raw_df)} invoices from uploaded CSV")
        except Exception as e:
            st.sidebar.error(f"Error loading CSV: {e}")
    elif st.sidebar.button("Load Default Sample Data", use_container_width=True):
        try:
            raw_df = pd.read_csv("data/invoices.csv")
            st.session_state.df = process_invoices(raw_df)
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
                
                with st.expander("🤖 AI Risk & Reasoning", expanded=True):
                    st.write(f"**Risk Level:** `{row['risk_level']}`")
                    st.write(f"**Tone Selected:** `{row['tone']}`")
                    st.write(f"**Reasoning:** {row['reasoning']}")
                
                with st.expander("✉️ Generated Email Preview", expanded=True):
                    # In a real scenario, this would pull the actual LLM generated email 
                    # If it was pre-generated. For now, we show a smart preview placeholder.
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
                        
                    st.text_area("Subject:", value=subject_text, disabled=True)
                    st.text_area("Body:", value=body_text, height=200, disabled=True)
                
                st.markdown("#### Human-in-the-Loop")
                reviewer_comment = st.text_area("Reviewer Comment:", placeholder="Add notes for audit trail...")
                
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("✅ Approve Email", type="primary", use_container_width=True):
                        add_log(f"Approval action: Approved dry-run email for {selected_invoice}")
                        if row['stage'] == 'Escalation Flag':
                            add_log(f"Escalation flagged: {selected_invoice} sent for Legal/Finance Review")
                        
                        # Log to audit file
                        log_audit_event(
                            invoice_id=selected_invoice,
                            client_name=row['customer_name'],
                            stage=row['stage'],
                            tone=row['tone'],
                            risk_level=row['risk_level'],
                            approval_status="Approved",
                            reviewer_comment=reviewer_comment,
                            send_status="Dry Run - Simulated"
                        )
                        st.success(f"Approved {selected_invoice} (Dry Run)")
                        
                with btn_col2:
                    if st.button("❌ Reject / Edit", use_container_width=True):
                        add_log(f"Approval action: Rejected email for {selected_invoice}")
                        
                        # Log to audit file
                        log_audit_event(
                            invoice_id=selected_invoice,
                            client_name=row['customer_name'],
                            stage=row['stage'],
                            tone=row['tone'],
                            risk_level=row['risk_level'],
                            approval_status="Rejected",
                            reviewer_comment=reviewer_comment,
                            send_status="Dry Run - Not Sent"
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
