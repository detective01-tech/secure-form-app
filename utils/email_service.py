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


def send_submission_email(submission_data, document_path=None):
    """
    Send email notification with submission details and document attachment
    
    Args:
        submission_data: Dictionary containing form submission data
        document_path: Path to the generated DOCX document (optional)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        recipient = current_app.config.get('MAIL_RECIPIENT')
        
        if not recipient:
            logger.warning("No email recipient configured. Skipping email.")
            return False, "No recipient configured"
        
        # Create email message
        msg = Message(
            subject=f"New Form Submission - {submission_data.get('name_on_card')}",
            sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
            recipients=[recipient]
        )
        
        # Create HTML email body
        msg.html = create_email_html(submission_data)
        
        # Attach document if provided
        if document_path and Path(document_path).exists():
            with open(document_path, 'rb') as doc:
                msg.attach(
                    filename=Path(document_path).name,
                    content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    data=doc.read()
                )
        
        # Send email
        mail.send(msg)
        logger.info(f"Email sent successfully to {recipient}")
        return True, "Email sent successfully"
        
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
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
