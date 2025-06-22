# Google Sheets Tracking Setup Guide

This guide will help you set up Google Sheets tracking for the cold email pipeline.

## 🎯 Overview

The Google Sheets tracker automatically logs every prospect processed through the pipeline with detailed information including:

- **Basic Info**: Name, company, email, LinkedIn URL, website URL
- **Research Data**: Triggers found, business focus, services offered
- **Quality Metrics**: Research quality score, validation results
- **Email Content**: Subject line, email body, AI application summary
- **Status**: Sent/skipped with reasons

## 📋 CSV Columns Tracked

| Column | Description |
|--------|-------------|
| `timestamp` | When the prospect was processed |
| `prospect_name` | Full name of the prospect |
| `company` | Company name |
| `email` | Email address |
| `linkedin_url` | LinkedIn profile URL |
| `website_url` | Company website URL |
| `status` | 'sent' or 'skipped' |
| `trigger_found` | 'Yes' or 'No' |
| `trigger_details` | Specific triggers found |
| `ai_application` | AI application mentioned in email |
| `subject_line` | Email subject line |
| `email_body` | Full email content |
| `skip_reason` | Reason for skipping (if applicable) |
| `research_quality_score` | Quality score (e.g., "4/5") |
| `personality_type` | Detected personality type |
| `services_offered` | Company's main services |
| `ai_info` | 10-word summary: "what they do - what we offered" |

## 🔧 Setup Instructions

### Step 1: Service Account Setup

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Select Project**: `emailscraper-451905`
3. **Enable APIs**:
   - Google Sheets API
   - Google Drive API
4. **Create Service Account** (if not exists):
   - Name: `emailscraprebot`
   - Email: `emailscraprebot@emailscraper-451905.iam.gserviceaccount.com`

### Step 2: Download Credentials

1. **Go to IAM & Admin > Service Accounts**
2. **Find service account**: `emailscraprebot@emailscraper-451905.iam.gserviceaccount.com`
3. **Click Actions > Manage Keys**
4. **Add Key > Create New Key > JSON**
5. **Download the JSON file**
6. **Rename to**: `google_sheets_credentials.json`
7. **Place in**: `/emailsenderbackend/` directory

### Step 3: Google Sheets Setup

1. **Create or Open Sheet**: "Cold Email Tracking"
2. **Share Sheet** with service account email:
   - Click "Share" button
   - Add: `emailscraprebot@emailscraper-451905.iam.gserviceaccount.com`
   - Permission: "Editor"
   - Uncheck "Notify people"

### Step 4: Test Connection

```bash
cd emailsenderbackend
python test_sheets_integration.py
```

Expected output:
```
🔍 Testing Google Sheets connection...
✅ Connected to existing sheet: 'Cold Email Tracking'
✅ Google Sheets tracker connected successfully
✅ Google Sheets connection test passed
🧪 Testing prospect logging...
✅ Logged Test Prospect to Google Sheets (Status: sent)
✅ Logged Skipped Prospect to Google Sheets (Status: skipped)
✅ Test logging completed!
📊 Daily stats: {'sent': 1, 'skipped': 1, 'total': 2}
🎉 Google Sheets integration test passed!
```

## 🚀 Usage

The Google Sheets tracker is automatically integrated into the pipeline. It will:

### ✅ Log Successful Emails
- All research data
- Email content
- Quality metrics
- AI application summary

### ⚠️ Log Skipped Emails
- Reason for skipping
- Available research data
- Quality gate results

### 📊 Track All Scenarios
- Quality gate failures
- Offer matching failures
- Strategy selection failures
- Message generation failures
- Email sending failures
- Pipeline errors

## 🔍 Example AI Info Summaries

The `ai_info` column provides 10-word summaries in the format "what they do - what we offered":

- `"Estate planning firm - offered will drafting automation"`
- `"Water damage restoration - offered workflow automation tools"`
- `"Construction company - offered project management AI"`
- `"Property management - offered AI automation tools"`

## 📈 Daily Statistics

Get daily stats programmatically:

```python
from utils.google_sheets_tracker import GoogleSheetsTracker

tracker = GoogleSheetsTracker()
stats = tracker.get_daily_stats()
print(f"Today: {stats['sent']} sent, {stats['skipped']} skipped")
```

## 🛠️ Troubleshooting

### Connection Issues

**Error**: `Credentials file not found`
- **Solution**: Ensure `google_sheets_credentials.json` exists in `/emailsenderbackend/`

**Error**: `Google Auth error`
- **Solution**: Re-download credentials file from Google Cloud Console

**Error**: `SpreadsheetNotFound`
- **Solution**: Create sheet named "Cold Email Tracking" or check sharing permissions

### Permission Issues

**Error**: `Insufficient permissions`
- **Solution**: Share sheet with service account email as "Editor"

**Error**: `API not enabled`
- **Solution**: Enable Google Sheets API and Google Drive API in Google Cloud Console

### Data Issues

**Error**: Missing data in columns
- **Solution**: Check that all agents are returning expected data structures

**Error**: AI info not generating properly
- **Solution**: Verify research data contains `services_offered` or `business_focus`

## 🔒 Security Notes

- Service account credentials are sensitive - keep them secure
- Don't commit `google_sheets_credentials.json` to version control
- Use `.gitignore` to exclude credentials file
- Regularly rotate service account keys

## 📝 Manual Logging

You can also log prospects manually:

```python
from utils.google_sheets_tracker import GoogleSheetsTracker
from utils.models import Prospect

tracker = GoogleSheetsTracker()

prospect = Prospect(
    name="John Doe",
    company="Example Corp",
    email="john@example.com",
    linkedin_url="https://linkedin.com/in/johndoe",
    website_url="https://example.com"
)

# Log successful email
tracker.log_sent_email(
    prospect=prospect,
    research_data=research_data,
    selected_offer=offer,
    outreach_message=message
)

# Log skipped email
tracker.log_skipped_email(
    prospect=prospect,
    skip_reason="Quality gate failed",
    research_data=research_data
)
```

## 🎉 Integration Complete!

The Google Sheets tracker is now fully integrated with your cold email pipeline. Every prospect will be automatically logged with comprehensive data for analysis and tracking. 