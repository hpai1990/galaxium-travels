import pytest
from unittest.mock import Mock, patch, MagicMock
from services.email import EmailService, get_email_service
import os


@pytest.fixture
def email_service():
    """Create an email service instance with test configuration."""
    with patch.dict(os.environ, {
        'EMAIL_ENABLED': 'true',
        'SMTP_HOST': 'smtp.test.com',
        'SMTP_PORT': '587',
        'SMTP_USER': 'test@test.com',
        'SMTP_PASSWORD': 'test_password',
        'FROM_EMAIL': 'noreply@galaxiumtravels.com',
        'FROM_NAME': 'Galaxium Travels'
    }):
        service = EmailService()
        yield service


@pytest.fixture
def email_service_disabled():
    """Create an email service instance with email disabled."""
    with patch.dict(os.environ, {
        'EMAIL_ENABLED': 'false',
        'SMTP_HOST': 'smtp.test.com',
        'SMTP_PORT': '587',
        'SMTP_USER': 'test@test.com',
        'SMTP_PASSWORD': 'test_password'
    }):
        service = EmailService()
        yield service


class TestEmailService:
    """Test suite for EmailService."""
    
    def test_email_service_initialization(self, email_service):
        """Test that email service initializes with correct configuration."""
        assert email_service.smtp_host == 'smtp.test.com'
        assert email_service.smtp_port == 587
        assert email_service.smtp_user == 'test@test.com'
        assert email_service.smtp_password == 'test_password'
        assert email_service.from_email == 'noreply@galaxiumtravels.com'
        assert email_service.from_name == 'Galaxium Travels'
        assert email_service.enabled is True
    
    def test_email_service_disabled(self, email_service_disabled):
        """Test that email service respects disabled flag."""
        assert email_service_disabled.enabled is False
    
    def test_generate_confirmation_code(self, email_service):
        """Test confirmation code generation."""
        code1 = email_service._generate_confirmation_code()
        code2 = email_service._generate_confirmation_code()
        
        # Codes should be 12 characters (6 bytes hex = 12 chars)
        assert len(code1) == 12
        assert len(code2) == 12
        
        # Codes should be uppercase
        assert code1.isupper()
        assert code2.isupper()
        
        # Codes should be unique
        assert code1 != code2
    
    def test_create_booking_confirmation_html(self, email_service):
        """Test HTML email template creation."""
        html = email_service._create_booking_confirmation_html(
            customer_name="John Doe",
            booking_reference="GT-2026-12345",
            confirmation_code="ABC123XYZ",
            destination="Mars Colony Alpha",
            departure_date="2026-06-15",
            return_date="2026-06-22",
            passengers=2,
            seat_class="economy",
            price_paid=5000
        )
        
        # Check that key information is in the HTML
        assert "John Doe" in html
        assert "GT-2026-12345" in html
        assert "ABC123XYZ" in html
        assert "Mars Colony Alpha" in html
        assert "2026-06-15" in html
        assert "2026-06-22" in html
        assert "Economy" in html
        assert "$5,000" in html
        
        # Check for responsive design meta tag
        assert 'viewport' in html
        assert 'max-width: 600px' in html
    
    def test_create_booking_confirmation_text(self, email_service):
        """Test plain text email template creation."""
        text = email_service._create_booking_confirmation_text(
            customer_name="John Doe",
            booking_reference="GT-2026-12345",
            confirmation_code="ABC123XYZ",
            destination="Mars Colony Alpha",
            departure_date="2026-06-15",
            return_date="2026-06-22",
            passengers=2,
            seat_class="business",
            price_paid=12500
        )
        
        # Check that key information is in the text
        assert "John Doe" in text
        assert "GT-2026-12345" in text
        assert "ABC123XYZ" in text
        assert "Mars Colony Alpha" in text
        assert "2026-06-15" in text
        assert "2026-06-22" in text
        assert "Business" in text
        assert "$12,500" in text
    
    @patch('services.email.smtplib.SMTP')
    def test_send_booking_confirmation_success(self, mock_smtp, email_service):
        """Test successful email sending."""
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = email_service.send_booking_confirmation(
            to_email="customer@example.com",
            customer_name="Jane Smith",
            booking_reference="GT-2026-67890",
            destination="Europa Station",
            departure_date="2026-07-01",
            return_date="2026-07-08",
            passengers=1,
            seat_class="galaxium",
            price_paid=25000
        )
        
        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with('test@test.com', 'test_password')
        mock_server.send_message.assert_called_once()
    
    @patch('services.email.smtplib.SMTP')
    def test_send_booking_confirmation_smtp_failure(self, mock_smtp, email_service):
        """Test email sending with SMTP failure and retry."""
        # Mock SMTP server to raise exception
        mock_server = MagicMock()
        mock_server.send_message.side_effect = Exception("SMTP error")
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = email_service.send_booking_confirmation(
            to_email="customer@example.com",
            customer_name="Jane Smith",
            booking_reference="GT-2026-67890",
            destination="Europa Station",
            departure_date="2026-07-01",
            return_date="2026-07-08"
        )
        
        assert result is False
        # Should retry 3 times
        assert mock_server.send_message.call_count == 3
    
    def test_send_booking_confirmation_disabled(self, email_service_disabled):
        """Test that email sending is skipped when disabled."""
        result = email_service_disabled.send_booking_confirmation(
            to_email="customer@example.com",
            customer_name="Jane Smith",
            booking_reference="GT-2026-67890",
            destination="Europa Station",
            departure_date="2026-07-01",
            return_date="2026-07-08"
        )
        
        # Should return True (success) but not actually send
        assert result is True
    
    def test_send_booking_confirmation_no_credentials(self):
        """Test email sending fails gracefully without credentials."""
        with patch.dict(os.environ, {
            'EMAIL_ENABLED': 'true',
            'SMTP_HOST': 'smtp.test.com',
            'SMTP_PORT': '587',
            'SMTP_USER': '',
            'SMTP_PASSWORD': ''
        }):
            service = EmailService()
            result = service.send_booking_confirmation(
                to_email="customer@example.com",
                customer_name="Jane Smith",
                booking_reference="GT-2026-67890",
                destination="Europa Station",
                departure_date="2026-07-01",
                return_date="2026-07-08"
            )
            
            assert result is False
    
    def test_get_email_service_singleton(self):
        """Test that get_email_service returns a singleton instance."""
        service1 = get_email_service()
        service2 = get_email_service()
        
        assert service1 is service2