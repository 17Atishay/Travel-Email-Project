"""
Data aggregation and visualization components using Plotly.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

def display_dashboard(df: pd.DataFrame):
    """
    Renders analytics charts and metrics using Streamlit and Plotly.
    
    Args:
        df (pd.DataFrame): The dataset containing invoice records.
    """
    if df.empty:
        st.warning("No data available for analytics.")
        return

    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Overdue stage distribution
        if 'stage' in df.columns:
            fig1 = px.pie(df, names='stage', title="Overdue Stage Distribution", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig1.update_layout(margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig1, use_container_width=True)
            
    with col2:
        # Pending amount by risk level
        if 'risk_level' in df.columns and 'amount' in df.columns:
            risk_amount = df.groupby('risk_level')['amount'].sum().reset_index()
            fig2 = px.bar(risk_amount, x='risk_level', y='amount', title="Pending Amount by Risk Level",
                          color='risk_level',
                          color_discrete_map={"Low Risk": "#2ca02c", "Medium Risk": "#ff7f0e", "High Risk": "#d62728"})
            fig2.update_layout(margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig2, use_container_width=True)
            
    with col3:
        # Escalation counts
        if 'stage' in df.columns:
            escalation_counts = df['stage'].value_counts().reset_index()
            escalation_counts.columns = ['stage', 'count']
            fig3 = px.bar(escalation_counts, x='stage', y='count', title="Escalation Counts",
                          color='stage', color_discrete_sequence=px.colors.sequential.Teal)
            fig3.update_layout(margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig3, use_container_width=True)
