# Deployment Guide - Secure Form Application

This guide will walk you through deploying your secure form application to Render (recommended) or other cloud platforms.

## 🚀 Quick Start - Deploy to Render

Render is the easiest and recommended deployment option. It's free to start and handles everything automatically.

### Prerequisites

1. **GitHub Account** - Create one at [github.com](https://github.com)
2. **Render Account** - Sign up at [render.com](https://render.com) (use your GitHub to sign in)
3. **Gmail Account** - For sending email notifications

### Step 1: Prepare Your Gmail

1. Go to your Google Account: [myaccount.google.com](https://myaccount.google.com)
2. Enable 2-Factor Authentication (if not already enabled)
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Create a new app password:
   - Select app: **Mail**
   - Select device: **Other** (type "Secure Form App")
   - Click **Generate**
   - **Save this 16-character password** - you'll need it later!

### Step 2: Push Code to GitHub

1. **Create a new repository on GitHub:**
   - Go to [github.com/new](https://github.com/new)
   - Name: `secure-form-app`
   - Keep it **Private** (important for security!)
   - Click **Create repository**

2. **Push your code:**
   ```bash
   cd "d:\secure form"
   git init
   git add .
   git commit -m "Initial commit - Secure Form App"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/secure-form-app.git
   git push -u origin main
   ```

### Step 3: Deploy to Render

1. **Go to Render Dashboard:**
   - Visit [dashboard.render.com](https://dashboard.render.com)
   - Click **New +** → **Web Service**

2. **Connect Your Repository:**
   - Click **Connect GitHub**
   - Select your `secure-form-app` repository
   - Click **Connect**

3. **Configure Your Service:**
   - **Name:** `secure-form-app` (or any name you like)
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Plan:** Select **Free** (or paid plan for better performance)

4. **Add Environment Variables:**
   Click **Advanced** → **Add Environment Variable** and add these:

   | Key | Value |
   |-----|-------|
   | `SECRET_KEY` | Click "Generate" or use a random string |
   | `ENCRYPTION_KEY` | Click "Generate" or use output from: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
   | `DEBUG` | `False` |
   | `FLASK_ENV` | `production` |
   | `MAIL_SERVER` | `smtp.gmail.com` |
   | `MAIL_PORT` | `587` |
   | `MAIL_USE_TLS` | `True` |
   | `MAIL_USERNAME` | Your Gmail address (e.g., `yourname@gmail.com`) |
   | `MAIL_PASSWORD` | The 16-character app password from Step 1 |
   | `MAIL_RECIPIENT` | Email where you want to receive submissions |
   | `ADMIN_USERNAME` | `admin` (or choose your own) |
   | `ADMIN_PASSWORD` | Choose a strong password for admin panel |

5. **Create PostgreSQL Database:**
   - In the same page, scroll to **Add Database**
   - Click **New PostgreSQL Database**
   - Name: `secure-form-db`
   - Plan: **Free**
   - Click **Create Database**
   - Render will automatically connect it to your web service

6. **Deploy:**
   - Click **Create Web Service**
   - Wait 3-5 minutes for deployment to complete
   - You'll see build logs in real-time

### Step 4: Access Your Application

Once deployment is complete:

1. **Your app URL:** `https://secure-form-app.onrender.com` (or your chosen name)
2. **Admin panel:** `https://secure-form-app.onrender.com/admin`
3. **Login credentials:** Use the `ADMIN_USERNAME` and `ADMIN_PASSWORD` you set

### Step 5: Test Everything

1. **Submit a test form:**
   - Go to your app URL
   - Fill out the form with test data
   - Submit

2. **Check email:**
   - You should receive an email with the document attached

3. **Check admin panel:**
   - Go to `/admin`
   - Login
   - You should see your submission
   - Click "Download" to get the document

---

## 🔧 Alternative Deployment Options

### Deploy to Heroku

1. **Create Heroku account:** [heroku.com](https://heroku.com)
2. **Install Heroku CLI:** [devcenter.heroku.com/articles/heroku-cli](https://devcenter.heroku.com/articles/heroku-cli)
3. **Deploy:**
   ```bash
   heroku login
   heroku create secure-form-app
   heroku addons:create heroku-postgresql:mini
   
   # Set environment variables
   heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
   heroku config:set ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
   heroku config:set DEBUG=False
   heroku config:set MAIL_USERNAME=your-email@gmail.com
   heroku config:set MAIL_PASSWORD=your-app-password
   heroku config:set MAIL_RECIPIENT=recipient@gmail.com
   heroku config:set ADMIN_USERNAME=admin
   heroku config:set ADMIN_PASSWORD=your-secure-password
   
   git push heroku main
   ```

### Deploy to Railway

1. **Create Railway account:** [railway.app](https://railway.app)
2. **Click "New Project" → "Deploy from GitHub"**
3. **Select your repository**
4. **Add PostgreSQL database** from Railway dashboard
5. **Set environment variables** (same as Render)
6. **Deploy automatically**

---

## 🔒 Security Checklist

After deployment, verify:

- [ ] HTTPS is enabled (should be automatic on Render/Heroku)
- [ ] `DEBUG=False` in production
- [ ] Strong `ADMIN_PASSWORD` is set
- [ ] `SECRET_KEY` and `ENCRYPTION_KEY` are randomly generated
- [ ] Email credentials are correct
- [ ] Repository is **Private** on GitHub
- [ ] `.env` file is NOT committed to Git (check `.gitignore`)

---

## 📧 How Email Works

After each form submission:
1. Document is generated as DOCX
2. Document is stored in database
3. Email is sent to `MAIL_RECIPIENT` with document attached
4. You can also download from admin panel anytime

---

## 🐛 Troubleshooting

### Email not sending?
- Check Gmail app password is correct (16 characters, no spaces)
- Verify `MAIL_USERNAME` is your full Gmail address
- Check Render logs for email errors

### Can't login to admin panel?
- Verify `ADMIN_USERNAME` and `ADMIN_PASSWORD` environment variables
- Try resetting password in Render dashboard

### Database errors?
- Render automatically creates PostgreSQL database
- Check that `DATABASE_URL` is set correctly
- View logs in Render dashboard

### App not loading?
- Check build logs in Render dashboard
- Verify all dependencies in `requirements.txt`
- Ensure `Procfile` is correct

---

## 📊 Monitoring

**View Logs:**
- Render: Dashboard → Your Service → Logs
- Heroku: `heroku logs --tail`

**Database Access:**
- Render: Dashboard → Database → Connect
- Use provided connection string with any PostgreSQL client

---

## 🔄 Updating Your App

When you make changes:

```bash
git add .
git commit -m "Description of changes"
git push origin main
```

Render will automatically redeploy! 🎉

---

## 💰 Cost Estimate

**Free Tier (Render):**
- Web Service: Free (sleeps after 15 min inactivity)
- PostgreSQL: Free (limited storage)
- Good for: Testing, low traffic

**Paid Tier ($7-25/month):**
- Always-on service
- More database storage
- Better performance
- Good for: Production use

---

## 📞 Support

If you encounter issues:
1. Check Render documentation: [render.com/docs](https://render.com/docs)
2. Review application logs
3. Verify all environment variables are set correctly

---

**Congratulations! Your secure form application is now live! 🎉**
