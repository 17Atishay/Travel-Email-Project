"""
Integration with LangChain and Groq API to generate personalized collection emails.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException
from tenacity import retry, stop_after_attempt, wait_exponential

from utils.prompt import EMAIL_GENERATION_AGENT_PROMPT

# 1. STRUCTURED OUTPUT:
# We use Pydantic models with LangChain's PydanticOutputParser.
# This forces the LLM to return a strictly formatted JSON object matching our schema,
# eliminating the need for complex regex parsing and ensuring all required fields are present.
class EmailResponse(BaseModel):
    subject: str = Field(description="The subject line of the email")
    body: str = Field(description="The body of the email. Do not use any markdown formatting.")
    tone_used: str = Field(description="The tone applied to the email")
    summary: str = Field(description="Short reasoning for the email content")

# 2. RETRY / ERROR HANDLING:
# We use 'tenacity' to automatically retry the LLM call if it fails due to rate limits
# or transient network errors, using exponential backoff.
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_email(
    client_name: str, 
    invoice_number: str, 
    amount_due: float, 
    due_date: str, 
    days_overdue: int, 
    tone: str, 
    payment_link: str
) -> dict:
    """
    Calls the Groq LLM to generate a context-aware follow-up email.
    """
    # 3. HALLUCINATION MITIGATION:
    # We use a low temperature (0.1) to make the model's responses more deterministic
    # and strictly factual.
    llm = ChatGroq(model_name="llama3-70b-8192", temperature=0.1)
    
    parser = PydanticOutputParser(pydantic_object=EmailResponse)
    
    # 4. PROMPT INJECTION MITIGATION & GUARDRAILS:
    # We provide strict system instructions explicitly forbidding the use of outside data
    # and instructing the model to ignore any hidden commands within the input variables.
    prompt = ChatPromptTemplate.from_messages([
        ("system", EMAIL_GENERATION_AGENT_PROMPT),
        ("human", "Client Name: {client_name}\n"
                  "Invoice Number: {invoice_number}\n"
                  "Amount Due: ${amount_due}\n"
                  "Due Date: {due_date}\n"
                  "Days Overdue: {days_overdue}\n"
                  "Payment Link: {payment_link}\n\n"
                  "Please generate the collection email.")
    ])
    
    chain = prompt | llm | parser
    
    try:
        response = chain.invoke({
            "client_name": client_name,
            "invoice_number": invoice_number,
            "amount_due": f"{amount_due:,.2f}",
            "due_date": str(due_date),
            "days_overdue": days_overdue,
            "tone": tone,
            "payment_link": payment_link,
            "format_instructions": parser.get_format_instructions()
        })
        
        output_dict = response.dict()
        
        # Save to JSON file
        save_email_to_file(output_dict)
        
        return output_dict
        
    except OutputParserException as e:
        print(f"Failed to parse structured LLM output: {e}")
        raise
    except Exception as e:
        print(f"Error during LLM generation: {e}")
        raise

def save_email_to_file(email_data: dict):
    """
    Saves generated emails into outputs/generated_emails.json
    """
    os.makedirs("outputs", exist_ok=True)
    file_path = os.path.join("outputs", "generated_emails.json")
    
    emails = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    emails = json.loads(content)
        except json.JSONDecodeError:
            pass
            
    email_data['timestamp'] = datetime.now().isoformat()
    emails.append(email_data)
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(emails, f, indent=4)

def generate_email_preview(customer_name: str, amount: float, stage: str, context: dict = None) -> str:
    """
    Legacy placeholder for dashboard preview functionality.
    """
    return f"Preview for {customer_name} - Stage: {stage} - Amount: ${amount:,.2f}"
