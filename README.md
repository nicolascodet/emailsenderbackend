# Email Generator

A Python script that generates personalized emails based on company websites and information.

## Features
- Scrapes company websites for key information
- Uses AI to analyze content and generate personalized insights
- Creates natural, conversational email drafts
- Handles multiple companies in batch

## Installation

1. Clone the repository:
```bash
git clone https://github.com/nicolascodet/emailsenderbackend.git
cd emailsenderbackend
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

1. Prepare your data in tab-separated format with these columns:
   - Company Name
   - Website
   - Address
   - LinkedIn URL
   - Industry
   - Company Size
   - Decision Maker Name
   - Title
   - Email
   - LinkedIn Profile
   
2. Run the script:
```bash
python website_analyzer.py
```

3. Paste your data when prompted and press Ctrl+D (Cmd+D on Mac) when done.

4. The script will create email drafts in your default mail client.

## Requirements
- Python 3.8+
- OpenAI API key
- See requirements.txt for Python package dependencies
