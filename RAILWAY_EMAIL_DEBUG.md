# Railway Email Debugging Guide

## Problem: Password Reset Emails Not Sending on Railway

The code has been updated with better error tracking and logging. Follow these steps to debug:

## Step 1: Check Railway Environment Variables

Go to **Railway Dashboard** → Your Project → Your Service → **Variables** tab

### Required Variables:

1. **BREVO_API_KEY** (Recommended - Most Reliable)
   ```
   Key: BREVO_API_KEY
   Value: xkeysib-your_actual_api_key_here
   ```
   - Get from: Brevo Dashboard → Settings → SMTP & API → API Keys
   - Must have "Send emails" permission

2. **EMAIL_FROM** (Required)
   ```
   Key: EMAIL_FROM
   Value: your_verified_email@example.com
   ```
   - Must match a verified sender in Brevo
   - Get from: Brevo Dashboard → Settings → Senders

3. **FRONTEND_DOMAIN** (Critical for Reset Links!)
   ```
   Key: FRONTEND_DOMAIN
   Value: https://uapcsedj-production.up.railway.app
   ```
   - Must be your actual Railway domain
   - Must include `https://` protocol
   - This is what generates the reset link URL

### Optional (SMTP Fallback):

4. **EMAIL_HOST**
   ```
   Key: EMAIL_HOST
   Value: smtp-relay.brevo.com
   ```

5. **EMAIL_PORT**
   ```
   Key: EMAIL_PORT
   Value: 587
   ```

6. **EMAIL_HOST_USER**
   ```
   Key: EMAIL_HOST_USER
   Value: your_brevo_smtp_login
   ```

7. **EMAIL_HOST_PASSWORD**
   ```
   Key: EMAIL_HOST_PASSWORD
   Value: your_brevo_smtp_password
   ```

## Step 2: Check Railway Logs

1. **Go to Railway Dashboard** → Your Service → **Deployments** tab
2. **Click on the latest deployment** → **View Logs**
3. **Or go to** → **Metrics** tab → **Logs**

### Look for these log messages:

✅ **Success indicators:**
- `✅ Password reset email sent successfully to [email] via Brevo API`
- `✅ Password reset email sent successfully to [email] via SMTP`

❌ **Error indicators:**
- `❌ Failed to send via Brevo API: [error]`
- `❌ SMTP fallback also failed: [error]`
- `⚠️ BREVO_API_KEY not set`
- `❌ Email configuration missing`

### Important log details:
- `Reset URL: [url]` - Check if this URL is correct
- `EMAIL_FROM: [email]` - Check if this matches your verified sender

## Step 3: Verify Brevo API Key

1. **Login to Brevo**: https://app.brevo.com/
2. **Go to**: Settings → SMTP & API → **API Keys** tab
3. **Check**:
   - API key exists and is active
   - Has "Send emails" permission
   - Copy the full key (starts with `xkeysib-`)

4. **Verify in Railway**:
   - Go to Railway Variables
   - Check `BREVO_API_KEY` value matches exactly (no extra spaces)

## Step 4: Verify FRONTEND_DOMAIN

**This is critical!** If `FRONTEND_DOMAIN` is wrong, the reset link won't work.

1. **Check your Railway domain**:
   - Railway Dashboard → Your Service → **Settings** → **Domains**
   - Copy the exact domain (e.g., `uapcsedj-production.up.railway.app`)

2. **Set FRONTEND_DOMAIN**:
   ```
   FRONTEND_DOMAIN=https://uapcsedj-production.up.railway.app
   ```
   - Must include `https://`
   - Must match your Railway domain exactly
   - No trailing slash

3. **Check logs** for `Reset URL:` - it should be:
   ```
   https://uapcsedj-production.up.railway.app/reset-password/[token]/
   ```

## Step 5: Test Email Sending

After updating variables:

1. **Redeploy** (Railway auto-redeploys when variables change)
2. **Wait for deployment** to complete
3. **Try forgot password** on your live site
4. **Check Railway logs** immediately after submitting

## Step 6: Check Brevo Dashboard

1. **Login to Brevo**: https://app.brevo.com/
2. **Go to**: Statistics → **Email Activity**
3. **Look for**:
   - Recent password reset emails
   - Any failed/bounced emails
   - Error messages

## Common Issues & Solutions

### Issue 1: "BREVO_API_KEY not set"
**Solution**: Add `BREVO_API_KEY` to Railway variables

### Issue 2: "Brevo API error: 401 Unauthorized"
**Solution**: 
- API key is invalid or expired
- Regenerate API key in Brevo
- Update Railway variable

### Issue 3: "Brevo API error: 400 Bad Request"
**Solution**:
- Check `EMAIL_FROM` matches verified sender
- Check email format in payload

### Issue 4: "SMTP credentials not configured"
**Solution**:
- Set `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` in Railway
- Or use `BREVO_API_KEY` instead (recommended)

### Issue 5: Reset link doesn't work
**Solution**:
- Check `FRONTEND_DOMAIN` is set correctly
- Must be `https://your-domain.railway.app` (with https://)
- Check logs for `Reset URL:` to verify

### Issue 6: Email sent but not received
**Solution**:
- Check spam/junk folder
- Check Brevo dashboard → Email Activity
- Verify recipient email is correct
- Check if email domain is blocked

## Quick Checklist

- [ ] `BREVO_API_KEY` is set in Railway
- [ ] `EMAIL_FROM` is set and matches verified sender
- [ ] `FRONTEND_DOMAIN` is set with `https://` and correct domain
- [ ] Railway logs show email sending attempts
- [ ] Brevo dashboard shows email activity
- [ ] No errors in Railway logs

## Still Not Working?

1. **Check Railway logs** for specific error messages
2. **Check Brevo dashboard** → Email Activity
3. **Verify all environment variables** are set correctly
4. **Try regenerating** Brevo API key
5. **Check** if Railway domain changed (update FRONTEND_DOMAIN)

## Updated Code Features

The updated code now:
- ✅ Tracks email sending success/failure
- ✅ Logs detailed error messages
- ✅ Shows errors in DEBUG mode
- ✅ Logs all configuration details
- ✅ Tries SMTP fallback if API fails
- ✅ Provides clear error messages in logs

Check Railway logs after each password reset attempt to see what's happening!

