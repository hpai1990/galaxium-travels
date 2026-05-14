import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import os
from datetime import datetime
import secrets

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending booking confirmation emails."""
    
    def __init__(self):
        """Initialize email service with SMTP configuration from environment."""
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@galaxiumtravels.com')
        self.from_name = os.getenv('FROM_NAME', 'Galaxium Travels')
        self.enabled = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
        
        if not self.enabled:
            logger.info("Email service is disabled. Set EMAIL_ENABLED=true to enable.")
    
    def generate_confirmation_code(self) -> str:
        """Generate a unique confirmation code for the booking."""
        return secrets.token_hex(6).upper()
    
    def create_booking_confirmation_email(
        self,
        customer_name: str,
        customer_email: str,
        booking_reference: str,
        confirmation_code: str,
        flight_origin: str,
        flight_destination: str,
        departure_date: str,
        return_date: Optional[str],
        seat_class: str,
        price_paid: int,
        passengers: int = 1
    ) -> tuple[str, str]:
        """
        Create booking confirmation email content.
        
        Returns:
            Tuple of (subject, html_body)
        """
        subject = f"Booking Confirmation - {booking_reference}"
        
        # Format dates for display
        try:
            dep_date = datetime.fromisoformat(departure_date.replace('Z', '+00:00'))
            departure_display = dep_date.strftime('%B %d, %Y at %H:%M UTC')
        except:
            departure_display = departure_date
        
        return_display = "One-way trip"
        if return_date:
            try:
                ret_date = datetime.fromisoformat(return_date.replace('Z', '+00:00'))
                return_display = ret_date.strftime('%B %d, %Y at %H:%M UTC')
            except:
                return_display = return_date
        
        # Create HTML email body
        html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Booking Confirmation</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f4f4f4;
        }}
        .container {{
            background-color: #ffffff;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            padding-bottom: 20px;
            border-bottom: 2px solid #4F46E5;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #4F46E5;
            margin: 0;
            font-size: 28px;
        }}
        .confirmation-code {{
            background-color: #F3F4F6;
            border-left: 4px solid #4F46E5;
            padding: 15px;
            margin: 20px 0;
            font-size: 18px;
            font-weight: bold;
            text-align: center;
            letter-spacing: 2px;
        }}
        .booking-details {{
            margin: 20px 0;
        }}
        .detail-row {{
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #E5E7EB;
        }}
        .detail-label {{
            font-weight: 600;
            color: #6B7280;
        }}
        .detail-value {{
            color: #111827;
            text-align: right;
        }}
        .highlight {{
            background-color: #FEF3C7;
            padding: 2px 6px;
            border-radius: 4px;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #E5E7EB;
            text-align: center;
            color: #6B7280;
            font-size: 14px;
        }}
        .button {{
            display: inline-block;
            padding: 12px 24px;
            background-color: #4F46E5;
            color: #ffffff;
            text-decoration: none;
            border-radius: 6px;
            margin: 20px 0;
        }}
        @media only screen and (max-width: 600px) {{
            body {{
                padding: 10px;
            }}
            .container {{
                padding: 20px;
            }}
            .detail-row {{
                flex-direction: column;
            }}
            .detail-value {{
                text-align: left;
                margin-top: 5px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Galaxium Travels</h1>
            <p style="margin: 10px 0 0 0; color: #6B7280;">Your Journey to the Stars Begins Here</p>
        </div>
        
        <p>Dear <strong>{customer_name}</strong>,</p>
        
        <p>Thank you for booking with Galaxium Travels! Your interstellar journey has been confirmed.</p>
        
        <div class="confirmation-code">
            Confirmation Code: {confirmation_code}
        </div>
        
        <div class="booking-details">
            <h2 style="color: #4F46E5; margin-bottom: 15px;">Booking Details</h2>
            
            <div class="detail-row">
                <span class="detail-label">Booking Reference:</span>
                <span class="detail-value"><strong>{booking_reference}</strong></span>
            </div>
            
            <div class="detail-row">
                <span class="detail-label">Route:</span>
                <span class="detail-value">{flight_origin} → {flight_destination}</span>
            </div>
            
            <div class="detail-row">
                <span class="detail-label">Departure:</span>
                <span class="detail-value">{departure_display}</span>
            </div>
            
            <div class="detail-row">
                <span class="detail-label">Return:</span>
                <span class="detail-value">{return_display}</span>
            </div>
            
            <div class="detail-row">
                <span class="detail-label">Seat Class:</span>
                <span class="detail-value"><span class="highlight">{seat_class.upper()}</span></span>
            </div>
            
            <div class="detail-row">
                <span class="detail-label">Passengers:</span>
                <span class="detail-value">{passengers}</span>
            </div>
            
            <div class="detail-row" style="border-bottom: 2px solid #4F46E5; font-size: 18px;">
                <span class="detail-label">Total Paid:</span>
                <span class="detail-value"><strong>${price_paid:,}</strong></span>
            </div>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <p style="color: #6B7280; margin-bottom: 10px;">Keep this confirmation code safe. You'll need it for check-in.</p>
        </div>
        
        <div class="footer">
            <p><strong>Important Information:</strong></p>
            <p style="margin: 10px 0;">Please arrive at the spaceport at least 3 hours before departure for security screening and boarding procedures.</p>
            <p style="margin: 10px 0;">For any questions or changes to your booking, please contact our support team.</p>
            <p style="margin-top: 20px; font-size: 12px;">
                This is an automated message. Please do not reply to this email.<br>
                © 2026 Galaxium Travels. All rights reserved.
            </p>
        </div>
    </div>
</body>
</html>
"""
        
        return subject, html_body
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        max_retries: int = 3
    ) -> bool:
        """
        Send an email with retry logic.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML content of the email
            max_retries: Maximum number of retry attempts
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info(f"Email service disabled. Would have sent email to {to_email}")
            logger.debug(f"Subject: {subject}")
            return True  # Return True in disabled mode to not block booking flow
        
        if not self.smtp_user or not self.smtp_password:
            logger.error("SMTP credentials not configured. Cannot send email.")
            return False
        
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # Create message
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = f"{self.from_name} <{self.from_email}>"
                msg['To'] = to_email
                
                # Attach HTML body
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
                
                # Send email
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
                
                logger.info(f"Email sent successfully to {to_email}")
                return True
                
            except smtplib.SMTPException as e:
                logger.warning(f"SMTP error on attempt {attempt + 1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Failed to send email to {to_email} after {max_retries} attempts")
                    return False
                    
            except Exception as e:
                logger.error(f"Unexpected error sending email to {to_email}: {e}")
                return False
        
        return False
    
    def send_booking_confirmation(
        self,
        customer_name: str,
        customer_email: str,
        booking_reference: str,
        flight_origin: str,
        flight_destination: str,
        departure_date: str,
        return_date: Optional[str],
        seat_class: str,
        price_paid: int,
        passengers: int = 1
    ) -> tuple[bool, str]:
        """
        Send a booking confirmation email.
        
        Returns:
            Tuple of (success: bool, confirmation_code: str)
        """
        # Generate confirmation code
        confirmation_code = self.generate_confirmation_code()
        
        # Create email content
        subject, html_body = self.create_booking_confirmation_email(
            customer_name=customer_name,
            customer_email=customer_email,
            booking_reference=booking_reference,
            confirmation_code=confirmation_code,
            flight_origin=flight_origin,
            flight_destination=flight_destination,
            departure_date=departure_date,
            return_date=return_date,
            seat_class=seat_class,
            price_paid=price_paid,
            passengers=passengers
        )
        
        # Send email
        success = self.send_email(
            to_email=customer_email,
            subject=subject,
            html_body=html_body
        )
        
        return success, confirmation_code


# Global email service instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create the global email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
