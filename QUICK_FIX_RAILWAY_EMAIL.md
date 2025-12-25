# Quick Fix: Railway Email Timeout

## ❌ Problem
```
⚠️ BREVO_API_KEY not set, attempting SMTP fallback
❌ SMTP failed: SMTP error: timed out
```

**Why?** Railway blocks SMTP connections (port 587), causing timeouts.

## ✅ Solution: Use Brevo API Instead

### Step 1: Get Brevo API Key (2 minutes)

1. **Login**: https://app.brevo.com/
2. **Go to**: Settings → **SMTP & API** → **API Keys** tab
3. **Click**: "Generate a new API key"
4. **Name**: `Django Password Reset`
5. **Permission**: **"Send emails"** ✓
6. **Click**: "Generate"
7. **COPY THE KEY** (looks like: `xkeysib-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-xxxxxxxx`)

### Step 2: Add to Railway (1 minute)

1. **Railway Dashboard** → Your Project → Your Service
2. **Click**: **Variables** tab
3. **Add New Variable**:
   ```
   Key: BREVO_API_KEY
   Value: [paste your API key here]
   ```
4. **Save** (Railway auto-redeploys)

### Step 3: Optional - Set FRONTEND_DOMAIN

Add this variable to avoid the warning:
```
Key: FRONTEND_DOMAIN
Value: https://uapcsedj-production.up.railway.app
```

## ✅ Result

After redeploy:
- ✅ Uses Brevo API (HTTPS - no timeouts!)
- ✅ More reliable than SMTP
- ✅ Faster email delivery
- ✅ Better error messages

## Test

1. Wait for Railway to redeploy (1-2 minutes)
2. Try forgot password on your live site
3. Check Railway logs - should see:
   ```
   ✅ Password reset email sent successfully to [email] via Brevo API
   ```

## Why Brevo API?

- ✅ **No timeouts** - Uses HTTPS (port 443) instead of SMTP (port 587)
- ✅ **Railway-friendly** - Cloud platforms don't block HTTPS
- ✅ **More reliable** - Better error handling
- ✅ **Faster** - No SMTP handshake delays

## Still Not Working?

Check Railway logs for:
- `✅` = Success
- `❌` = Error (check the error message)
- `⚠️` = Warning (usually not critical)

Look for: `✅ Password reset email sent successfully`

