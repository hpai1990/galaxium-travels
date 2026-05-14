import pytest
from unittest.mock import Mock, patch, MagicMock
from services.email import EmailService, get_email_service
import smtplib


class TestEmailService:
    """Tests for the EmailService class."""
    
    def test_email_service_initialization_disabled(self, monkeypatch):
        """Test email service initializes correctly when disabled."""
        monkeypatch.setenv('EMAIL_ENABLED', 'false')
        service = EmailService()
        
        assert service.enabled is False
        assert service.smtp_host == 'smtp.gmail.com'
        assert service.smtp_port == 587
    
    def test_email_service_initialization_enabled(self, monkeypatch):
        """Test email service initializes correctly when enabled."""
        monkeypatch.setenv('EMAIL_ENABLED', 'true')
        monkeypatch.setenv('SMTP_HOST', 'smtp.example.com')
        monkeypatch.setenv('SMTP_PORT', '465')
        monkeypatch.setenv('SMTP_USER', 'test@example.com')
        monkeypatch.setenv('SMTP_PASSWORD', 'password123')
        
        service = EmailService()
        
        assert service.enabled is True
        assert service.smtp_host == 'smtp.example.com'
        assert service.smtp_port == 465
        assert service.smtp_user == 'test@example.com'
        assert service.smtp_password == 'password123'
    
    def test_generate_confirmation_code(self):
        """Test confirmation code generation."""
        service = EmailService()
        code = service.generate_confirmation_code()
        
        # Should be 12 characters (6 bytes hex = 12 chars)
        assert len(code) == 12
        # Should be uppercase
        assert code.isupper()
        # Should be alphanumeric
        assert code.isalnum()
    
    def test_generate_confirmation_code_uniqueness(self):
        """Test that confirmation codes are unique."""
        service = EmailService()
        codes = [service.generate_confirmation_code() for _ in range(100)]
        
        # All codes should be unique
        assert len(codes) == len(set(codes))
    
    def test_create_booking_confirmation_email(self):
        """Test booking confirmation email creation."""
        service = EmailService()
        
        subject, html_body = service.create_booking_confirmation_email(
            customer_name="John Doe",
            customer_email="john@example.com",
            booking_reference="GT-2026-00001",
            confirmation_code="ABC123DEF456",
            flight_origin="Earth",
            flight_destination="Mars",
            departure_date="2026-06-15T10:00:00Z",
            return_date="2026-06-22T15:00:00Z",
            seat_class="business",
            price_paid=5000,
            passengers=2
        )
        
        # Check subject
        assert "GT-2026-00001" in subject
        assert "Booking Confirmation" in subject
        
        # Check HTML body contains key information
        assert "John Doe" in html_body
        assert "GT-2026-00001" in html_body
        assert "ABC123DEF456" in html_body
        assert "Earth" in html_body
        assert "Mars" in html_body
        assert "BUSINESS" in html_body
        assert "$5,000" in html_body
        assert "2" in html_body  # passengers
        
        # Check HTML structure
        assert "<!DOCTYPE html>" in html_body
        assert "<html" in html_body
        assert "</html>" in html_body
        assert "Galaxium Travels" in html_body
    
    def test_create_booking_confirmation_email_one_way(self):
        """Test booking confirmation email for one-way trip."""
        service = EmailService()
        
        subject, html_body = service.create_booking_confirmation_email(
            customer_name="Jane Smith",
            customer_email="jane@example.com",
            booking_reference="GT-2026-00002",
            confirmation_code="XYZ789ABC123",
            flight_origin="Mars",
            flight_destination="Jupiter",
            departure_date="2026-07-01T08:00:00Z",
            return_date=None,
            seat_class="economy",
            price_paid=2000,
            passengers=1
        )
        
        # Check for one-way indicator
        assert "One-way trip" in html_body
        assert "Jane Smith" in html_body
        assert "ECONOMY" in html_body
    
    @patch('smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        """Test successful email sending."""
        # Setup mock
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        service = EmailService()
        service.enabled = True
        service.smtp_user = "test@example.com"
        service.smtp_password = "password"
        
        # Send email
        result = service.send_email(
            to_email="recipient@example.com",
            subject="Test Subject",
            html_body="<html><body>Test</body></html>"
        )
        
        # Verify
        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@example.com", "password")
        mock_server.send_message.assert_called_once()
    
    def test_send_email_disabled(self):
        """Test email sending when service is disabled."""
        service = EmailService()
        service.enabled = False
        
        result = service.send_email(
            to_email="recipient@example.com",
            subject="Test Subject",
            html_body="<html><body>Test</body></html>"
        )
        
        # Should return True but not actually send
        assert result is True
    
    def test_send_email_no_credentials(self):
        """Test email sending fails without credentials."""
        service = EmailService()
        service.enabled = True
        service.smtp_user = ""
        service.smtp_password = ""
        
        result = service.send_email(
            to_email="recipient@example.com",
            subject="Test Subject",
            html_body="<html><body>Test</body></html>"
        )
        
        assert result is False
    
    @patch('smtplib.SMTP')
    def test_send_email_smtp_error_with_retry(self, mock_smtp):
        """Test email sending retries on SMTP error."""
        # Setup mock to fail twice then succeed
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        mock_server.send_message.side_effect = [
            smtplib.SMTPException("Temporary error"),
            smtplib.SMTPException("Temporary error"),
            None  # Success on third attempt
        ]
        
        service = EmailService()
        service.enabled = True
        service.smtp_user = "test@example.com"
        service.smtp_password = "password"
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = service.send_email(
                to_email="recipient@example.com",
                subject="Test Subject",
                html_body="<html><body>Test</body></html>",
                max_retries=3
            )
        
        assert result is True
        assert mock_server.send_message.call_count == 3
    
    @patch('smtplib.SMTP')
    def test_send_email_fails_after_max_retries(self, mock_smtp):
        """Test email sending fails after max retries."""
        # Setup mock to always fail
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        mock_server.send_message.side_effect = smtplib.SMTPException("Permanent error")
        
        service = EmailService()
        service.enabled = True
        service.smtp_user = "test@example.com"
        service.smtp_password = "password"
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = service.send_email(
                to_email="recipient@example.com",
                subject="Test Subject",
                html_body="<html><body>Test</body></html>",
                max_retries=3
            )
        
        assert result is False
        assert mock_server.send_message.call_count == 3
    
    @patch('services.email.EmailService.send_email')
    def test_send_booking_confirmation(self, mock_send_email):
        """Test complete booking confirmation flow."""
        mock_send_email.return_value = True
        
        service = EmailService()
        success, confirmation_code = service.send_booking_confirmation(
            customer_name="Alice Johnson",
            customer_email="alice@example.com",
            booking_reference="GT-2026-00003",
            flight_origin="Earth",
            flight_destination="Venus",
            departure_date="2026-08-01T12:00:00Z",
            return_date="2026-08-08T14:00:00Z",
            seat_class="galaxium",
            price_paid=10000,
            passengers=1
        )
        
        # Verify success
        assert success is True
        assert len(confirmation_code) == 12
        
        # Verify send_email was called
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args
        assert call_args[1]['to_email'] == "alice@example.com"
        assert "GT-2026-00003" in call_args[1]['subject']
    
    def test_get_email_service_singleton(self):
        """Test that get_email_service returns singleton instance."""
        service1 = get_email_service()
        service2 = get_email_service()
        
        assert service1 is service2
    
    def test_email_html_is_mobile_responsive(self):
        """Test that email HTML includes mobile-responsive CSS."""
        service = EmailService()
        
        _, html_body = service.create_booking_confirmation_email(
            customer_name="Test User",
            customer_email="test@example.com",
            booking_reference="GT-2026-00001",
            confirmation_code="TEST123456",
            flight_origin="Earth",
            flight_destination="Mars",
            departure_date="2026-06-15T10:00:00Z",
            return_date=None,
            seat_class="economy",
            price_paid=1000,
            passengers=1
        )
        
        # Check for viewport meta tag
        assert 'name="viewport"' in html_body
        assert 'width=device-width' in html_body
        
        # Check for media query
        assert '@media only screen and (max-width: 600px)' in html_body
