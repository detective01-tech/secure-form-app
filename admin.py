"""
Admin panel blueprint for managing form submissions
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file, current_app
from functools import wraps
from models import db, FormSubmission
from werkzeug.security import check_password_hash, generate_password_hash
import io
import logging

logger = logging.getLogger(__name__)

# Create admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def login_required(f):
    """Decorator to require login for admin routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login_admin'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/logout')
def logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('Successfully logged out.', 'success')
    return redirect(url_for('login_admin'))


@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Admin dashboard showing all submissions"""
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Get search parameter
    search = request.args.get('search', '')
    
    # Build query
    query = FormSubmission.query
    
    if search:
        query = query.filter(
            db.or_(
                FormSubmission.name_on_card.ilike(f'%{search}%'),
                FormSubmission.card_type.ilike(f'%{search}%'),
                FormSubmission.ip_address.ilike(f'%{search}%')
            )
        )
    
    # Order by most recent first
    query = query.order_by(FormSubmission.submission_date.desc())
    
    # Paginate results
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    submissions = pagination.items
    
    # Get statistics
    total_submissions = FormSubmission.query.count()
    emails_sent = FormSubmission.query.filter_by(email_sent=True).count()
    
    return render_template(
        'admin/dashboard.html',
        submissions=submissions,
        pagination=pagination,
        total_submissions=total_submissions,
        emails_sent=emails_sent,
        search=search
    )


@admin_bp.route('/download/<int:submission_id>')
@login_required
def download_document(submission_id):
    """Download document for a specific submission"""
    submission = FormSubmission.query.get_or_404(submission_id)
    
    # Try to get document from database first
    if submission.document_data:
        try:
            filename = submission.docx_filename or f'submission_{submission_id}.docx'
            return send_file(
                io.BytesIO(submission.document_data),
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                as_attachment=True,
                download_name=filename
            )
        except Exception as e:
            logger.error(f"Error sending document from database: {str(e)}")
            flash('Error downloading document from database.', 'error')
    
    # Fallback to file system
    if submission.docx_filename:
        try:
            file_path = current_app.config['SUBMISSIONS_FOLDER'] / submission.docx_filename
            if file_path.exists():
                return send_file(
                    file_path,
                    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    as_attachment=True,
                    download_name=submission.docx_filename
                )
        except Exception as e:
            logger.error(f"Error sending document from file: {str(e)}")
    
    flash('Document not found.', 'error')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/view/<int:submission_id>')
@login_required
def view_submission(submission_id):
    """View detailed information about a submission"""
    submission = FormSubmission.query.get_or_404(submission_id)
    return render_template('admin/view_submission.html', submission=submission)
