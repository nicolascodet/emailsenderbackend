# CSV Outreach Usage Guide

## Overview
The `csv_outreach.py` script allows you to process CSV files (like those exported from Apollo, ZoomInfo, or other sales intelligence platforms) and run them through your existing outreach pipeline.

## Usage

### Basic Usage
```bash
python csv_outreach.py your_prospects.csv
```

### Advanced Usage
```bash
# Process only first 10 prospects
python csv_outreach.py your_prospects.csv --limit 10

# Start from row 50 (skip first 49 rows)
python csv_outreach.py your_prospects.csv --start-row 50

# Process 5 prospects starting from row 20
python csv_outreach.py your_prospects.csv --start-row 20 --limit 5
```

## Required CSV Columns

The script expects these key columns (case-sensitive):
- `First Name` - Required
- `Last Name` - Required  
- `Email` - Required
- `Title` - Optional but recommended
- `Company` or `Company Name for Emails` - At least one required
- `Person Linkedin Url` - Optional but helps with personalization
- `Website` - Optional but helps with company research
- `Work Direct Phone` - Optional

## CSV Format Support

The script is designed to work with Apollo CSV exports, but will work with any CSV that has the required columns. It handles:

- ✅ Missing/empty fields gracefully
- ✅ URL cleaning and validation
- ✅ Company name extraction from websites
- ✅ Phone number formatting
- ✅ LinkedIn URL validation

## Example CSV Structure

See `example_prospects.csv` for a sample file with the correct format.

## What Happens

1. **CSV Loading**: Reads and validates your CSV file
2. **Data Cleaning**: Cleans URLs, validates emails, handles missing data
3. **Prospect Creation**: Converts each row to a Prospect object
4. **Pipeline Processing**: Runs each prospect through your existing outreach pipeline:
   - LinkedIn scraping for personalization
   - Website analysis for company insights
   - AI message generation with personalized content
   - Email sending via Gmail
   - Google Sheets tracking

## Output

The script provides detailed output including:
- Number of prospects loaded and processed
- Individual success/failure status for each prospect
- Daily email count tracking
- Error messages for failed sends

## Tips

1. **Test First**: Use `--limit 1` to test with a single prospect
2. **Batch Processing**: Process in small batches (10-20) to avoid rate limits
3. **Resume Processing**: Use `--start-row` to resume from where you left off
4. **Check Daily Limits**: The system respects the 50 emails/day Gmail limit

## Error Handling

The script will:
- Skip rows with missing names or emails
- Continue processing even if some prospects fail
- Log detailed error messages
- Provide a summary of successes and failures

## Integration with Existing System

This script uses your existing:
- ✅ Outreach pipeline and all agents
- ✅ Gmail integration and daily limits
- ✅ Google Sheets tracking
- ✅ AI message generation
- ✅ LinkedIn and website scraping

No changes to your current setup are needed! 