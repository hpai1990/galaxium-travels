import smtplib
import logging
import secrets
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime
import os
from sqlalchemy.orm import Session
from models import Booking, Flight, User

logger = logging.getLogger(__name__)


def generate_confirmation_code(length: int = 9) -> str:
    """Generate a unique confirmation code for booking."""
    # Format: ABC123XYZ (3 letters, 3 digits, 3 letters)
    letters = string.ascii_uppercase
    digits = string.digits
    
    code = (
        ''.join(secrets.choice(letters) for _ in range(3)) +
        ''.join(secrets.choice(digits) for _ in range(3)) +
        ''.join(secrets.choice(letters) for _ in range(3))
    )
    return code


def format_booking_reference(booking_id: int) -> str:
    """Format booking ID into a reference number."""
    return f"GT-2026-{booking_id:05d}"


def create_email_template(
    customer_name: str,
    booking_reference: str,
    confirmation_code: str,
    destination: str,
    origin: str,
    departure_time: str,
    arrival_time: str,
    seat_class: str,
    price_paid: int
) -> str:
    """Create HTML email template for booking confirmation."""
    
    # Parse dates for better formatting
    try:
        dep_date = datetime.fromisoformat(departure_time.replace('Z', '+00:00'))
        arr_date = datetime.fromisoformat(arrival_time.replace('Z', '+00:00'))
        departure_formatted = dep_date.strftime("%B %d, %Y at %H:%M UTC")
        arrival_formatted = arr_date.strftime("%B %d, %Y at %H:%M UTC")
    except:
        departure_formatted = departure_time
        arrival_formatted = arrival_time
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
                border: 1px solid #ddd;
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
            .detail-value {{
                color: #333;
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
                background: #333;
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 0 0 10px 10px;
                font-size: 14px;
            }}
            .footer a {{
                color: #667eea;
                text-decoration: none;
            }}
            @media only screen and (max-width: 600px) {{
                body {{
                    padding: 10px;
                }}
                .header h1 {{
                    font-size: 24px;
                }}
                .content {{
                    padding: 20px;
                }}
                .confirmation-code {{
                    font-size: 20px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 Booking Confirmed!</h1>
            <p>Your journey to the stars awaits</p>
        </div>
        
        <div class="content">
            <p>Dear {customer_name},</p>
            
            <p>Thank you for booking with <strong>Galaxium Travels</strong>! Your space journey has been confirmed.</p>
            
            <div class="booking-details">
                <h2 style="color: #667eea; margin-top: 0;">Booking Details</h2>
                
                <div class="detail-row">
                    <span class="detail-label">Reference Number:</span>
                    <span class="detail-value">{booking_reference}</span>
                </div>
                
                <div class="detail-row">
                    <span class="detail-label">Origin:</span>
                    <span class="detail-value">{origin}</span>
                </div>
                
                <div class="detail-row">
                    <span class="detail-label">Destination:</span>
                    <span class="detail-value">{destination}</span>
                </div>
                
                <div class="detail-row">
                    <span class="detail-label">Departure:</span>
                    <span class="detail-value">{departure_formatted}</span>
                </div>
                
                <div class="detail-row">
                    <span class="detail-label">Arrival:</span>
                    <span class="detail-value">{arrival_formatted}</span>
                </div>
                
                <div class="detail-row">
                    <span class="detail-label">Seat Class:</span>
                    <span class="detail-value">{seat_class.title()}</span>
                </div>
                
                <div class="detail-row">
                    <span class="detail-label">Total Paid:</span>
                    <span class="detail-value">${price_paid:,}</span>
                </div>
            </div>
            
            <p><strong>Your Confirmation Code:</strong></p>
            <div class="confirmation-code">
                {confirmation_code}
            </div>
            
            <p style="font-size: 14px; color: #666;">
                Please keep this confirmation code safe. You'll need it for check-in and boarding.
            </p>
            
            <p>We're excited to have you aboard! If you have any questions, please don't hesitate to contact our support team.</p>
            
            <p style="margin-top: 30px;">
                Safe travels!<br>
                <strong>The Galaxium Travels Team</strong>
            </p>
        </div>
        
        <div class="footer">
            <p>© 2026 Galaxium Travels | Your Gateway to the Stars</p>
            <p>
                <a href="#">View Booking</a> | 
                <a href="#">Contact Support</a> | 
                <a href="#">Travel Guidelines</a>
            </p>
        </div>
    </body>
    </html>
    """
    
    return html_content


def send_booking_confirmation_email(
    db: Session,
    booking_id: int,
    smtp_server: Optional[str] = None,
    smtp_port: Optional[int] = None,
    smtp_username: Optional[str] = None,
    smtp_password: Optional[str] = None,
    from_email: Optional[str] = None
) -> dict:
    """
    Send booking confirmation email to the customer.
    
    Args:
        db: Database session
        booking_id: ID of the booking
        smtp_server: SMTP server address (defaults to env var)
        smtp_port: SMTP port (defaults to env var)
        smtp_username: SMTP username (defaults to env var)
        smtp_password: SMTP password (defaults to env var)
        from_email: Sender email address (defaults to env var)
    
    Returns:
        dict with status and details
    """
    # Get configuration from environment or parameters
    smtp_server = smtp_server or os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = smtp_port or int(os.getenv('SMTP_PORT', '587'))
    smtp_username = smtp_username or os.getenv('SMTP_USERNAME', '')
    smtp_password = smtp_password or os.getenv('SMTP_PASSWORD', '')
    from_email = from_email or os.getenv('FROM_EMAIL', 'noreply@galaxiumtravels.com')
    
    # Check if email is enabled
    email_enabled = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
    
    try:
        # Fetch booking details
        booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
        if not booking:
            logger.error(f"Booking {booking_id} not found")
            return {
                'success': False,
                'error': 'Booking not found',
                'booking_id': booking_id
            }
        
        # Fetch related flight and user
        flight = db.query(Flight).filter(Flight.flight_id == booking.flight_id).first()
        user = db.query(User).filter(User.user_id == booking.user_id).first()
        
        if not flight or not user:
            logger.error(f"Flight or user not found for booking {booking_id}")
            return {
                'success': False,
                'error': 'Flight or user not found',
                'booking_id': booking_id
            }
        
        # Generate confirmation code
        confirmation_code = generate_confirmation_code()
        booking_reference = format_booking_reference(booking_id)
        
        # Create email content
        html_content = create_email_template(
            customer_name=user.name,
            booking_reference=booking_reference,
            confirmation_code=confirmation_code,
            destination=flight.destination,
            origin=flight.origin,
            departure_time=flight.departure_time,
            arrival_time=flight.arrival_time,
            seat_class=booking.seat_class,
            price_paid=booking.price_paid
        )
        
        # Create plain text version
        text_content = f"""
Booking Confirmation - {booking_reference}

Dear {user.name},

Thank you for booking with Galaxium Travels!

Booking Details:

Reference: {booking_reference}
Origin: {flight.origin}
Destination: {flight.destination}
Departure: {flight.departure_time}
Arrival: {flight.arrival_time}
Seat Class: {booking.seat_class.title()}
Total Paid: ${booking.price_paid:,}

Your confirmation code: {confirmation_code}

Safe travels!
Galaxium Travels Team
        """
        
        # If email is not enabled, just log and return success
        if not email_enabled:
            logger.info(f"Email sending disabled. Would have sent confirmation to {user.email}")
            logger.info(f"Confirmation code: {confirmation_code}")
            return {
                'success': True,
                'message': 'Email sending disabled (demo mode)',
                'booking_id': booking_id,
                'confirmation_code': confirmation_code,
                'booking_reference': booking_reference,
                'recipient': user.email
            }
        
        # Create message
        message = MIMEMultipart('alternative')
        message['Subject'] = f"Booking Confirmation - {booking_reference}"
        message['From'] = from_email
        message['To'] = user.email
        
        # Attach both plain text and HTML versions
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        message.attach(part1)
        message.attach(part2)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            if smtp_username and smtp_password:
                server.login(smtp_username, smtp_password)
            server.send_message(message)
        
        logger.info(f"Booking confirmation email sent successfully to {user.email}")
        
        return {
            'success': True,
            'message': 'Email sent successfully',
            'booking_id': booking_id,
            'confirmation_code': confirmation_code,
            'booking_reference': booking_reference,
            'recipient': user.email
        }
        
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending email for booking {booking_id}: {str(e)}")
        return {
            'success': False,
            'error': f'SMTP error: {str(e)}',
            'booking_id': booking_id
        }
    except Exception as e:
        logger.error(f"Error sending email for booking {booking_id}: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'booking_id': booking_id
        }
