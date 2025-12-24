# Debug Email Internal Server Error

## ✅ You've Set Actual Values - Now Let's Debug

Since you've set the actual values but still getting Internal Server Error, let's find the exact issue.

## 🔍 Step 1: Check Railway Logs

**This is the most important step!**

1. **Go to Railway Dashboard**: https://railway.app
2. **Your Project** → **Your Service**
3. **Click "Logs" tab**
4. **Look for the error** - It will show the exact problem

**Common errors you might see:**

### Error 1: "Authentication failed"
```
SMTPAuthenticationError: (535, 'Authentication failed')
```
**Fix**: Check that `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` are correct

### Error 2: "Connection refused"
```
ConnectionRefusedError: [Errno 111] Connection refused
```
**Fix**: Check that `EMAIL_HOST` is `smtp-relay.brevo.com`

### Error 3: "NameError" or "AttributeError"
```
NameError: name 'EMAIL_HOST_ENV' is not defined
```
**Fix**: Code issue - but we've already fixed this

### Error 4: "Invalid email address"
```
ValueError: Invalid email address
```
**Fix**: Check that `EMAIL_FROM` is a valid email format

## 🔍 Step 2: Verify Your Variables

Double-check in Railway that your variables look like this:

```
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_HOST_USER=something@brevo.com (or your actual SMTP login)
EMAIL_HOST_PASSWORD=long_random_string_here
EMAIL_FROM=your-verified-email@example.com
```

**Important checks:**
- ✅ No extra spaces before/after values
- ✅ No quotes around values
- ✅ EMAIL_HOST_USER is the SMTP login (not your Brevo account email)
- ✅ EMAIL_HOST_PASSWORD is the SMTP password (not your Brevo account password)
- ✅ EMAIL_FROM is a valid email address

## 🔍 Step 3: Test SMTP Connection

The error might be happening when trying to connect to Brevo. Let's add better error handling.

## 🔍 Step 4: Check Brevo Dashboard

1. **Login to Brevo**: https://app.brevo.com/
2. **Go to**: Statistics → Email Activity
3. **See if any emails were attempted** - This tells us if the connection worked

## 🛠️ Quick Fixes to Try

### Fix 1: Verify SMTP Credentials Format

Make sure your `EMAIL_HOST_USER` is:
- The SMTP login from Brevo (usually looks like `smtp123456@brevo.com` or an email)
- NOT your Brevo account email
- NOT "The email address you just verified"

Make sure your `EMAIL_HOST_PASSWORD` is:
- The SMTP password from Brevo (long random string)
- NOT your Brevo account password
- If you don't see it, click "Generate" in Brevo dashboard

### Fix 2: Check Email Format

Make sure `EMAIL_FROM` is:
- A valid email address format
- Matches your verified sender (if you verified one)
- Example: `noreply@uap-cse.edu` or `your-email@example.com`

### Fix 3: Redeploy

After updating variables:
1. **Trigger a redeploy** in Railway
2. **Or make a small code change** and push
3. **Wait for deployment to complete**

## 📋 What to Share

If you can share:
1. **The exact error from Railway logs** (most important!)
2. **A screenshot of your Railway variables** (hide sensitive values)
3. **What happens** when you try password reset

Then I can give you the exact fix!

## 🧪 Quick Test

Try this in Railway terminal (if available):
```bash
cd /app
python manage.py shell
```

Then:
```python
from django.core.mail import send_mail
from django.conf import settings

print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"EMAIL_FROM: {settings.DEFAULT_FROM_EMAIL}")

# Try sending a test email
try:
    send_mail(
        'Test',
        'Test message',
        settings.DEFAULT_FROM_EMAIL,
        ['your-email@example.com'],
        fail_silently=False,
    )
    print("Email sent successfully!")
except Exception as e:
    print(f"Error: {e}")
```

This will show you exactly what's wrong.

