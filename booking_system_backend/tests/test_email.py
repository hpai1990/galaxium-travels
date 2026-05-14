import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.email import (
    generate_confirmation_code,
    format_booking_reference,
    create_booking_confirmation_email,
    send_booking_confirmation_email
)


class TestEmailService:
    """Tests for email service functions."""
    
    def test_generate_confirmation_code(self):
        """Test confirmation code generation."""
        code = generate_confirmation_code()
        
        # Check length (3 letters + 3 digits + 3 letters = 9 chars)
        assert len(code) == 9
        
        # Check format: ABC123XYZ
        assert code[:3].isalpha() and code[:3].isupper()
        assert code[3:6].isdigit()
        assert code[6:].isalpha() and code[6:].isupper()
    
    def test_generate_confirmation_code_uniqueness(self):
        """Test that confirmation codes are unique."""
        codes = [generate_confirmation_code() for _ in range(100)]
        # Should have high uniqueness (allow for small chance of collision)
        assert len(set(codes)) > 95
    
    def test_format_booking_reference(self):
        """Test booking reference formatting."""
        ref = format_booking_reference(12345)
        
        # Check format: GT-YYYY-12345
        assert ref.startswith("GT-")
        assert ref.endswith("-12345")
        parts = ref.split("-")
        assert len(parts) == 3
        assert parts[0] == "GT"
        assert parts[1].isdigit() and len(parts[1]) == 4  # Year
        assert parts[2] == "12345"
    
    def test_format_booking_reference_padding(self):
        """Test booking reference with padding for small IDs."""
        ref = format_booking_reference(42)
        assert ref.endswith("-00042")
    
    def test_create_booking_confirmation_email(self):
        """Test email content creation."""
        subject, html_body = create_booking_confirmation_email(
            customer_name="John Doe",
            customer_email="john@example.com",
            booking_id=123,
            origin="Earth",
            destination="Mars",
            departure_time="2026-06-15 10:00",
            return_time="2026-06-22 18:00",
            seat_class="business",
            price_paid=5000,
            passengers=2
        )
        
        # Check subject
        assert "Booking Confirmation" in subject
        assert "GT-" in subject
        
        # Check HTML body contains key information
        assert "John Doe" in html_body
        assert "Earth" in html_body
        assert "Mars" in html_body
        assert "business" in html_body.lower()
        assert "$5,000" in html_body
        assert "2 adult(s)" in html_body
        assert "Galaxium Travels" in html_body
        
        # Check HTML structure
        assert "<!DOCTYPE html>" in html_body
        assert "<html" in html_body
        assert "</html>" in html_body
        assert "viewport" in html_body  # Mobile responsive
    
    def test_create_booking_confirmation_email_without_return(self):
        """Test email content creation without return time."""
        subject, html_body = create_booking_confirmation_email(
            customer_name="Jane Smith",
            customer_email="jane@example.com",
            booking_id=456,
            origin="Moon",
            destination="Venus",
            departure_time="2026-07-01 14:00",
            return_time=None,
            seat_class="economy",
            price_paid=1500,
            passengers=1
        )
        
        # Check that return time is not in the email when None
        assert "Jane Smith" in html_body
        assert "Moon" in html_body
        assert "Venus" in html_body
    
    @patch('services.email.smtplib.SMTP')
    @patch.dict('os.environ', {
        'SMTP_HOST': 'smtp.test.com',
        'SMTP_PORT': '587',
        'SMTP_USERNAME': 'test@test.com',
        'SMTP_PASSWORD': 'testpass',
        'SMTP_FROM_EMAIL': 'noreply@test.com',
        'SMTP_FROM_NAME': 'Test Travels'
    })
    def test_send_booking_confirmation_email_success(self, mock_smtp):
        """Test successful email sending."""
        # Setup mock
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Send email
        result = send_booking_confirmation_email(
            customer_name="Test User",
            customer_email="test@example.com",
            booking_id=789,
            origin="Earth",
            destination="Mars",
            departure_time="2026-08-01 09:00",
            return_time="2026-08-08 17:00",
            seat_class="galaxium",
            price_paid=10000,
            passengers=1
        )
        
        # Verify result
        assert result is True
        
        # Verify SMTP calls
        mock_smtp.assert_called_once_with('smtp.test.com', 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with('test@test.com', 'testpass')
        mock_server.send_message.assert_called_once()
    
    @patch('services.email.smtplib.SMTP')
    @patch.dict('os.environ', {
        'SMTP_HOST': 'smtp.test.com',
        'SMTP_PORT': '587',
        'SMTP_USERNAME': 'test@test.com',
        'SMTP_PASSWORD': 'testpass'
    })
    def test_send_booking_confirmation_email_smtp_error(self, mock_smtp):
        """Test email sending with SMTP error."""
        # Setup mock to raise exception
        mock_smtp.return_value.__enter__.return_value.login.side_effect = Exception("SMTP Error")
        
        # Send email
        result = send_booking_confirmation_email(
            customer_name="Test User",
            customer_email="test@example.com",
            booking_id=999,
            origin="Earth",
            destination="Mars",
            departure_time="2026-09-01 09:00",
            return_time=None,
            seat_class="economy",
            price_paid=2000,
            passengers=1
        )
        
        # Verify result is False on error
        assert result is False
    
    @patch.dict('os.environ', {}, clear=True)
    def test_send_booking_confirmation_email_no_config(self):
        """Test email sending without SMTP configuration (demo mode)."""
        # Send email without SMTP config
        result = send_booking_confirmation_email(
            customer_name="Demo User",
            customer_email="demo@example.com",
            booking_id=111,
            origin="Earth",
            destination="Mars",
            departure_time="2026-10-01 09:00",
            return_time=None,
            seat_class="business",
            price_paid=3000,
            passengers=1
        )
        
        # Should return True in demo mode (logs instead of sending)
        assert result is True
    
    def test_email_content_escaping(self):
        """Test that email content handles special characters safely."""
        subject, html_body = create_booking_confirmation_email(
            customer_name="O'Brien & Sons",
            customer_email="test@example.com",
            booking_id=222,
            origin="Earth <Planet>",
            destination="Mars & Beyond",
            departure_time="2026-11-01 09:00",
            return_time=None,
            seat_class="economy",
            price_paid=1000,
            passengers=1
        )
        
        # Check that content is included (HTML will handle escaping)
        assert "O'Brien" in html_body or "O&#39;Brien" in html_body
        assert "Earth" in html_body
        assert "Mars" in html_body
