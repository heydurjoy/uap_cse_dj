# Brevo Quick Start - Free Forever Email Setup

## 🚀 5-Minute Setup

### Step 1: Sign Up (2 minutes)
- Go to: https://www.brevo.com/
- Click "Sign up free"
- Verify your email

### Step 2: Get SMTP Credentials (1 minute)
- Login: https://app.brevo.com/
- Settings → SMTP & API → SMTP tab
- Copy:
  - **SMTP Server**: `smtp-relay.brevo.com`
  - **Port**: `587`
  - **Login**: (your SMTP login)
  - **Password**: (your SMTP password - generate if needed)

### Step 3: Verify Sender (1 minute - Optional)
- Settings → Senders → Add a sender
- Email: `noreply@uap-cse.edu`
- Name: `CSE UAP`
- Check email and verify ✅

### Step 4: Add to Railway (1 minute)
- Railway Dashboard → Your Service → Variables
- Add these:
  ```
  EMAIL_HOST=smtp-relay.brevo.com
  EMAIL_PORT=587
  EMAIL_HOST_USER=your_brevo_smtp_login
  EMAIL_HOST_PASSWORD=your_brevo_smtp_password
  EMAIL_FROM=noreply@uap-cse.edu
  ```

### Step 5: Deploy & Test
- Push your code (settings.py already updated!)
- Try password reset on live site
- Check email inbox ✅

## ✅ Done!

**Free forever:** 300 emails/day (9,000/month) - More than enough for password resets!

## 📋 What You Get

- ✅ **300 emails/day FREE forever**
- ✅ **No credit card required**
- ✅ **No time limit**
- ✅ **Works with Railway**
- ✅ **Professional delivery**

## 🔍 Need More Details?

See `BREVO_SETUP_GUIDE.md` for complete instructions.

## 💡 Other Free Options?

See `FREE_EMAIL_OPTIONS.md` for:
- Resend (3,000/month free)
- Gmail (free but may have Railway issues)
- Outlook (free, works with Railway)

