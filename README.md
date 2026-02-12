# Secure Form Application

A professional, secure web application for collecting sensitive user information with encrypted storage, email notifications, and admin dashboard.

## ✨ Features

- **Secure Data Collection**: Collect card information and SSN with real-time validation
- **End-to-End Encryption**: All sensitive data encrypted using Fernet (AES-256)
- **Email Notifications**: Automatic email delivery with document attachments
- **Admin Dashboard**: Password-protected panel to view and download submissions
- **Document Generation**: Professional DOCX documents for each submission
- **Modern UI**: Responsive design with gradient aesthetics and smooth animations
- **CSRF Protection**: Built-in protection against cross-site request forgery
- **Database Storage**: Dual storage (file + database) for redundancy
- **Search & Filter**: Easy submission management in admin panel

## 🚀 Quick Start (Local Development)

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd secure-form
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   copy .env.example .env
   ```

5. **Edit `.env` file:**
   - Generate encryption key:
     ```bash
     python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
     ```
   - Add your Gmail credentials (see Email Setup below)
   - Set admin credentials

6. **Run the application:**
   ```bash
   python app.py
   ```

7. **Access the application:**
   - Main form: http://localhost:5000
   - Admin panel: http://localhost:5000/admin

## 📧 Email Setup (Gmail)

To enable email notifications:

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Factor Authentication
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Create app password for "Mail"
5. Add to `.env`:
   ```
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-16-char-app-password
   MAIL_RECIPIENT=where-to-receive@gmail.com
   ```

## 🔐 Admin Panel

Access the admin dashboard at `/admin`:

- **Login**: Use credentials from `.env` (`ADMIN_USERNAME` / `ADMIN_PASSWORD`)
- **Dashboard**: View all submissions with statistics
- **Search**: Filter by name, card type, or IP address
- **Download**: Get DOCX documents for any submission
- **Email Status**: See which submissions had emails sent

## 🌐 Deployment

Ready to deploy to production? See **[DEPLOYMENT.md](DEPLOYMENT.md)** for detailed instructions.

**Recommended Platform: Render** (easiest, free tier available)

Quick deployment steps:
1. Push code to GitHub
2. Connect to Render
3. Add environment variables
4. Deploy! 🎉

Full guide: [DEPLOYMENT.md](DEPLOYMENT.md)

## 📁 Project Structure

```
secure-form/
├── app.py                 # Main Flask application
├── admin.py              # Admin panel blueprint
├── config.py             # Configuration settings
├── models.py             # Database models
├── requirements.txt      # Python dependencies
├── Procfile             # Production server config
├── render.yaml          # Render deployment config
├── DEPLOYMENT.md        # Deployment guide
├── static/
│   ├── css/
│   │   ├── style.css    # Main app styles
│   │   └── admin.css    # Admin panel styles
│   └── js/
│       └── main.js      # Client-side JavaScript
├── templates/
│   ├── index.html       # Main form page
│   └── admin/
│       ├── login.html   # Admin login
│       └── dashboard.html # Admin dashboard
└── utils/
    ├── validators.py    # Input validation
    ├── encryption.py    # Encryption utilities
    ├── docx_generator.py # Document generation
    └── email_service.py  # Email notifications
```

## 🔒 Security Features

- **Encryption**: AES-256 encryption for sensitive data
- **CSRF Protection**: Flask-WTF CSRF tokens
- **Secure Sessions**: HTTPOnly, Secure, SameSite cookies
- **Input Validation**: Server-side validation for all inputs
- **SQL Injection Protection**: SQLAlchemy ORM
- **XSS Protection**: Input sanitization
- **HTTPS**: Enforced in production
- **Password Protection**: Admin panel authentication

## 🛠️ Technology Stack

- **Backend**: Flask 3.0
- **Database**: SQLite (dev) / PostgreSQL (production)
- **ORM**: SQLAlchemy
- **Email**: Flask-Mail
- **Encryption**: Cryptography (Fernet)
- **Documents**: python-docx
- **Production Server**: Gunicorn
- **Frontend**: HTML5, CSS3, Vanilla JavaScript

## 📊 Database Schema

### FormSubmission
- `id`: Primary key
- `name_on_card`: Cardholder name
- `card_type`: Credit/Debit
- `card_number_encrypted`: Encrypted card number
- `expiration_date_encrypted`: Encrypted expiration
- `cvv_encrypted`: Encrypted CVV
- `ssn_encrypted`: Encrypted SSN
- `document_data`: Binary DOCX storage
- `docx_filename`: Document filename
- `email_sent`: Email delivery status
- `email_sent_at`: Email timestamp
- `submission_date`: Submission timestamp
- `ip_address`: Submitter IP

## 🧪 Testing

### Test Form Submission
1. Run app locally
2. Fill form with test data
3. Check email for document
4. Login to admin panel
5. Verify submission appears
6. Download document

### Test Admin Panel
1. Navigate to `/admin`
2. Login with credentials
3. Test search functionality
4. Test pagination
5. Test document download

## 🐛 Troubleshooting

### Email not sending?
- Verify Gmail app password (16 characters)
- Check `MAIL_USERNAME` is correct
- Ensure 2FA is enabled on Gmail
- Check application logs

### Database errors?
- Delete `submissions/database.db` and restart
- Check `ENCRYPTION_KEY` hasn't changed
- Verify write permissions

### Admin login fails?
- Check `.env` has correct `ADMIN_PASSWORD`
- Clear browser cookies
- Verify environment variables loaded

## 📝 License

This project is private and confidential. All rights reserved.

## 🤝 Support

For deployment help, see [DEPLOYMENT.md](DEPLOYMENT.md)

---

**Built with ❤️ for secure data collection**
