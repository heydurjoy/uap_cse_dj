# Brevo (Sendinblue) Setup Guide - Free Forever

## Why Brevo?

- ✅ **300 emails/day FREE forever** (9,000/month)
- ✅ **No credit card required**
- ✅ **No time limit** - Truly free forever
- ✅ **Works great with Railway**
- ✅ **Easy SMTP setup**
- ✅ **Professional email delivery**

## Step 1: Create Brevo Account

1. **Go to Brevo**: https://www.brevo.com/
2. **Click "Sign up free"**
3. **Fill in your details**:
   - Email (use your institutional email if possible)
   - Password
   - Company name: `UAP CSE` (or your department)
4. **Verify your email** - Check inbox for verification link
5. **Complete profile** - Fill in basic information

## Step 2: Get SMTP Credentials

1. **Login to Brevo Dashboard**: https://app.brevo.com/
2. **Go to Settings** → **SMTP & API** (left sidebar)
3. **Click on "SMTP" tab**
4. **You'll see:**
   - **SMTP Server**: `smtp-relay.brevo.com`
   - **Port**: `587`
   - **Login**: Your SMTP login (looks like an email)
   - **Password**: Your SMTP password (click "Generate" if needed)

5. **Copy these credentials** - You'll need them for Railway

## Step 3: Verify Sender Email (Optional but Recommended)

1. **Go to Settings** → **Senders**
2. **Click "Add a sender"**
3. **Fill in:**
   - **Email**: `noreply@uap-cse.edu` (or your preferred email)
   - **Name**: `CSE UAP`
4. **Click "Save"**
5. **Check your email** - Brevo will send a verification link
6. **Click the verification link**
7. **Status should show "Verified"** ✅

**Note:** You can send from any email, but verified senders have better deliverability.

## Step 4: Update Railway Environment Variables

1. **Go to Railway Dashboard**: https://railway.app
2. **Select your project** → **Your Django service**
3. **Go to "Variables" tab**
4. **Add these environment variables**:

```
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_brevo_smtp_login
EMAIL_HOST_PASSWORD=your_brevo_smtp_password
EMAIL_FROM=noreply@uap-cse.edu
```

**Replace:**
- `your_brevo_smtp_login` with your Brevo SMTP login
- `your_brevo_smtp_password` with your Brevo SMTP password
- `noreply@uap-cse.edu` with your verified sender email (or any email)

## Step 5: Test

1. **Deploy your code** (settings.py already supports Brevo!)
2. **Try password reset** on your live site
3. **Check your email inbox** - You should receive the reset email! ✅

## Troubleshooting

### Emails Not Sending?

1. **Check Brevo Dashboard**:
   - Go to **Statistics** → **Email Activity**
   - See if emails are being sent
   - Check for any errors

2. **Verify Credentials**:
   - Make sure SMTP login and password are correct
   - Check Railway environment variables

3. **Check Email Limits**:
   - Free tier: 300 emails/day
   - Check your usage in Brevo dashboard
   - If exceeded, wait 24 hours

4. **Verify Sender**:
   - Make sure sender email is verified (optional but recommended)
   - Check Brevo → Settings → Senders

### Common Errors

**Error: "Authentication failed"**
- Check if SMTP credentials are correct
- Make sure you're using SMTP login (not API key)

**Error: "Sender not verified"**
- Verify your sender email in Brevo dashboard
- Or use a verified email address

**Error: "Daily limit exceeded"**
- You've sent more than 300 emails today
- Wait 24 hours or upgrade plan (but free tier is usually enough!)

## Brevo Dashboard Features

### Monitor Email Activity
- **Statistics** → **Email Activity**: See all sent emails
- **Statistics** → **Email Statistics**: View delivery rates
- **Statistics** → **Bounces**: See bounced emails

### Email Templates (Optional)
- You can create HTML email templates in Brevo
- For now, plain text emails work fine for password reset

## Cost

- **Free Tier**: 300 emails/day forever (9,000/month)
- **Paid Plans**: Start at €9/month for 20,000 emails
- **You likely won't need paid plan** unless you send newsletters

## Security Best Practices

1. ✅ **Never commit SMTP password to git**
2. ✅ **Use environment variables** (as we're doing)
3. ✅ **Monitor email activity** for suspicious activity
4. ✅ **Verify sender email** for better deliverability

## Next Steps

1. ✅ Create Brevo account
2. ✅ Get SMTP credentials
3. ✅ Verify sender email (optional)
4. ✅ Set Railway environment variables
5. ✅ Test password reset

## Summary

**Brevo Setup:**
1. Sign up at https://www.brevo.com/ (free)
2. Get SMTP credentials (Settings → SMTP & API)
3. Verify sender email (optional)
4. Add to Railway: `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`
5. Code will automatically use Brevo! ✅

**Benefits:**
- ✅ Free forever (300 emails/day)
- ✅ No credit card required
- ✅ Works reliably with Railway
- ✅ Professional email delivery
- ✅ Easy setup

