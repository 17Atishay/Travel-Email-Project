"""
Email Sender Module for AI Finance Collections Agent.
Handles secure, authenticated SMTP dispatch with fallback mechanisms.
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize module logger
logger = logging.getLogger("collections_agent")

def send_email(recipient_email: str, subject: str, body: str, real_email_mode: bool = False) -> tuple[bool, str]:
    """
    Dispatches a professional collection email using secure SMTP.
    
    Args:
        recipient_email (str): The target client's email address.
        subject (str): The subject line of the email.
        body (str): The body content of the email.
        real_email_mode (bool): Safety switch. If False, executes a dry-run.
        
    Returns:
        tuple[bool, str]: A tuple containing (Success Status, Status Message / Error Message).
    """
    
    if not real_email_mode:
        logger.info(f"[DRY RUN] Simulated sending email to {recipient_email}")
        return True, "Dry Run - Simulated"
        
    logger.info("[INFO] Connecting to SMTP server...")
    
    # Retrieve SMTP credentials
    sender_email = os.environ.get("EMAIL_ADDRESS")
    sender_password = os.environ.get("EMAIL_PASSWORD")
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    
    try:
        smtp_port = int(os.environ.get("SMTP_PORT", 587))
    except ValueError:
        smtp_port = 587

    # Validate configuration
    if not sender_email or not sender_password:
        error_msg = "SMTP credentials missing in environment variables (.env)."
        logger.error(f"[ERROR] {error_msg}")
        return False, error_msg

    # Construct the MIME message payload
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_email

    try:
        # Establish secure connection with a 15-second timeout
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=15)
        server.ehlo()
        server.starttls() # Secure the connection using TLS
        server.ehlo()
        
        # Authenticate
        server.login(sender_email, sender_password)
        
        # Dispatch email
        server.sendmail(sender_email, [recipient_email], msg.as_string())
        server.quit()
        
        logger.info(f"[INFO] Email sent successfully to {recipient_email}")
        return True, "Sent Successfully"
        
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"SMTP authentication failed. Check credentials. Detail: {str(e)}"
        logger.error(f"[ERROR] {error_msg}")
        return False, f"FAILED: {error_msg}"
        
    except smtplib.SMTPConnectError as e:
        error_msg = f"Failed to connect to SMTP server. Detail: {str(e)}"
        logger.error(f"[ERROR] {error_msg}")
        return False, f"FAILED: {error_msg}"
        
    except TimeoutError as e:
        error_msg = "SMTP connection timed out."
        logger.error(f"[ERROR] {error_msg}")
        return False, f"FAILED: {error_msg}"
        
    except Exception as e:
        error_msg = f"Unexpected error during SMTP dispatch: {str(e)}"
        logger.error(f"[ERROR] {error_msg}")
        return False, f"FAILED: {error_msg}"
