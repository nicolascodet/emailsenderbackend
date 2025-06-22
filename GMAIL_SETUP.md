# Gmail SMTP Setup Guide

To use Gmail SMTP with this application, you need to set up an App Password:

## Steps:

1. **Enable 2-Factor Authentication** (if not already enabled):
   - Go to https://myaccount.google.com/security
   - Under "How you sign in to Google", select "2-Step Verification"
   - Follow the setup process

2. **Generate App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" as the app
   - Select "Other (custom name)" as the device
   - Enter "AI Outreach Pipeline" as the name
   - Click "Generate"
   - Copy the 16-character password (it will look like: `abcd efgh ijkl mnop`)

3. **Update .env file**:
   ```
   GMAIL_PASSWORD=your-16-character-app-password-here
   ```

## Alternative: Use a different email provider
If you prefer not to use Gmail, you can use any SMTP provider by updating these settings in .env:
```
SMTP_SERVER=your-smtp-server.com
SMTP_PORT=587
GMAIL_EMAIL=your-email@domain.com
GMAIL_PASSWORD=your-password
```

## Current Status
The pipeline is working except for:
- LinkedIn scraping (browser closing issue)
- Gmail authentication (needs App Password)

Everything else is functional:
✅ Website analysis
✅ Offer matching  
✅ Strategy selection
✅ Message generation 