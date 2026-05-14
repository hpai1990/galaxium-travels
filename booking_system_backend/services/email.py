import smtplib
import logging
import secrets
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime
import os

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


def format_booking_reference(booking_id: int, booking_time: str) -> str:
    """Format booking reference number as GT-YYYY-XXXXX."""
    try:
        # Extract year from booking_time (ISO format)
        year = booking_time[:4]
        # Pad booking_id to 5 digits
        ref_number = f"GT-{year}-{booking_id:05d}"
        return ref_number
    except Exception as e:
        logger.error(f"Error formatting booking reference: {e}")
        return f"GT-{booking_id}"


def create_booking_email_html(
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
    
    # Format seat class for display
    seat_class_display = seat_class.capitalize()
    
    html = f"""
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
            background-color: #f4f4f4;
        }}
        .container {{
            background-color: #ffffff;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px 8px 0 0;
            margin: -30px -30px 20px -30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .confirmation-code {{
            background-color: #f8f9fa;
            border: 2px dashed #667eea;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            margin: 20px 0;
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
            letter-spacing: 2px;
        }}
        .booking-details {{
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
        .detail-row {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #e0e0e0;
        }}
        .detail-row:last-child {{
            border-bottom: none;
        }}
        .detail-label {{
            font-weight: bold;
            color: #666;
        }}
        .detail-value {{
            color: #333;
            text-align: right;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            color: #666;
            font-size: 14px;
        }}
        .highlight {{
            color: #667eea;
            font-weight: bold;
        }}
        @media only screen and (max-width: 600px) {{
            body {{
                padding: 10px;
            }}
            .container {{
                padding: 20px;
            }}
            .header {{
                margin: -20px -20px 20px -20px;
            }}
            .confirmation-code {{
                font-size: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Booking Confirmed!</h1>
        </div>
        
        <p>Dear <strong>{customer_name}</strong>,</p>
        
        <p>Thank you for booking with <span class="highlight">Galaxium Travels</span>! Your interstellar journey is confirmed.</p>
        
        <div class="confirmation-code">
            {confirmation_code}
        </div>
        
        <div class="booking-details">
            <h2 style="margin-top: 0; color: #667eea;">Booking Details</h2>
            
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
                <span class="detail-value">{departure_time}</span>
            </div>
            
            <div class="detail-row">
                <span class="detail-label">Arrival:</span>
                <span class="detail-value">{arrival_time}</span>
            </div>
            
            <div class="detail-row">
                <span class="detail-label">Seat Class:</span>
                <span class="detail-value">{seat_class_display}</span>
            </div>
            
            <div class="detail-row">
                <span class="detail-label">Total Paid:</span>
                <span class="detail-value">${price_paid:,}</span>
            </div>
        </div>
        
        <p><strong>Your confirmation code:</strong> <span class="highlight">{confirmation_code}</span></p>
        
        <p>Please keep this email for your records. You will need your confirmation code at check-in.</p>
        
        <div class="footer">
            <p><strong>Safe travels!</strong><br>
            The Galaxium Travels Team</p>
            <p style="font-size: 12px; color: #999;">
                This is an automated message. Please do not reply to this email.
            </p>
        </div>
    </div>
</body>
</html>
"""
    return html


def create_booking_email_text(
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
    """Create plain text email for booking confirmation."""
    
    seat_class_display = seat_class.capitalize()
    
    text = f"""
Dear {customer_name},

Thank you for booking with Galaxium Travels!

Your interstellar journey is confirmed.

BOOKING DETAILS
===============

Reference Number: {booking_reference}
Origin: {origin}
Destination: {destination}
Departure: {departure_time}
Arrival: {arrival_time}
Seat Class: {seat_class_display}
Total Paid: ${price_paid:,}

Your confirmation code: {confirmation_code}

Please keep this email for your records. You will need your confirmation code at check-in.

Safe travels!
The Galaxium Travels Team

---
This is an automated message. Please do not reply to this email.
"""
    return text


def send_booking_confirmation_email(
    to_email: str,
    customer_name: str,
    booking_id: int,
    booking_time: str,
    destination: str,
    origin: str,
    departure_time: str,
    arrival_time: str,
    seat_class: str,
    price_paid: int
) -> tuple[bool, Optional[str], str]:
    """
    Send booking confirmation email to customer.
    
    Args:
        to_email: Customer's email address
        customer_name: Customer's name
        booking_id: Booking ID from database
        booking_time: Booking timestamp (ISO format)
        destination: Flight destination
        origin: Flight origin
        departure_time: Flight departure time
        arrival_time: Flight arrival time
        seat_class: Seat class (economy/business/galaxium)
        price_paid: Total price paid
    
    Returns:
        Tuple of (success: bool, error_message: Optional[str], confirmation_code: str)
    """
    
    # Generate confirmation code
    confirmation_code = generate_confirmation_code()
    
    # Format booking reference
    booking_reference = format_booking_reference(booking_id, booking_time)
    
    # Get SMTP configuration from environment variables
    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_username = os.getenv('SMTP_USERNAME', '')
    smtp_password = os.getenv('SMTP_PASSWORD', '')
    smtp_from_email = os.getenv('SMTP_FROM_EMAIL', 'noreply@galaxiumtravels.com')
    smtp_from_name = os.getenv('SMTP_FROM_NAME', 'Galaxium Travels')
    
    # Check if SMTP is configured
    if not smtp_username or not smtp_password:
        logger.warning(
            f"SMTP not configured. Email would be sent to {to_email} "
            f"for booking {booking_reference} with confirmation code {confirmation_code}"
        )
        # In development/demo mode, just log and return success
        return True, None, confirmation_code
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Booking Confirmation - {booking_reference}'
        msg['From'] = f'{smtp_from_name} <{smtp_from_email}>'
        msg['To'] = to_email
        
        # Create plain text and HTML versions
        text_content = create_booking_email_text(
            customer_name=customer_name,
            booking_reference=booking_reference,
            confirmation_code=confirmation_code,
            destination=destination,
            origin=origin,
            departure_time=departure_time,
            arrival_time=arrival_time,
            seat_class=seat_class,
            price_paid=price_paid
        )
        
        html_content = create_booking_email_html(
            customer_name=customer_name,
            booking_reference=booking_reference,
            confirmation_code=confirmation_code,
            destination=destination,
            origin=origin,
            departure_time=departure_time,
            arrival_time=arrival_time,
            seat_class=seat_class,
            price_paid=price_paid
        )
        
        # Attach parts
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        logger.info(
            f"Booking confirmation email sent successfully to {to_email} "
            f"for booking {booking_reference}"
        )
        return True, None, confirmation_code
        
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"SMTP authentication failed: {str(e)}"
        logger.error(f"Failed to send booking confirmation email: {error_msg}")
        return False, error_msg, confirmation_code
        
    except smtplib.SMTPException as e:
        error_msg = f"SMTP error: {str(e)}"
        logger.error(f"Failed to send booking confirmation email: {error_msg}")
        return False, error_msg, confirmation_code
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"Failed to send booking confirmation email: {error_msg}")
        return False, error_msg, confirmation_code
