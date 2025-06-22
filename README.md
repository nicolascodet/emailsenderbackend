# 🚀 AI Outreach Pipeline - Multi-Agent Email Sniper

A sophisticated, modular AI-powered cold outreach system that automatically scrapes and analyzes prospects, determines which services to pitch, and generates personalized messages using Reddit-proven strategies.

## 🧠 System Overview

This system uses **6 specialized AI agents** working together:

1. **🔍 LinkedIn Scraper Agent** - Extracts profile data and classifies personality types
2. **🌐 Website Scraper Agent** - Analyzes company websites for business intelligence  
3. **🎯 Offer Matching Agent** - Determines the best service offering for each prospect
4. **📋 Strategy Selector Agent** - Selects optimal Reddit-proven outreach strategies
5. **✍️ Message Generator Agent** - Creates personalized emails using GPT-4
6. **📧 Email Sender Agent** - Sends via Gmail SMTP with smart rate limiting

## ✨ Key Features

- **Multi-Agent Architecture**: Modular, extensible design with specialized agents
- **Personality Classification**: AI-powered prospect personality analysis
- **Reddit-Proven Strategies**: Uses actual high-performing cold email templates
- **Smart Rate Limiting**: Respects Gmail limits (50 emails/day by default)
- **Business Intelligence**: Deep company analysis from websites
- **Offer Matching**: Automatically selects your best service for each prospect
- **FastAPI Backend**: RESTful API for integration
- **CLI Interface**: Command-line tool for direct usage

## 🛠 Installation

1. **Clone and setup:**
```bash
cd emailsenderbackend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Install Playwright browsers:**
```bash
playwright install chromium
```

3. **Setup environment variables:**
```bash
cp .env.example .env
# Edit .env with your credentials
```

## 🔧 Configuration

### Required Environment Variables

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Gmail SMTP Configuration
GMAIL_EMAIL=your_gmail@gmail.com
GMAIL_APP_PASSWORD=your_16_character_app_password

# Sender Information  
SENDER_NAME=Your Name

# Rate Limiting
DAILY_EMAIL_LIMIT=50
```

### Gmail Setup

1. Enable 2-Factor Authentication on your Gmail account
2. Generate an App Password: [Google Account Settings](https://myaccount.google.com/apppasswords)
3. Use the 16-character app password (not your regular password)

### Service Offerings

Edit `config/settings.py` to customize your service offerings:

```python
my_offers = [
    {
        "name": "Your Service Name",
        "description": "What you offer",
        "best_for": ["keywords", "that", "match"],
        "cta": "Try demo"  # or "Book discovery call", "Reply if curious"
    }
]
```

## 🚀 Usage

### Option 1: Command Line Interface

```bash
python cli_runner.py
```

Follow the prompts to input prospects and run the pipeline.

### Option 2: FastAPI Server

```bash
python api_server.py
# or
uvicorn api_server:app --reload
```

Then visit `http://localhost:8000/docs` for the interactive API documentation.

### Option 3: Direct Python Usage

```python
from outreach_pipeline import OutreachPipeline
from utils.models import Prospect

# Create prospects
prospects = [
    Prospect(
        name="John Doe",
        email="john@company.com", 
        linkedin_url="https://linkedin.com/in/johndoe",
        company_domain="company.com"
    )
]

# Run pipeline
pipeline = OutreachPipeline()
results = await pipeline.process_prospects(prospects)
```

## 📊 Input Formats

### CSV Format (Recommended)
```csv
Name,Email,LinkedIn URL,Company Domain,Phone
John Doe,john@company.com,https://linkedin.com/in/johndoe,company.com,555-1234
```

### Manual Input
```
John Doe, john@company.com, https://linkedin.com/in/johndoe, company.com
Jane Smith, jane@startup.io, https://linkedin.com/in/janesmith, startup.io
```

## 🎯 Reddit-Proven Strategies

The system includes 6 battle-tested strategies:

- **Funny Opener** - Light humor + value (18% success rate)
- **Value Bomb** - Lead with immediate value (22% success rate)  
- **Pain Point** - Address specific challenges (19% success rate)
- **Social Proof** - Leverage credibility (25% success rate)
- **Curiosity Gap** - Create intrigue (16% success rate)
- **Direct Benefit** - Straightforward approach (20% success rate)

## 📈 Rate Limiting & Best Practices

- **Start Conservative**: 10-20 emails/day, increase gradually
- **Warm Up New Accounts**: Begin with smaller volumes
- **Monitor Deliverability**: Track open rates and responses
- **Respect Limits**: System enforces daily limits automatically

## 🔍 API Endpoints

- `GET /` - API information
- `GET /status` - System status and email counts
- `POST /campaign/start` - Start new campaign
- `GET /campaign/{id}` - Check campaign status
- `GET /campaigns` - List all campaigns

## 📁 Project Structure

```
emailsenderbackend/
├── agents/                 # AI agents
│   ├── linkedin_scraper.py
│   ├── website_scraper.py
│   ├── offer_matcher.py
│   ├── strategy_selector.py
│   ├── message_generator.py
│   └── email_sender.py
├── config/                 # Configuration
│   └── settings.py
├── data/                   # Data files
│   └── reddit_strategies.json
├── utils/                  # Utilities
│   └── models.py
├── outreach_pipeline.py    # Main orchestrator
├── cli_runner.py          # CLI interface
├── api_server.py          # FastAPI server
└── requirements.txt
```

## 🛡 Security & Privacy

- All credentials stored in environment variables
- No data logging to external services
- LinkedIn scraping respects rate limits
- Email tracking stored locally only

## 🤝 Contributing

This system is designed to be modular and extensible:

1. **Add New Agents**: Create new agent classes following the existing pattern
2. **Custom Strategies**: Add new templates to `data/reddit_strategies.json`
3. **New Offers**: Modify service offerings in `config/settings.py`
4. **Enhanced Analysis**: Extend scraping and analysis capabilities

## 📝 License

MIT License - feel free to modify and extend for your needs.

## 🆘 Troubleshooting

### Common Issues

1. **Gmail Authentication Error**: Ensure you're using an App Password, not your regular password
2. **LinkedIn Scraping Fails**: LinkedIn may require login - consider using public profiles only
3. **Rate Limiting**: Respect the daily limits to maintain deliverability
4. **OpenAI API Errors**: Check your API key and billing status

### Support

Check the logs for detailed error messages. The system provides comprehensive logging at each step.

---

**Built for speed, scale, and effectiveness. Happy outreaching! 🎯**
