"""
Database models for the Secure Form application
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from utils.encryption import encryption_helper

db = SQLAlchemy()

class FormSubmission(db.Model):
    """Model for storing form submissions"""
    
    __tablename__ = 'form_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Personal information
    name_on_card = db.Column(db.String(100), nullable=False)
    
    # Card information (encrypted)
    # Using Text instead of String to accommodate base64 encoded encrypted strings which can be long
    card_type = db.Column(db.String(50), nullable=False)
    card_number_encrypted = db.Column(db.Text, nullable=False)
    expiration_date_encrypted = db.Column(db.Text, nullable=False)
    cvv_encrypted = db.Column(db.Text, nullable=False)
    
    # SSN (encrypted)
    ssn_encrypted = db.Column(db.Text, nullable=False)
    
    # Metadata
    submission_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    docx_filename = db.Column(db.String(255), nullable=True)
    document_data = db.Column(db.LargeBinary, nullable=True)  # Store DOCX in database
    ip_address = db.Column(db.String(45), nullable=True)  # Support IPv6
    
    # Email tracking
    email_sent = db.Column(db.Boolean, default=False, nullable=False)
    email_sent_at = db.Column(db.DateTime, nullable=True)
    
    def __init__(self, name_on_card, card_type, card_number, expiration_date, cvv, ssn, ip_address=None):
        """
        Initialize a new form submission with encrypted sensitive data
        
        Args:
            name_on_card: Name as it appears on card
            card_type: Type of card (Credit/Debit)
            card_number: Card number (will be encrypted)
            expiration_date: Expiration date (will be encrypted)
            cvv: CVV code (will be encrypted)
            ssn: Social Security Number (will be encrypted)
            ip_address: Optional IP address of submitter
        """
        self.name_on_card = name_on_card
        self.card_type = card_type
        # Encrypt sensitive data before storing
        self.card_number_encrypted = encryption_helper.encrypt(card_number)
        self.expiration_date_encrypted = encryption_helper.encrypt(expiration_date)
        self.cvv_encrypted = encryption_helper.encrypt(cvv)
        self.ssn_encrypted = encryption_helper.encrypt(ssn)
        self.ip_address = ip_address
    
    @property
    def card_number(self):
        """Decrypt and return card number"""
        return encryption_helper.decrypt(self.card_number_encrypted)
    
    @property
    def expiration_date(self):
        """Decrypt and return expiration date"""
        return encryption_helper.decrypt(self.expiration_date_encrypted)
    
    @property
    def cvv(self):
        """Decrypt and return CVV"""
        return encryption_helper.decrypt(self.cvv_encrypted)
    
    @property
    def ssn(self):
        """Decrypt and return SSN"""
        return encryption_helper.decrypt(self.ssn_encrypted)
    
    def to_dict(self, include_document=False):
        """
        Convert submission to dictionary (with decrypted values)
        
        Args:
            include_document: Whether to include binary document data
        
        Returns:
            Dictionary containing all form data
        """
        data = {
            'id': self.id,
            'name_on_card': self.name_on_card,
            'card_type': self.card_type,
            'card_number': self.card_number,
            'expiration_date': self.expiration_date,
            'cvv': self.cvv,
            'ssn': self.ssn,
            'submission_date': self.submission_date.isoformat(),
            'docx_filename': self.docx_filename,
            'ip_address': self.ip_address,
            'email_sent': self.email_sent,
            'email_sent_at': self.email_sent_at.isoformat() if self.email_sent_at else None
        }
        
        if include_document and self.document_data:
            data['document_data'] = self.document_data
        
        return data
    
    def __repr__(self):
        return f'<FormSubmission {self.id} - {self.name_on_card}>'
