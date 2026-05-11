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
        
    def _generate_confirmation_code(self) -> str:
        """Generate a unique confirmation code."""
        return secrets.token_hex(6).upper()
    
    def _create_booking_confirmation_html(
        self,
        customer_name: str,
        booking_reference: str,
        confirmation_code: str,
        destination: str,
        departure_date: str,
        return_date: str,
        passengers: int,
        seat_class: str,
        price_paid: int
    ) -> str:
        """Create HTML email template for booking confirmation."""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Booking Confirmation</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px 10px 0 0;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
        }}
        .content {{
            background: #f9f9f9;
            padding: 30px;
            border-radius: 0 0 10px 10px;
        }}
        .booking-details {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .detail-row {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }}
        .detail-row:last-child {{
            border-bottom: none;
        }}
        .detail-label {{
            font-weight: bold;
            color: #667eea;
        }}
        .confirmation-code {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: center;
            border-radius: 8px;
            font-size: 24px;
            font-weight: bold;
            letter-spacing: 2px;
            margin: 20px 0;
        }}
        .footer {{
            text-align: center;
            color: #666;
            font-size: 12px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }}
        @media only screen and (max-width: 600px) {{
            body {{
                padding: 10px;
            }}
            .header h1 {{
                font-size: 22px;
            }}
            .confirmation-code {{
                font-size: 18px;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Booking Confirmed!</h1>
        <p>Thank you for choosing Galaxium Travels</p>
    </div>
    
    <div class="content">
        <p>Dear {customer_name},</p>
        
        <p>Your booking has been confirmed! We're excited to have you aboard for your journey to the stars.</p>
        
        <div class="booking-details">
            <h2 style="color: #667eea; margin-top: 0;">Booking Details</h2>
            
            <div class="detail-row">
                <span class="detail-label">Reference Number:</span>
                <span>{booking_reference}</span>
            </div>
            
            <div class="detail-row">
                <span class="detail-label">Destination:</span>
                <span>{destination}</span>
            </div>
            
            <div class="detail-row">
                <span class="detail-label">Departure Date:</span>
                <span>{departure_date}</span>
            </div>
            
            <div class="detail-row">
                <span class="detail-label">Return Date:</span>
                <span>{return_date}</span>
            </div>
            
            <div class="detail-row">
                <span class="detail-label">Passengers:</span>
                <span>{passengers}</span>
            </div>
            
            <div class="detail-row">
                <span class="detail-label">Seat Class:</span>
                <span>{seat_class.title()}</span>
            </div>
            
            <div class="detail-row">
                <span class="detail-label">Total Paid:</span>
                <span>${price_paid:,}</span>
            </div>
        </div>
        
        <p><strong>Your Confirmation Code:</strong></p>
        <div class="confirmation-code">
            {confirmation_code}
        </div>
        
        <p>Please keep this confirmation code safe. You'll need it for check-in and boarding.</p>
        
        <p><strong>Important Information:</strong></p>
        <ul>
            <li>Check-in opens 24 hours before departure</li>
            <li>Arrive at the spaceport at least 3 hours before departure</li>
            <li>Bring a valid ID and your confirmation code</li>
            <li>Review our baggage policy on our website</li>
        </ul>
        
        <p>If you have any questions or need to make changes to your booking, please contact our customer service team.</p>
        
        <p>Safe travels among the stars!</p>
        
        <p><strong>The Galaxium Travels Team</strong></p>
    </div>
    
    <div class="footer">
        <p>This is an automated message. Please do not reply to this email.</p>
        <p>&copy; 2026 Galaxium Travels. All rights reserved.</p>
    </div>
</body>
</html>
"""
    
    def _create_booking_confirmation_text(
        self,
        customer_name: str,
        booking_reference: str,
        confirmation_code: str,
        destination: str,
        departure_date: str,
        return_date: str,
        passengers: int,
        seat_class: str,
        price_paid: int
    ) -> str:
        """Create plain text email template for booking confirmation."""
        return f"""
BOOKING CONFIRMED - Galaxium Travels

Dear {customer_name},

Thank you for booking with Galaxium Travels!

BOOKING DETAILS
===============

Reference Number: {booking_reference}
Destination: {destination}
Departure Date: {departure_date}
Return Date: {return_date}
Passengers: {passengers}
Seat Class: {seat_class.title()}
Total Paid: ${price_paid:,}

YOUR CONFIRMATION CODE
======================
{confirmation_code}

Please keep this confirmation code safe. You'll need it for check-in and boarding.

IMPORTANT INFORMATION
=====================
- Check-in opens 24 hours before departure
- Arrive at the spaceport at least 3 hours before departure
- Bring a valid ID and your confirmation code
- Review our baggage policy on our website

If you have any questions or need to make changes to your booking, please contact our customer service team.

Safe travels among the stars!

The Galaxium Travels Team

---
This is an automated message. Please do not reply to this email.
© 2026 Galaxium Travels. All rights reserved.
"""
    
    def send_booking_confirmation(
        self,
        to_email: str,
        customer_name: str,
        booking_reference: str,
        destination: str,
        departure_date: str,
        return_date: str,
        passengers: int = 1,
        seat_class: str = 'economy',
        price_paid: int = 0
    ) -> bool:
        """
        Send booking confirmation email.
        
        Args:
            to_email: Recipient email address
            customer_name: Customer's name
            booking_reference: Booking reference number (e.g., GT-2026-12345)
            destination: Travel destination
            departure_date: Departure date string
            return_date: Return date string
            passengers: Number of passengers
            seat_class: Seat class (economy, business, galaxium)
            price_paid: Total price paid
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info(f"Email service disabled. Would have sent confirmation to {to_email}")
            return True
        
        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP credentials not configured. Cannot send email.")
            return False
        
        try:
            # Generate confirmation code
            confirmation_code = self._generate_confirmation_code()
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'Booking Confirmation - {booking_reference}'
            msg['From'] = f'{self.from_name} <{self.from_email}>'
            msg['To'] = to_email
            
            # Create plain text and HTML versions
            text_content = self._create_booking_confirmation_text(
                customer_name=customer_name,
                booking_reference=booking_reference,
                confirmation_code=confirmation_code,
                destination=destination,
                departure_date=departure_date,
                return_date=return_date,
                passengers=passengers,
                seat_class=seat_class,
                price_paid=price_paid
            )
            
            html_content = self._create_booking_confirmation_html(
                customer_name=customer_name,
                booking_reference=booking_reference,
                confirmation_code=confirmation_code,
                destination=destination,
                departure_date=departure_date,
                return_date=return_date,
                passengers=passengers,
                seat_class=seat_class,
                price_paid=price_paid
            )
            
            # Attach parts
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email with retry logic
            max_retries = 3
            retry_delay = 1
            
            for attempt in range(max_retries):
                try:
                    with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                        server.starttls()
                        server.login(self.smtp_user, self.smtp_password)
                        server.send_message(msg)
                    
                    logger.info(f"Booking confirmation email sent successfully to {to_email} (confirmation: {confirmation_code})")
                    return True
                    
                except smtplib.SMTPException as e:
                    logger.warning(f"Email send attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        logger.error(f"Failed to send email after {max_retries} attempts: {e}")
                        return False
            
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error sending booking confirmation email: {e}", exc_info=True)
            return False


# Global email service instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create the global email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
