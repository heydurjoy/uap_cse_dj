# Fix Railway Environment Variables

## ❌ Problem

Your environment variables might have placeholder text instead of actual values:
- `EMAIL_HOST_USER=The email address you just verified` ❌
- `EMAIL_HOST_PASSWORD=The long SMTP Key you copied earlier` ❌

These need to be replaced with **actual values** from Brevo!

## ✅ Correct Values

### Step 1: Get Your Brevo SMTP Credentials

1. **Login to Brevo**: https://app.brevo.com/
2. **Go to**: Settings → SMTP & API → **SMTP** tab
3. **You'll see**:
   - **SMTP Server**: `smtp-relay.brevo.com` ✅ (this is correct)
   - **Port**: `587` ✅ (this is correct)
   - **Login**: This is your `EMAIL_HOST_USER` - **COPY THIS!**
   - **Password**: This is your `EMAIL_HOST_PASSWORD` - **COPY THIS!**

### Step 2: Get Your Verified Sender Email

1. **Go to**: Settings → **Senders**
2. **Find your verified sender email** (the one you verified earlier)
3. **This is your `EMAIL_FROM`** - **COPY THIS!**

## 🔧 Update Railway Variables

### Go to Railway Dashboard:

1. **Railway Dashboard** → Your Project → Your Service
2. **Click "Variables" tab**
3. **Update each variable** with actual values:

### Variable 1: EMAIL_HOST
```
Key: EMAIL_HOST
Value: smtp-relay.brevo.com
```
✅ This should already be correct!

### Variable 2: EMAIL_PORT
```
Key: EMAIL_PORT
Value: 587
```
✅ This should already be correct!

### Variable 3: EMAIL_HOST_USER
```
Key: EMAIL_HOST_USER
Value: [Your Brevo SMTP Login - from Settings → SMTP & API]
```
**Example**: `your-email@example.com` or `smtp123456@brevo.com`

**NOT**: "The email address you just verified" ❌

### Variable 4: EMAIL_HOST_PASSWORD
```
Key: EMAIL_HOST_PASSWORD
Value: [Your Brevo SMTP Password - from Settings → SMTP & API]
```
**Example**: `AbCdEfGhIjKlMnOpQrStUvWxYz123456`

**NOT**: "The long SMTP Key you copied earlier" ❌

### Variable 5: EMAIL_FROM
```
Key: EMAIL_FROM
Value: [Your verified sender email - from Settings → Senders]
```
**Example**: `noreply@uap-cse.edu` or `your-email@example.com`

**NOT**: "The email address you just verified" ❌

## 📋 Example (What It Should Look Like)

```
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_HOST_USER=smtp123456@brevo.com
EMAIL_HOST_PASSWORD=AbCdEfGhIjKlMnOpQrStUvWxYz123456
EMAIL_FROM=noreply@uap-cse.edu
```

## 🔍 How to Find Your Brevo Credentials

### SMTP Login & Password:

1. **Login to Brevo**: https://app.brevo.com/
2. **Settings** → **SMTP & API** → **SMTP** tab
3. **You'll see**:
   ```
   SMTP Server: smtp-relay.brevo.com
   Port: 587
   Login: [THIS IS YOUR EMAIL_HOST_USER]
   Password: [THIS IS YOUR EMAIL_HOST_PASSWORD - click "Generate" if needed]
   ```

### Verified Sender Email:

1. **Settings** → **Senders**
2. **Find the email you verified** (status should be "Verified")
3. **That email is your EMAIL_FROM**

## ⚠️ Important Notes

1. **SMTP Login** might look like an email address (e.g., `smtp123456@brevo.com`)
2. **SMTP Password** is a long random string (not your Brevo account password!)
3. **If you don't see SMTP password**, click "Generate" to create one
4. **EMAIL_FROM** should match your verified sender email

## ✅ After Updating

1. **Save the variables** in Railway
2. **Railway will automatically redeploy** (or trigger a redeploy)
3. **Wait for deployment to complete**
4. **Test password reset again**

## 🧪 Test

After updating variables:
1. Go to your live site
2. Try forgot password
3. Should work now! ✅

## ❓ Still Not Working?

1. **Check Railway Logs** for specific error
2. **Verify credentials** in Brevo dashboard
3. **Make sure** all variables have actual values (not placeholder text)
4. **Check** that EMAIL_FROM matches your verified sender

