# Test Password Reset with Brevo

## ✅ Setup Complete!

You've added Brevo variables to Railway and deployed. Now let's test!

## 🧪 Testing Steps

### Step 1: Verify Environment Variables

Check that these are set in Railway:
- ✅ `EMAIL_HOST=smtp-relay.brevo.com`
- ✅ `EMAIL_PORT=587`
- ✅ `EMAIL_HOST_USER=your_brevo_smtp_login`
- ✅ `EMAIL_HOST_PASSWORD=your_brevo_smtp_password`
- ✅ `EMAIL_FROM=noreply@uap-cse.edu` (or your verified sender)

### Step 2: Test Password Reset

1. **Go to your live site**: `https://your-app.up.railway.app`
2. **Click "Forgot Password"** (or go to `/forgot-password/`)
3. **Enter an email** that:
   - Is in your `AllowedEmail` list
   - Has a `BaseUser` account
   - Is active
4. **Click "Send Reset Link"**
5. **Check for success message**: "Password reset link has been sent to your email address"

### Step 3: Check Your Email

1. **Check inbox** of the email you entered
2. **Look for email from**: `noreply@uap-cse.edu` (or your EMAIL_FROM)
3. **Subject**: "Password Reset Request - CSE UAP"
4. **Click the reset link** in the email

### Step 4: Reset Password

1. **Enter new password** (at least 8 characters)
2. **Confirm password**
3. **Click "Reset Password"**
4. **Should redirect to login** with success message
5. **Try logging in** with new password ✅

## 🔍 Troubleshooting

### Email Not Received?

1. **Check Railway Logs**:
   - Railway Dashboard → Your Service → Logs
   - Look for email-related errors
   - Check for SMTP authentication errors

2. **Check Brevo Dashboard**:
   - Login: https://app.brevo.com/
   - Go to **Statistics** → **Email Activity**
   - See if email was sent
   - Check for any errors or bounces

3. **Verify Environment Variables**:
   - Railway → Your Service → Variables
   - Make sure all variables are set correctly
   - Check for typos in SMTP credentials

4. **Check Email Limits**:
   - Brevo free tier: 300 emails/day
   - Check usage in Brevo dashboard
   - If exceeded, wait 24 hours

5. **Check Spam Folder**:
   - Sometimes emails go to spam
   - Check spam/junk folder

### Common Errors

**"Failed to send password reset email"**
- Check Railway logs for specific error
- Verify SMTP credentials are correct
- Check Brevo dashboard for errors

**"Authentication failed"**
- SMTP login or password incorrect
- Double-check credentials in Railway variables

**"Sender not verified"**
- Verify sender email in Brevo dashboard
- Settings → Senders → Verify your email

**Email sent but not received**
- Check spam folder
- Verify recipient email is correct
- Check Brevo → Statistics → Email Activity

### Verify Brevo is Working

1. **Check Brevo Dashboard**:
   - Login: https://app.brevo.com/
   - Statistics → Email Activity
   - You should see your password reset emails listed
   - Check delivery status

2. **Check Email Statistics**:
   - Statistics → Email Statistics
   - See delivery rates, bounces, etc.

## ✅ Success Indicators

You'll know it's working when:
- ✅ Success message appears after requesting reset
- ✅ Email arrives in inbox (check spam too!)
- ✅ Reset link works when clicked
- ✅ Password can be changed successfully
- ✅ Can login with new password
- ✅ Brevo dashboard shows sent emails

## 🎯 Quick Test Checklist

- [ ] Environment variables set in Railway
- [ ] Code deployed successfully
- [ ] Can access forgot password page
- [ ] Success message appears after submitting email
- [ ] Email received in inbox
- [ ] Reset link works
- [ ] Password can be changed
- [ ] Can login with new password
- [ ] Brevo dashboard shows sent emails

## 📊 Monitor in Brevo

**Check regularly:**
- **Statistics** → **Email Activity**: See all sent emails
- **Statistics** → **Email Statistics**: Delivery rates
- **Statistics** → **Bounces**: Failed deliveries

## 🚀 Next Steps

Once password reset is working:
1. ✅ Test with different user accounts
2. ✅ Monitor Brevo dashboard for any issues
3. ✅ Check Railway logs periodically
4. ✅ Document any issues for future reference

## 💡 Pro Tips

1. **Monitor Brevo Dashboard**: Check email activity regularly
2. **Check Spam**: First emails might go to spam until reputation builds
3. **Verify Sender**: Verified senders have better deliverability
4. **Test Regularly**: Test password reset periodically to ensure it works
5. **Keep Credentials Safe**: Never commit SMTP passwords to git

## 🎉 You're All Set!

If everything works:
- ✅ Password reset emails are being sent via Brevo
- ✅ Free forever (300 emails/day)
- ✅ Professional email delivery
- ✅ No more email issues!

If you encounter any problems, check the troubleshooting section above or Railway/Brevo logs.

