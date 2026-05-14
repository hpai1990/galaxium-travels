import pytest
from unittest.mock import Mock, patch, MagicMock
import smtplib
from services.email import (
    generate_confirmation_code,
    format_booking_reference,
    create_booking_email_html,
    create_booking_email_text,
    send_booking_confirmation_email
)


class TestConfirmationCode:
    """Tests for confirmation code generation."""
    
    def test_generate_confirmation_code_format(self):
        """Test that confirmation code has correct format (9 characters)."""
        code = generate_confirmation_code()
        assert len(code) == 9
        assert code[:3].isalpha()
        assert code[3:6].isdigit()
        assert code[6:].isalpha()
    
    def test_generate_confirmation_code_uppercase(self):
        """Test that letters in confirmation code are uppercase."""
        code = generate_confirmation_code()
        assert code[:3].isupper()
        assert code[6:].isupper()
    
    def test_generate_confirmation_code_uniqueness(self):
        """Test that generated codes are unique."""
        codes = [generate_confirmation_code() for _ in range(100)]
        assert len(set(codes)) == 100  # All codes should be unique


class TestBookingReference:
    """Tests for booking reference formatting."""
    
    def test_format_booking_reference_standard(self):
        """Test standard booking reference format."""
        ref = format_booking_reference(12345, "2026-05-14T10:30:00")
        assert ref == "GT-2026-12345"
    
    def test_format_booking_reference_padding(self):
        """Test that booking ID is padded to 5 digits."""
        ref = format_booking_reference(1, "2026-05-14T10:30:00")
        assert ref == "GT-2026-00001"
        
        ref = format_booking_reference(999, "2026-05-14T10:30:00")
        assert ref == "GT-2026-00999"
    
    def test_format_booking_reference_large_id(self):
        """Test booking reference with large ID."""
        ref = format_booking_reference(123456, "2026-05-14T10:30:00")
        assert ref == "GT-2026-123456"
    
    def test_format_booking_reference_different_years(self):
        """Test booking reference with different years."""
        ref_2025 = format_booking_reference(100, "2025-12-31T23:59:59")
        assert ref_2025 == "GT-2025-00100"
        
        ref_2027 = format_booking_reference(100, "2027-01-01T00:00:00")
        assert ref_2027 == "GT-2027-00100"


class TestEmailContent:
    """Tests for email content generation."""
    
    def test_create_booking_email_html_contains_required_info(self):
        """Test that HTML email contains all required information."""
        html = create_booking_email_html(
            customer_name="John Doe",
            booking_reference="GT-2026-12345",
            confirmation_code="ABC123XYZ",
            destination="Mars Colony Alpha",
            origin="Earth Station",
            departure_time="2026-06-15 09:00",
            arrival_time="2026-06-15 17:00",
            seat_class="business",
            price_paid=2500000
        )
        
        assert "John Doe" in html
        assert "GT-2026-12345" in html
        assert "ABC123XYZ" in html
        assert "Mars Colony Alpha" in html
        assert "Earth Station" in html
        assert "2026-06-15 09:00" in html
        assert "2026-06-15 17:00" in html
        assert "Business" in html
        assert "$2,500,000" in html
    
    def test_create_booking_email_html_is_valid_html(self):
        """Test that generated HTML is valid."""
        html = create_booking_email_html(
            customer_name="Test User",
            booking_reference="GT-2026-00001",
            confirmation_code="XYZ789ABC",
            destination="Moon Base",
            origin="Earth",
            departure_time="2026-07-01 10:00",
            arrival_time="2026-07-01 12:00",
            seat_class="economy",
            price_paid=500000
        )
        
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html
        assert "<head>" in html
        assert "<body>" in html
    
    def test_create_booking_email_html_mobile_responsive(self):
        """Test that HTML includes mobile-responsive styles."""
        html = create_booking_email_html(
            customer_name="Test",
            booking_reference="GT-2026-00001",
            confirmation_code="ABC123XYZ",
            destination="Mars",
            origin="Earth",
            departure_time="2026-06-15 09:00",
            arrival_time="2026-06-15 17:00",
            seat_class="economy",
            price_paid=1000000
        )
        
        assert "@media only screen and (max-width: 600px)" in html
    
    def test_create_booking_email_text_contains_required_info(self):
        """Test that plain text email contains all required information."""
        text = create_booking_email_text(
            customer_name="Jane Smith",
            booking_reference="GT-2026-54321",
            confirmation_code="DEF456GHI",
            destination="Venus Station",
            origin="Earth Hub",
            departure_time="2026-08-20 14:00",
            arrival_time="2026-08-20 20:00",
            seat_class="galaxium",
            price_paid=5000000
        )
        
        assert "Jane Smith" in text
        assert "GT-2026-54321" in text
        assert "DEF456GHI" in text
        assert "Venus Station" in text
        assert "Earth Hub" in text
        assert "2026-08-20 14:00" in text
        assert "2026-08-20 20:00" in text
        assert "Galaxium" in text
        assert "$5,000,000" in text
    
    def test_seat_class_capitalization(self):
        """Test that seat class is properly capitalized in emails."""
        html = create_booking_email_html(
            customer_name="Test",
            booking_reference="GT-2026-00001",
            confirmation_code="ABC123XYZ",
            destination="Mars",
            origin="Earth",
            departure_time="2026-06-15 09:00",
            arrival_time="2026-06-15 17:00",
            seat_class="economy",
            price_paid=1000000
        )
        assert "Economy" in html
        
        text = create_booking_email_text(
            customer_name="Test",
            booking_reference="GT-2026-00001",
            confirmation_code="ABC123XYZ",
            destination="Mars",
            origin="Earth",
            departure_time="2026-06-15 09:00",
            arrival_time="2026-06-15 17:00",
            seat_class="business",
            price_paid=2500000
        )
        assert "Business" in text


class TestSendBookingConfirmationEmail:
    """Tests for sending booking confirmation emails."""
    
    @patch.dict('os.environ', {
        'SMTP_HOST': 'smtp.test.com',
        'SMTP_PORT': '587',
        'SMTP_USERNAME': '',
        'SMTP_PASSWORD': '',
        'SMTP_FROM_EMAIL': 'test@example.com',
        'SMTP_FROM_NAME': 'Test Sender'
    })
    def test_send_email_demo_mode_no_credentials(self):
        """Test that email works in demo mode when credentials are not set."""
        success, error_msg, confirmation_code = send_booking_confirmation_email(
            to_email="customer@example.com",
            customer_name="Test Customer",
            booking_id=1,
            booking_time="2026-05-14T10:30:00",
            destination="Mars",
            origin="Earth",
            departure_time="2026-06-15 09:00",
            arrival_time="2026-06-15 17:00",
            seat_class="economy",
            price_paid=1000000
        )
        
        assert success is True
        assert error_msg is None
        assert len(confirmation_code) == 9
    
    @patch('smtplib.SMTP')
    @patch.dict('os.environ', {
        'SMTP_HOST': 'smtp.test.com',
        'SMTP_PORT': '587',
        'SMTP_USERNAME': 'test@example.com',
        'SMTP_PASSWORD': 'test_password',
        'SMTP_FROM_EMAIL': 'noreply@test.com',
        'SMTP_FROM_NAME': 'Test Sender'
    })
    def test_send_email_success(self, mock_smtp):
        """Test successful email sending."""
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        success, error_msg, confirmation_code = send_booking_confirmation_email(
            to_email="customer@example.com",
            customer_name="Test Customer",
            booking_id=123,
            booking_time="2026-05-14T10:30:00",
            destination="Mars Colony",
            origin="Earth Station",
            departure_time="2026-06-15 09:00",
            arrival_time="2026-06-15 17:00",
            seat_class="business",
            price_paid=2500000
        )
        
        assert success is True
        assert error_msg is None
        assert len(confirmation_code) == 9
        
        # Verify SMTP methods were called
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with('test@example.com', 'test_password')
        mock_server.send_message.assert_called_once()
    
    @patch('smtplib.SMTP')
    @patch.dict('os.environ', {
        'SMTP_HOST': 'smtp.test.com',
        'SMTP_PORT': '587',
        'SMTP_USERNAME': 'test@example.com',
        'SMTP_PASSWORD': 'wrong_password',
        'SMTP_FROM_EMAIL': 'noreply@test.com',
        'SMTP_FROM_NAME': 'Test Sender'
    })
    def test_send_email_authentication_failure(self, mock_smtp):
        """Test email sending with authentication failure."""
        # Mock SMTP authentication error
        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b'Authentication failed')
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        success, error_msg, confirmation_code = send_booking_confirmation_email(
            to_email="customer@example.com",
            customer_name="Test Customer",
            booking_id=456,
            booking_time="2026-05-14T10:30:00",
            destination="Mars",
            origin="Earth",
            departure_time="2026-06-15 09:00",
            arrival_time="2026-06-15 17:00",
            seat_class="economy",
            price_paid=1000000
        )
        
        assert success is False
        assert "SMTP authentication failed" in error_msg
        assert len(confirmation_code) == 9  # Code is still generated
    
    @patch('smtplib.SMTP')
    @patch.dict('os.environ', {
        'SMTP_HOST': 'smtp.test.com',
        'SMTP_PORT': '587',
        'SMTP_USERNAME': 'test@example.com',
        'SMTP_PASSWORD': 'test_password',
        'SMTP_FROM_EMAIL': 'noreply@test.com',
        'SMTP_FROM_NAME': 'Test Sender'
    })
    def test_send_email_smtp_exception(self, mock_smtp):
        """Test email sending with SMTP exception."""
        # Mock SMTP exception
        mock_server = MagicMock()
        mock_server.send_message.side_effect = smtplib.SMTPException("Connection failed")
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        success, error_msg, confirmation_code = send_booking_confirmation_email(
            to_email="customer@example.com",
            customer_name="Test Customer",
            booking_id=789,
            booking_time="2026-05-14T10:30:00",
            destination="Mars",
            origin="Earth",
            departure_time="2026-06-15 09:00",
            arrival_time="2026-06-15 17:00",
            seat_class="economy",
            price_paid=1000000
        )
        
        assert success is False
        assert "SMTP error" in error_msg
        assert len(confirmation_code) == 9
    
    @patch('smtplib.SMTP')
    @patch.dict('os.environ', {
        'SMTP_HOST': 'smtp.test.com',
        'SMTP_PORT': '587',
        'SMTP_USERNAME': 'test@example.com',
        'SMTP_PASSWORD': 'test_password',
        'SMTP_FROM_EMAIL': 'noreply@test.com',
        'SMTP_FROM_NAME': 'Test Sender'
    })
    def test_email_message_structure(self, mock_smtp):
        """Test that email message has correct structure."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        send_booking_confirmation_email(
            to_email="customer@example.com",
            customer_name="Test Customer",
            booking_id=100,
            booking_time="2026-05-14T10:30:00",
            destination="Mars",
            origin="Earth",
            departure_time="2026-06-15 09:00",
            arrival_time="2026-06-15 17:00",
            seat_class="economy",
            price_paid=1000000
        )
        
        # Get the message that was sent
        call_args = mock_server.send_message.call_args
        msg = call_args[0][0]
        
        # Verify message structure
        assert msg['To'] == 'customer@example.com'
        assert 'Test Sender' in msg['From']
        assert 'Booking Confirmation' in msg['Subject']
        assert 'GT-2026-00100' in msg['Subject']
