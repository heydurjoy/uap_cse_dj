# SendGrid Setup Guide for Password Reset

## Why SendGrid?

- ✅ **Free tier**: 100 emails/day (perfect for password resets)
- ✅ **Reliable**: Works great with Railway and other cloud platforms
- ✅ **No IP blocking**: Unlike Gmail, SendGrid is designed for cloud apps
- ✅ **Easy setup**: Simple API key configuration
- ✅ **Professional**: Better deliverability than Gmail SMTP

## Step 1: Create SendGrid Account

1. **Go to SendGrid**: https://signup.sendgrid.com/
2. **Sign up** with your email (use your institutional email if possible)
3. **Verify your email** - Check your inbox for verification link
4. **Complete setup** - Fill in basic information

## Step 2: Create API Key

1. **Login to SendGrid Dashboard**: https://app.sendgrid.com/
2. **Go to Settings** → **API Keys** (left sidebar)
3. **Click "Create API Key"**
4. **Name it**: `Django Password Reset` (or any name you prefer)
5. **Choose permissions**: Select **"Full Access"** (or "Restricted Access" with Mail Send permission)
6. **Click "Create & View"**
7. **IMPORTANT**: Copy the API key immediately - you won't be able to see it again!
   - It looks like: `SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

## Step 3: Verify Sender Identity (Required for Production)

SendGrid requires you to verify who you are before sending emails.

### Option A: Single Sender Verification (Easiest - Recommended)

1. **Go to Settings** → **Sender Authentication**
2. **Click "Verify a Single Sender"**
3. **Fill in the form**:
   - **From Email**: `noreply@uap-cse.edu` (or your preferred email)
   - **From Name**: `CSE UAP` (or your department name)
   - **Reply To**: Your actual email (e.g., `admin@uap-cse.edu`)
   - **Company Address**: Your institution's address
   - **Website**: Your website URL
4. **Click "Create"**
5. **Check your email** - SendGrid will send a verification link
6. **Click the verification link** in your email
7. **Status should change to "Verified"** ✅

### Option B: Domain Authentication (Advanced - Better for Production)

If you have access to your domain's DNS settings:
1. **Go to Settings** → **Sender Authentication** → **Authenticate Your Domain**
2. **Follow SendGrid's instructions** to add DNS records
3. **Wait for verification** (can take a few hours)

**For now, use Option A (Single Sender) - it's faster and works immediately!**

## Step 4: Update Django Settings

Update your `uap_cse_dj/settings.py`:

```python
# Email settings (for password reset)
# Use SendGrid in production, console backend in development

# Check if SendGrid credentials are provided
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', '')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')

if SENDGRID_API_KEY and EMAIL_HOST_USER:
    # Production: Use SendGrid
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.sendgrid.net'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = 'apikey'  # This is always 'apikey' for SendGrid
    EMAIL_HOST_PASSWORD = SENDGRID_API_KEY  # Your SendGrid API key
    DEFAULT_FROM_EMAIL = EMAIL_HOST_USER  # Use the verified sender email
elif EMAIL_HOST_USER and os.getenv('EMAIL_HOST_PASSWORD'):
    # Fallback: Use Gmail or other SMTP (if configured)
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = True
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
    DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
else:
    # Development: Use console backend (emails print to terminal)
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'noreply@uap-cse.edu'  # Just for display
```

## Step 5: Set Environment Variables in Railway

1. **Go to Railway Dashboard**: https://railway.app
2. **Select your project** → **Your Django service**
3. **Go to "Variables" tab**
4. **Add these environment variables**:

```
SENDGRID_API_KEY=SG.your_actual_api_key_here
EMAIL_HOST_USER=noreply@uap-cse.edu
```

**Important Notes:**
- Replace `SG.your_actual_api_key_here` with your actual SendGrid API key
- Replace `noreply@uap-cse.edu` with the email you verified in SendGrid
- The `EMAIL_HOST_USER` should match your verified sender email

## Step 6: Update Your Code

I'll update your `settings.py` file to use SendGrid properly. The code will:
- Use SendGrid if API key is provided
- Fall back to Gmail if Gmail credentials are provided
- Use console backend for local development (no credentials needed)

## Step 7: Test Locally (Development)

1. **Don't set environment variables locally** (or set them to empty)
2. **Run your Django server**
3. **Try password reset**
4. **Check your terminal** - You should see the email printed there
5. **Verify the reset link works**

## Step 8: Test in Production (Railway)

1. **Set environment variables in Railway** (as shown in Step 5)
2. **Deploy your code** (push to git)
3. **Wait for deployment to complete**
4. **Try password reset on your live site**
5. **Check your email inbox** - You should receive the reset email!
6. **Click the reset link** - Should work correctly

## Troubleshooting

### Emails Not Sending?

1. **Check SendGrid Dashboard**:
   - Go to **Activity** → **Email Activity**
   - See if emails are being sent
   - Check for any errors

2. **Check Railway Logs**:
   - Go to Railway → Your service → **Logs**
   - Look for email-related errors

3. **Verify API Key**:
   - Make sure `SENDGRID_API_KEY` is set correctly in Railway
   - Should start with `SG.`

4. **Verify Sender Email**:
   - Make sure `EMAIL_HOST_USER` matches your verified sender in SendGrid
   - Check SendGrid → Settings → Sender Authentication

5. **Check Email Limits**:
   - Free tier: 100 emails/day
   - Check your usage in SendGrid dashboard

### Common Errors

**Error: "Authentication failed"**
- Check if API key is correct
- Make sure `EMAIL_HOST_USER` is set to `apikey` (not your email)

**Error: "Sender not verified"**
- Verify your sender email in SendGrid dashboard
- Make sure `DEFAULT_FROM_EMAIL` matches verified sender

**Error: "Rate limit exceeded"**
- You've exceeded 100 emails/day (free tier limit)
- Wait 24 hours or upgrade plan

## SendGrid Dashboard Features

### Monitor Email Activity
- **Activity** → **Email Activity**: See all sent emails
- **Activity** → **Suppressions**: See blocked/bounced emails
- **Stats**: View email statistics

### Email Templates (Optional)
- You can create HTML email templates in SendGrid
- For now, plain text emails work fine for password reset

## Cost

- **Free Tier**: 100 emails/day forever (perfect for password resets!)
- **Paid Plans**: Start at $19.95/month for 50,000 emails
- **You likely won't need paid plan** unless you send newsletters

## Security Best Practices

1. ✅ **Never commit API keys to git**
2. ✅ **Use environment variables** (as we're doing)
3. ✅ **Rotate API keys** periodically
4. ✅ **Use restricted API keys** if possible (instead of full access)
5. ✅ **Monitor email activity** for suspicious activity

## Next Steps

1. ✅ Create SendGrid account
2. ✅ Get API key
3. ✅ Verify sender email
4. ✅ I'll update your code
5. ✅ Set Railway environment variables
6. ✅ Test password reset

## Summary

**SendGrid Setup:**
1. Sign up at https://signup.sendgrid.com/
2. Create API key (Settings → API Keys)
3. Verify sender email (Settings → Sender Authentication)
4. Add to Railway: `SENDGRID_API_KEY` and `EMAIL_HOST_USER`
5. Code will automatically use SendGrid in production!

**Benefits:**
- ✅ Works reliably with Railway
- ✅ Free tier (100 emails/day)
- ✅ Professional email delivery
- ✅ No IP blocking issues

