"""
Email Sender Agent - Sends emails via Gmail SMTP with rate limiting
"""
import asyncio
import logging
import smtplib
import pickle
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
from typing import Optional

from config.settings import settings
from utils.models import OutreachMessage, CampaignResult

logger = logging.getLogger(__name__)

class EmailSenderAgent:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.today_count = self._load_daily_count()
        
    def _load_daily_count(self) -> int:
        """Load today's email count from tracking file"""
        try:
            if os.path.exists(settings.tracking_file):
                with open(settings.tracking_file, 'rb') as f:
                    data = pickle.load(f)
                    if data.get('date') == str(date.today()):
                        return data.get('count', 0)
            return 0
        except Exception as e:
            logger.warning(f"Could not load email tracking: {e}")
            return 0
    
    def _save_daily_count(self):
        """Save today's email count to tracking file"""
        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(settings.tracking_file), exist_ok=True)
            
            data = {
                'date': str(date.today()),
                'count': self.today_count
            }
            with open(settings.tracking_file, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            logger.warning(f"Could not save email tracking: {e}")
    
    def can_send_email(self) -> bool:
        """Check if we can send another email today"""
        return self.today_count < settings.daily_email_limit
    
    def get_remaining_emails(self) -> int:
        """Get number of emails remaining for today"""
        return max(0, settings.daily_email_limit - self.today_count)
    
    async def send_email(self, message: OutreachMessage) -> CampaignResult:
        """
        Send email via Gmail SMTP
        """
        try:
            # Check daily limit
            if not self.can_send_email():
                error_msg = f"Daily email limit reached ({settings.daily_email_limit})"
                logger.warning(error_msg)
                return CampaignResult(
                    prospect=message.prospect,
                    message=message,
                    sent=False,
                    error=error_msg
                )
            
            # Validate Gmail credentials
            if not settings.gmail_email or not settings.gmail_app_password:
                error_msg = "Gmail credentials not found. Please set GMAIL_EMAIL and GMAIL_APP_PASSWORD in .env"
                logger.error(error_msg)
                return CampaignResult(
                    prospect=message.prospect,
                    message=message,
                    sent=False,
                    error=error_msg
                )
            
            # Send the email
            success = await self._send_via_smtp(message)
            
            if success:
                # Update daily count
                self.today_count += 1
                self._save_daily_count()
                
                logger.info(f"Email sent successfully to {message.prospect.email} ({self.today_count}/{settings.daily_email_limit} today)")
                
                return CampaignResult(
                    prospect=message.prospect,
                    message=message,
                    sent=True,
                    sent_at=datetime.now().isoformat()
                )
            else:
                return CampaignResult(
                    prospect=message.prospect,
                    message=message,
                    sent=False,
                    error="SMTP send failed"
                )
            
        except Exception as e:
            error_msg = f"Unexpected error sending email: {str(e)}"
            logger.error(error_msg)
            return CampaignResult(
                prospect=message.prospect,
                message=message,
                sent=False,
                error=error_msg
            )
    
    async def _send_via_smtp(self, message: OutreachMessage) -> bool:
        """
        Send email via SMTP (runs in thread to avoid blocking)
        """
        def _smtp_send():
            try:
                # Create message
                msg = MIMEMultipart()
                msg['From'] = f"{settings.sender_name} <{settings.gmail_email}>"
                msg['To'] = str(message.prospect.email)
                msg['Subject'] = message.subject_line
                
                # Add body to email
                msg.attach(MIMEText(message.message_body, 'plain'))
                
                # Connect to Gmail SMTP server
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()  # Enable security
                server.login(settings.gmail_email, settings.gmail_app_password)
                
                # Send email
                text = msg.as_string()
                server.sendmail(settings.gmail_email, str(message.prospect.email), text)
                server.quit()
                
                return True
                
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"Gmail authentication failed: {str(e)}")
                return False
            except smtplib.SMTPException as e:
                logger.error(f"SMTP error: {str(e)}")
                return False
            except Exception as e:
                logger.error(f"Unexpected SMTP error: {str(e)}")
                return False
        
        # Run SMTP in thread to avoid blocking
        return await asyncio.to_thread(_smtp_send) 