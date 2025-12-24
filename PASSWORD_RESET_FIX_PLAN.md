# Password Reset Fix Plan

## Problems Identified

1. **Hardcoded Email Credentials** - Email password is exposed in `settings.py`
2. **No Environment Variable Support** - Settings don't use env vars for production
3. **Gmail May Block Railway** - Gmail often blocks connections from cloud platforms
4. **No Development Fallback** - No console/file backend for local testing

## Solution Plan

### Phase 1: Secure Email Configuration (Priority: HIGH)

**Goal:** Move email credentials to environment variables

**Steps:**
1. Update `settings.py` to read email config from environment variables
2. Add fallback to console backend for development (when env vars not set)
3. Document required environment variables
4. Update Railway environment variables

**Changes:**
- `EMAIL_HOST_USER` → `os.getenv('EMAIL_HOST_USER', '')`
- `EMAIL_HOST_PASSWORD` → `os.getenv('EMAIL_HOST_PASSWORD', '')`
- `EMAIL_BACKEND` → Use console backend if no credentials provided (dev mode)

### Phase 2: Alternative Email Providers (Priority: MEDIUM)

**Goal:** Provide options if Gmail doesn't work

**Options:**
1. **SendGrid** (Recommended for production)
   - Free tier: 100 emails/day
   - Reliable for cloud platforms
   - Easy setup with Railway

2. **Mailgun** (Alternative)
   - Free tier: 5,000 emails/month
   - Good for production

3. **Resend** (Modern option)
   - Free tier: 3,000 emails/month
   - Developer-friendly API

4. **Keep Gmail** (If it works)
   - Use app password via environment variable
   - May need to enable "Less secure app access" or use OAuth2

### Phase 3: Better Error Handling (Priority: MEDIUM)

**Goal:** Improve user experience when email fails

**Steps:**
1. Add better error messages
2. Log email failures properly
3. Consider showing reset link in admin (for testing)
4. Add email sending status check

### Phase 4: Testing & Verification (Priority: HIGH)

**Goal:** Ensure password reset works in production

**Steps:**
1. Test email sending locally (console backend)
2. Test email sending in Railway (with real SMTP)
3. Verify reset links work correctly
4. Test token expiration
5. Test email delivery

## Implementation Order

1. ✅ **Phase 1** - Secure email configuration (do this first)
2. ✅ **Phase 4** - Test locally
3. ✅ **Phase 2** - Set up SendGrid (if Gmail fails)
4. ✅ **Phase 3** - Improve error handling
5. ✅ **Phase 4** - Test in production

## Recommended Approach

**For Production (Railway):**
- Use **SendGrid** (most reliable for cloud platforms)
- Set environment variables in Railway dashboard
- Remove hardcoded credentials from code

**For Development:**
- Use console backend (emails print to terminal)
- No credentials needed
- Easy to test

## Environment Variables Needed

```bash
# For Gmail
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# OR for SendGrid
EMAIL_HOST=smtp.sendgrid.net
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
EMAIL_PORT=587
EMAIL_USE_TLS=True
```

## Next Steps

1. Review this plan
2. Choose email provider (SendGrid recommended)
3. Implement Phase 1 (secure configuration)
4. Test locally
5. Set up Railway environment variables
6. Test in production

