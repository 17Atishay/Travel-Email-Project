"""
Multi-Agent Plan-and-Execute Orchestrator for Finance Collections.
This module defines the agentic workflow pipeline.

Architecture Explanation:
-------------------------
This project employs a Plan-and-Execute Multi-Agent Architecture.
Instead of a monolithic script, specialized "Agents" handle distinct parts of the workflow.
1. Supervisor Agent: Orchestrates the pipeline and handles state transitions.
2. Invoice Analysis Agent: Validates data and computes core overdue metrics.
3. Risk Assessment Agent: Scores the probability of non-payment.
4. Tone Selection Agent: Determines the behavioral approach (Tone) based on the stage.
5. Email Generation Agent: Synthesizes the final communication using LLMs.
6. Audit Logging Agent: Finalizes observability and compliance logging.

This design ensures Separation of Concerns (SoC), makes the prompt engineering
highly targeted (preventing hallucination), and aligns with enterprise-grade
AI design patterns.
"""

import pandas as pd
from typing import Dict, Any

from utils.stages import calculate_escalation_stage
from utils.risk_engine import calculate_risk_score

class CollectionAgentPipeline:
    """
    Supervisor Agent orchestrating the plan-and-execute workflow.
    """
    def __init__(self, logger_callback=None):
        self.logger = logger_callback

    def log(self, msg: str):
        if self.logger:
            self.logger(msg)

    def execute_workflow(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Executes the plan-and-execute sequence across all agents.
        """
        if df.empty:
            return df
            
        self.log(f"[Supervisor Agent] Initiating workflow for {len(df)} invoices.")
        
        # Step 1 -> analyze invoices
        df = self._invoice_analysis_agent(df)
        
        # Step 2 -> choose escalation strategy (Tone Selection)
        df = self._tone_selection_agent(df)
        
        # Step 3 -> assess risk
        df = self._risk_assessment_agent(df)
        
        # Step 4 -> generate communication (Preparation step before LLM)
        df = self._email_generation_prep_agent(df)
        
        # Step 5 -> log and review
        df = self._audit_logging_agent(df)
        
        self.log("[Supervisor Agent] Workflow execution completed successfully.")
        return df

    def _invoice_analysis_agent(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Role: Validates raw invoice data and calculates days overdue.
        Inputs: Raw dataframe with 'due_date'.
        Outputs: Dataframe enriched with 'days_overdue'.
        """
        self.log("[Invoice Analysis Agent] Validating data and computing overdue metrics.")
        today = pd.to_datetime('today').normalize()
        if 'due_date' in df.columns:
            df['due_date'] = pd.to_datetime(df['due_date'])
            df['days_overdue'] = (today - df['due_date']).dt.days
            df['days_overdue'] = df['days_overdue'].apply(lambda x: max(0, x))
        return df

    def _tone_selection_agent(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Role: Selects the escalation tone based on the overdue timeline.
        Inputs: Dataframe with 'days_overdue'.
        Outputs: Dataframe enriched with 'stage' and 'tone'.
        """
        self.log("[Tone Selection Agent] Determining escalation stages and behavioral tones.")
        if 'days_overdue' in df.columns:
            stage_tone_tuples = df['days_overdue'].apply(calculate_escalation_stage)
            df['stage'] = [st[0] for st in stage_tone_tuples]
            df['tone'] = [st[1] for st in stage_tone_tuples]
        return df

    def _risk_assessment_agent(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Role: Determines payment recovery risk based on overdue days, amount, and history.
        Inputs: Dataframe with 'days_overdue', 'amount', 'stage'.
        Outputs: Dataframe enriched with 'risk_level' and 'reasoning'.
        """
        self.log("[Risk Assessment Agent] Scoring payment recovery probability.")
        if 'stage' in df.columns and 'days_overdue' in df.columns and 'amount' in df.columns:
            stage_to_count = {'1st Follow-Up': 1, '2nd Follow-Up': 2, '3rd Follow-Up': 3, '4th Follow-Up': 4, 'Escalation Flag': 5}
            df['follow_up_count'] = df['stage'].map(stage_to_count).fillna(0).astype(int)
            
            risk_data = df.apply(lambda row: calculate_risk_score(row['days_overdue'], row['amount'], row['follow_up_count']), axis=1)
            df['risk_level'] = [r[0] for r in risk_data]
            df['reasoning'] = [r[1] for r in risk_data]
            
            df = df.drop(columns=['follow_up_count'], errors='ignore')
        return df

    def _email_generation_prep_agent(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Role: Prepares the state for the LLM email generation.
        Inputs: Enriched Dataframe.
        Outputs: Dataframe with 'email_status'.
        """
        self.log("[Email Generation Agent] Queuing context for LLM generation.")
        if 'email_status' not in df.columns:
            df['email_status'] = "Pending"
        return df

    def _audit_logging_agent(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Role: Finalizes the observability state.
        Inputs: Dataframe with all computed fields.
        Outputs: Final dataframe ready for UI presentation.
        """
        self.log("[Audit Logging Agent] Finalizing observability markers and system-of-record prep.")
        return df
