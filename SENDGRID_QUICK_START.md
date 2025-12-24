# SendGrid Quick Start - 5 Minutes Setup

## 🚀 Quick Steps

### 1. Create Account (2 minutes)
- Go to: https://signup.sendgrid.com/
- Sign up and verify your email

### 2. Get API Key (1 minute)
- Login: https://app.sendgrid.com/
- Settings → API Keys → Create API Key
- Name: `Django Password Reset`
- Permission: **Full Access**
- **COPY THE KEY** (starts with `SG.`)

### 3. Verify Sender (1 minute)
- Settings → Sender Authentication → Verify a Single Sender
- Email: `noreply@uap-cse.edu` (or your preferred email)
- Name: `CSE UAP`
- **Check your email and click verify link**

### 4. Add to Railway (1 minute)
- Railway Dashboard → Your Service → Variables
- Add:
  ```
  SENDGRID_API_KEY=SG.your_key_here
  EMAIL_HOST_USER=noreply@uap-cse.edu
  ```

### 5. Deploy & Test
- Push your code (settings.py is already updated!)
- Try password reset on your live site
- Check your email inbox ✅

## ✅ Done!

Your password reset will now work in production!

## 📋 What Changed

- ✅ `settings.py` now supports SendGrid
- ✅ Automatically uses SendGrid if API key is set
- ✅ Falls back to console backend for local development
- ✅ No hardcoded credentials (secure!)

## 🔍 Testing

**Local (Development):**
- No env vars needed
- Emails print to terminal
- Perfect for testing!

**Production (Railway):**
- Set `SENDGRID_API_KEY` and `EMAIL_HOST_USER`
- Emails sent via SendGrid
- Works reliably!

## ❓ Need Help?

See `SENDGRID_SETUP_GUIDE.md` for detailed instructions.

