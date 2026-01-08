# Your Brevo Credentials - Verified ✅

## Your Current SMTP Credentials

```
SMTP Server: smtp-relay.brevo.com ✅
Port: 587 ✅
Login: 9ebce7001@smtp-brevo.com ✅
```

These are correct! However, we're using **Brevo API** instead of SMTP to avoid timeout issues.

## Option 1: Use Brevo API (Recommended - No Timeouts!)

### Get Your API Key:

1. **Login to Brevo**: https://app.brevo.com/
2. **Go to**: Settings → **SMTP & API** → **API Keys** tab
3. **Click "Generate a new API key"**
4. **Name**: `Django Password Reset`
5. **Permission**: **"Send emails"** (or Full access)
6. **Click "Generate"**
7. **Copy the API key** (looks like: `xkeysib-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-xxxxxxxx`)

### Add to Railway:

1. **Railway Dashboard** → Your Service → **Variables** tab
2. **Add this variable**:
   ```
   BREVO_API_KEY=xkeysib-your_actual_api_key_here
   ```

### Your Current Railway Variables Should Be:

```
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_HOST_USER=9ebce7001@smtp-brevo.com
EMAIL_HOST_PASSWORD=your_smtp_password_here
EMAIL_FROM=your_verified_email@example.com
BREVO_API_KEY=xkeysib-your_api_key_here  ← ADD THIS!
```

## Option 2: Keep Using SMTP (If You Prefer)

If you want to try SMTP again with the timeout fix:

1. **Make sure** you have the SMTP password (not shown above)
2. **Verify** all variables are set in Railway:
   ```
   EMAIL_HOST=smtp-relay.brevo.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=9ebce7001@smtp-brevo.com
   EMAIL_HOST_PASSWORD=your_smtp_password
   EMAIL_FROM=your_verified_email@example.com
   ```
3. **The code already has timeout protection** (10 seconds)

## Recommendation

**Use Brevo API** (Option 1) because:
- ✅ No timeout issues
- ✅ More reliable on Railway
- ✅ Faster
- ✅ Better error messages

## Next Steps

1. **Get Brevo API key** (if using API)
2. **Add `BREVO_API_KEY` to Railway** (if using API)
3. **Or verify SMTP password is set** (if using SMTP)
4. **Deploy and test**

## Quick Test

After setting up:
1. Go to your live site
2. Try forgot password
3. Should work! ✅










