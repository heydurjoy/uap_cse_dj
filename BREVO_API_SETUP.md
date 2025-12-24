# Brevo API Setup - Fix SMTP Timeout Issue

## Problem

SMTP connections are timing out on Railway. This is a common issue with cloud platforms blocking outbound SMTP connections.

## Solution: Use Brevo API Instead

Brevo's API is more reliable than SMTP for cloud platforms like Railway. It uses HTTPS requests instead of SMTP connections.

## Step 1: Get Your Brevo API Key

1. **Login to Brevo**: https://app.brevo.com/
2. **Go to**: Settings → **SMTP & API** → **API Keys** tab
3. **Click "Generate a new API key"**
4. **Name it**: `Django Password Reset`
5. **Select permissions**: **"Send emails"** (or Full access)
6. **Click "Generate"**
7. **COPY THE API KEY** - You'll need it for Railway

## Step 2: Add API Key to Railway

1. **Go to Railway Dashboard**: https://railway.app
2. **Your Project** → **Your Service** → **Variables** tab
3. **Add this variable**:
   ```
   BREVO_API_KEY=your_brevo_api_key_here
   ```

**Important:**
- Keep your existing SMTP variables (as fallback)
- Add `BREVO_API_KEY` as a new variable
- The code will use API first, then fall back to SMTP if API key is not set

## Step 3: Deploy

1. **Push your code** (the code is already updated!)
2. **Wait for deployment**
3. **Test password reset**

## How It Works

The code now:
1. **First tries Brevo API** (if `BREVO_API_KEY` is set) - More reliable!
2. **Falls back to SMTP** (if API key not set) - For other providers

## Benefits of API

- ✅ **No connection timeouts** - Uses HTTPS requests
- ✅ **More reliable** - Works better with cloud platforms
- ✅ **Faster** - No SMTP handshake delays
- ✅ **Better error messages** - Clear API responses

## Testing

After adding `BREVO_API_KEY`:
1. Deploy your code
2. Try password reset
3. Should work without timeout! ✅

## Troubleshooting

### Still Getting Timeout?

1. **Check API key** is set correctly in Railway
2. **Verify API key** has "Send emails" permission
3. **Check Brevo dashboard** → Statistics → Email Activity
4. **Check Railway logs** for specific error

### API Key Not Working?

1. **Regenerate API key** in Brevo dashboard
2. **Make sure** it has correct permissions
3. **Update** Railway variable with new key
4. **Redeploy**

## Summary

**Quick Fix:**
1. Get Brevo API key (Settings → SMTP & API → API Keys)
2. Add `BREVO_API_KEY` to Railway variables
3. Deploy
4. Done! ✅

The code is already updated to use the API when available!

