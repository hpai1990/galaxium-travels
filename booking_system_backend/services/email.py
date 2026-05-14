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
    # Format: ABC123XYZ (3 letters, 3 numbers, 3 letters)
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
    # Format: GT-2026-12345
    year = datetime.now().year
    return f"GT-{year}-{booking_id:05d}"


def create_booking_confirmation_email(
    customer_name: str,
    customer_email: str,
    booking_id: int,
    origin: str,
    destination: str,
    departure_time: str,
    return_time: Optional[str],
    seat_class: str,
    price_paid: int,
    passengers: int = 1
) -> tuple[str, str]:
    """
    Create booking confirmation email content.
    
    Returns:
        Tuple of (subject, html_body)
    """
    booking_ref = format_booking_reference(booking_id)
    confirmation_code = generate_confirmation_code()
    
    # Parse departure time for display
    try:
        departure_date = datetime.fromisoformat(departure_time.replace(' ', 'T'))
        departure_display = departure_date.strftime('%B %d, %Y at %I:%M %p')
    except:
        departure_display = departure_time
    
    # Parse return time if provided
    return_display = ""
    if return_time:
        try:
            return_date = datetime.fromisoformat(return_time.replace(' ', 'T'))
            return_display = f"<tr><td style='padding: 8px; border-bottom: 1px solid #e0e0e0;'><strong>Return:</strong></td><td style='padding: 8px; border-bottom: 1px solid #e0e0e0;'>{return_date.strftime('%B %d, %Y at %I:%M %p')}</td></tr>"
        except:
            return_display = f"<tr><td style='padding: 8px; border-bottom: 1px solid #e0e0e0;'><strong>Return:</strong></td><td style='padding: 8px; border-bottom: 1px solid #e0e0e0;'>{return_time}</td></tr>"
    
    subject = f"Booking Confirmation - {booking_ref}"
    
    html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Booking Confirmation</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 20px 0;">
                <table role="presentation" style="width: 100%; max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px;">🚀 Galaxium Travels</h1>
                            <p style="margin: 10px 0 0 0; color: #ffffff; font-size: 16px;">Your Journey to the Stars</p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <h2 style="margin: 0 0 20px 0; color: #333333; font-size: 24px;">Booking Confirmed! ✓</h2>
                            
                            <p style="margin: 0 0 20px 0; color: #666666; font-size: 16px; line-height: 1.5;">
                                Dear {customer_name},
                            </p>
                            
                            <p style="margin: 0 0 30px 0; color: #666666; font-size: 16px; line-height: 1.5;">
                                Thank you for booking with Galaxium Travels! Your interstellar journey is confirmed.
                            </p>
                            
                            <!-- Booking Details Box -->
                            <div style="background-color: #f8f9fa; border-left: 4px solid #667eea; padding: 20px; margin-bottom: 30px; border-radius: 4px;">
                                <h3 style="margin: 0 0 15px 0; color: #333333; font-size: 18px;">Booking Details</h3>
                                
                                <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                    <tr>
                                        <td style="padding: 8px; border-bottom: 1px solid #e0e0e0;"><strong>Reference:</strong></td>
                                        <td style="padding: 8px; border-bottom: 1px solid #e0e0e0; color: #667eea; font-weight: bold;">{booking_ref}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px; border-bottom: 1px solid #e0e0e0;"><strong>Destination:</strong></td>
                                        <td style="padding: 8px; border-bottom: 1px solid #e0e0e0;">{origin} → {destination}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px; border-bottom: 1px solid #e0e0e0;"><strong>Departure:</strong></td>
                                        <td style="padding: 8px; border-bottom: 1px solid #e0e0e0;">{departure_display}</td>
                                    </tr>
                                    {return_display}
                                    <tr>
                                        <td style="padding: 8px; border-bottom: 1px solid #e0e0e0;"><strong>Class:</strong></td>
                                        <td style="padding: 8px; border-bottom: 1px solid #e0e0e0; text-transform: capitalize;">{seat_class}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px; border-bottom: 1px solid #e0e0e0;"><strong>Passengers:</strong></td>
                                        <td style="padding: 8px; border-bottom: 1px solid #e0e0e0;">{passengers} adult(s)</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px;"><strong>Total Paid:</strong></td>
                                        <td style="padding: 8px; color: #667eea; font-weight: bold; font-size: 18px;">${price_paid:,}</td>
                                    </tr>
                                </table>
                            </div>
                            
                            <!-- Confirmation Code Box -->
                            <div style="background-color: #fff3cd; border: 2px dashed #ffc107; padding: 20px; text-align: center; margin-bottom: 30px; border-radius: 4px;">
                                <p style="margin: 0 0 10px 0; color: #856404; font-size: 14px; font-weight: bold;">YOUR CONFIRMATION CODE</p>
                                <p style="margin: 0; color: #856404; font-size: 32px; font-weight: bold; letter-spacing: 4px; font-family: 'Courier New', monospace;">{confirmation_code}</p>
                                <p style="margin: 10px 0 0 0; color: #856404; font-size: 12px;">Please keep this code for your records</p>
                            </div>
                            
                            <!-- Important Information -->
                            <div style="background-color: #e7f3ff; border-left: 4px solid #2196F3; padding: 15px; margin-bottom: 20px; border-radius: 4px;">
                                <p style="margin: 0; color: #0d47a1; font-size: 14px; line-height: 1.5;">
                                    <strong>📋 Important:</strong> Please arrive at the spaceport at least 2 hours before departure. Bring a valid ID and your confirmation code.
                                </p>
                            </div>
                            
                            <p style="margin: 0 0 10px 0; color: #666666; font-size: 16px; line-height: 1.5;">
                                Safe travels among the stars!
                            </p>
                            
                            <p style="margin: 0; color: #666666; font-size: 16px; line-height: 1.5;">
                                <strong>The Galaxium Travels Team</strong>
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8f9fa; padding: 20px 30px; text-align: center; border-radius: 0 0 8px 8px;">
                            <p style="margin: 0 0 10px 0; color: #999999; font-size: 12px;">
                                This is an automated confirmation email. Please do not reply to this message.
                            </p>
                            <p style="margin: 0; color: #999999; font-size: 12px;">
                                © {datetime.now().year} Galaxium Travels. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    
    return subject, html_body


def send_booking_confirmation_email(
    customer_name: str,
    customer_email: str,
    booking_id: int,
    origin: str,
    destination: str,
    departure_time: str,
    return_time: Optional[str],
    seat_class: str,
    price_paid: int,
    passengers: int = 1
) -> bool:
    """
    Send booking confirmation email to customer.
    
    Returns:
        True if email sent successfully, False otherwise
    """
    # Get SMTP configuration from environment variables
    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_username = os.getenv('SMTP_USERNAME', '')
    smtp_password = os.getenv('SMTP_PASSWORD', '')
    smtp_from_email = os.getenv('SMTP_FROM_EMAIL', smtp_username)
    smtp_from_name = os.getenv('SMTP_FROM_NAME', 'Galaxium Travels')
    
    # Check if SMTP is configured
    if not smtp_username or not smtp_password:
        logger.warning(
            f"SMTP not configured. Email would be sent to {customer_email} for booking {booking_id}. "
            "Set SMTP_USERNAME and SMTP_PASSWORD environment variables to enable email sending."
        )
        # In development/demo mode, log the email content instead of failing
        subject, html_body = create_booking_confirmation_email(
            customer_name, customer_email, booking_id, origin, destination,
            departure_time, return_time, seat_class, price_paid, passengers
        )
        logger.info(f"[DEMO MODE] Email Subject: {subject}")
        logger.info(f"[DEMO MODE] Email would be sent to: {customer_email}")
        return True  # Return success in demo mode
    
    try:
        # Create email message
        subject, html_body = create_booking_confirmation_email(
            customer_name, customer_email, booking_id, origin, destination,
            departure_time, return_time, seat_class, price_paid, passengers
        )
        
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = f"{smtp_from_name} <{smtp_from_email}>"
        message['To'] = customer_email
        
        # Attach HTML content
        html_part = MIMEText(html_body, 'html')
        message.attach(html_part)
        
        # Send email via SMTP
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)
        
        logger.info(f"Booking confirmation email sent successfully to {customer_email} for booking {booking_id}")
        return True
        
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending booking confirmation email to {customer_email}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending booking confirmation email to {customer_email}: {e}")
        return False
