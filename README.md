# AI Finance Collections Agent

An enterprise-grade, AI-powered Finance Credit Follow-Up Email Agent.

## Features
- Reads overdue invoice records from CSV
- Calculates overdue days and determines escalation stage
- Generates personalized collection emails using Groq Llama3 via LangChain
- Supports human approval workflow and logs audit history
- Interactive analytics dashboard using Streamlit and Plotly
- Dry-run mode to simulate sending emails

## Architecture
- **app.py**: Main Streamlit application entry point.
- **utils/**: Modular components handling specific business logic:
  - `stages.py`: Defines logic for escalation stages based on overdue days.
  - `risk_engine.py`: Analyzes customer risk profile.
  - `email_generator.py`: Interfaces with LangChain/Groq to generate emails.
  - `logger.py`: Handles audit logging.
  - `analytics.py`: Generates visualizations for the dashboard.
- **data/**: Stores input data like invoices.
- **logs/**: Stores audit history and application logs.
- **outputs/**: Stores generated outputs (e.g., approved emails).
- **prompts/**: Stores LLM prompt templates.
