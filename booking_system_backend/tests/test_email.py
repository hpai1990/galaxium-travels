import pytest
from unittest.mock import Mock, patch, MagicMock
from services.email import (
    generate_confirmation_code,
    format_booking_reference,
    create_email_template,
    send_booking_confirmation_email
)
from models import User, Flight, Booking


class TestConfirmationCode:
    """Tests for confirmation code generation."""
    
    def test_generate_confirmation_code_format(self):
        """Test that confirmation code has correct format (3 letters, 3 digits, 3 letters)."""
        code = generate_confirmation_code()
        assert len(code) == 9
        assert code[:3].isalpha() and code[:3].isupper()
        assert code[3:6].isdigit()
        assert code[6:].isalpha() and code[6:].isupper()
    
    def test_generate_confirmation_code_uniqueness(self):
        """Test that generated codes are unique."""
        codes = [generate_confirmation_code() for _ in range(100)]
        assert len(codes) == len(set(codes))  # All codes should be unique


class TestBookingReference:
    """Tests for booking reference formatting."""
    
    def test_format_booking_reference(self):
        """Test booking reference format."""
        assert format_booking_reference(1) == "GT-2026-00001"
        assert format_booking_reference(123) == "GT-2026-00123"
        assert format_booking_reference(99999) == "GT-2026-99999"
    
    def test_format_booking_reference_padding(self):
        """Test that booking reference is zero-padded to 5 digits."""
        ref = format_booking_reference(42)
        assert ref == "GT-2026-00042"
        assert len(ref.split('-')[-1]) == 5


class TestEmailTemplate:
    """Tests for email template creation."""
    
    def test_create_email_template_contains_required_fields(self):
        """Test that email template contains all required information."""
        html = create_email_template(
            customer_name="John Doe",
            booking_reference="GT-2026-00001",
            confirmation_code="ABC123XYZ",
            destination="Mars Colony Alpha",
            origin="Earth Station",
            departure_time="2026-06-15 10:00",
            arrival_time="2026-06-15 18:00",
            seat_class="business",
            price_paid=5000
        )
        
        assert "John Doe" in html
        assert "GT-2026-00001" in html
        assert "ABC123XYZ" in html
        assert "Mars Colony Alpha" in html
        assert "Earth Station" in html
        assert "business" in html.lower()
        assert "$5,000" in html
    
    def test_create_email_template_is_html(self):
        """Test that template is valid HTML."""
        html = create_email_template(
            customer_name="Test User",
            booking_reference="GT-2026-00001",
            confirmation_code="ABC123XYZ",
            destination="Mars",
            origin="Earth",
            departure_time="2026-06-15 10:00",
            arrival_time="2026-06-15 18:00",
            seat_class="economy",
            price_paid=1000
        )
        
        assert "<!DOCTYPE html>" in html
        assert "<html>" in html
        assert "</html>" in html
        assert "<body>" in html
        assert "</body>" in html
    
    def test_create_email_template_mobile_responsive(self):
        """Test that template includes mobile-responsive meta tag."""
        html = create_email_template(
            customer_name="Test",
            booking_reference="GT-2026-00001",
            confirmation_code="ABC123XYZ",
            destination="Mars",
            origin="Earth",
            departure_time="2026-06-15 10:00",
            arrival_time="2026-06-15 18:00",
            seat_class="economy",
            price_paid=1000
        )
        
        assert 'name="viewport"' in html
        assert "max-width: 600px" in html  # Mobile-friendly width


class TestSendBookingConfirmationEmail:
    """Tests for sending booking confirmation emails."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session with test data."""
        session = Mock()
        
        # Mock user
        user = User(user_id=1, name="John Doe", email="john@example.com")
        
        # Mock flight
        flight = Flight(
            flight_id=1,
            origin="Earth Station",
            destination="Mars Colony Alpha",
            departure_time="2026-06-15 10:00:00",
            arrival_time="2026-06-15 18:00:00",
            base_price=1000,
            economy_seats_available=50,
            business_seats_available=20,
            galaxium_seats_available=5
        )
        
        # Mock booking
        booking = Booking(
            booking_id=1,
            user_id=1,
            flight_id=1,
            status="booked",
            booking_time="2026-05-14T08:00:00",
            seat_class="business",
            price_paid=2500
        )
        
        # Configure query mocks
        session.query.return_value.filter.return_value.first.side_effect = [
            booking,  # First call returns booking
            flight,   # Second call returns flight
            user      # Third call returns user
        ]
        
        return session
    
    def test_send_email_disabled_mode(self, mock_db_session):
        """Test email sending in disabled mode (demo mode)."""
        with patch.dict('os.environ', {'EMAIL_ENABLED': 'false'}):
            result = send_booking_confirmation_email(mock_db_session, 1)
            
            assert result['success'] is True
            assert 'demo mode' in result['message'].lower()
            assert 'confirmation_code' in result
            assert 'booking_reference' in result
            assert result['booking_reference'] == "GT-2026-00001"
            assert result['recipient'] == "john@example.com"
    
    def test_send_email_booking_not_found(self, mock_db_session):
        """Test error handling when booking is not found."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = send_booking_confirmation_email(mock_db_session, 999)
        
        assert result['success'] is False
        assert 'not found' in result['error'].lower()
        assert result['booking_id'] == 999
    
    def test_send_email_flight_not_found(self, mock_db_session):
        """Test error handling when flight is not found."""
        booking = Booking(
            booking_id=1,
            user_id=1,
            flight_id=1,
            status="booked",
            booking_time="2026-05-14T08:00:00",
            seat_class="economy",
            price_paid=1000
        )
        
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            booking,  # Booking found
            None,     # Flight not found
        ]
        
        result = send_booking_confirmation_email(mock_db_session, 1)
        
        assert result['success'] is False
        assert 'not found' in result['error'].lower()
    
    @patch('services.email.smtplib.SMTP')
    def test_send_email_enabled_mode(self, mock_smtp, mock_db_session):
        """Test email sending in enabled mode with SMTP."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        with patch.dict('os.environ', {
            'EMAIL_ENABLED': 'true',
            'SMTP_SERVER': 'smtp.test.com',
            'SMTP_PORT': '587',
            'SMTP_USERNAME': 'test@test.com',
            'SMTP_PASSWORD': 'password',
            'FROM_EMAIL': 'noreply@test.com'
        }):
            result = send_booking_confirmation_email(mock_db_session, 1)
            
            assert result['success'] is True
            assert 'sent successfully' in result['message'].lower()
            assert 'confirmation_code' in result
            assert 'booking_reference' in result
            assert result['recipient'] == "john@example.com"
            
            # Verify SMTP was called
            mock_smtp.assert_called_once_with('smtp.test.com', 587)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with('test@test.com', 'password')
            mock_server.send_message.assert_called_once()
    
    @patch('services.email.smtplib.SMTP')
    def test_send_email_smtp_error(self, mock_smtp, mock_db_session):
        """Test error handling for SMTP errors."""
        mock_smtp.return_value.__enter__.side_effect = Exception("SMTP connection failed")
        
        with patch.dict('os.environ', {'EMAIL_ENABLED': 'true'}):
            result = send_booking_confirmation_email(mock_db_session, 1)
            
            assert result['success'] is False
            assert 'error' in result
            assert result['booking_id'] == 1
    
    def test_confirmation_code_format_in_result(self, mock_db_session):
        """Test that confirmation code in result has correct format."""
        with patch.dict('os.environ', {'EMAIL_ENABLED': 'false'}):
            result = send_booking_confirmation_email(mock_db_session, 1)
            
            code = result['confirmation_code']
            assert len(code) == 9
            assert code[:3].isalpha()
            assert code[3:6].isdigit()
            assert code[6:].isalpha()
    
    def test_email_content_includes_all_details(self, mock_db_session):
        """Test that generated email includes all booking details."""
        with patch.dict('os.environ', {'EMAIL_ENABLED': 'false'}):
            with patch('services.email.create_email_template') as mock_template:
                mock_template.return_value = "<html>test</html>"
                
                send_booking_confirmation_email(mock_db_session, 1)
                
                # Verify template was called with correct parameters
                mock_template.assert_called_once()
                call_kwargs = mock_template.call_args[1]
                
                assert call_kwargs['customer_name'] == "John Doe"
                assert call_kwargs['destination'] == "Mars Colony Alpha"
                assert call_kwargs['origin'] == "Earth Station"
                assert call_kwargs['seat_class'] == "business"
                assert call_kwargs['price_paid'] == 2500
