"""Tests for FlightFinder exceptions."""

from flightfinder.exceptions import (
    APIError,
    ConfigurationError,
    FlightFinderError,
    NetworkError,
    ParseError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)


class TestFlightFinderError:
    """Tests for base FlightFinderError."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = FlightFinderError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.details == {}

    def test_error_with_details(self):
        """Test error with details."""
        error = FlightFinderError("Error", details={"code": 123})
        assert "code" in str(error)
        assert error.details["code"] == 123


class TestAPIError:
    """Tests for APIError."""

    def test_api_error(self):
        """Test API error creation."""
        error = APIError("API failed", status_code=500, response_body="Internal error")
        assert error.status_code == 500
        assert error.response_body == "Internal error"


class TestRateLimitError:
    """Tests for RateLimitError."""

    def test_rate_limit_error(self):
        """Test rate limit error creation."""
        error = RateLimitError(retry_after=60)
        assert error.status_code == 429
        assert error.retry_after == 60

    def test_rate_limit_default_message(self):
        """Test default rate limit message."""
        error = RateLimitError()
        assert "Rate limit" in error.message


class TestValidationError:
    """Tests for ValidationError."""

    def test_validation_error(self):
        """Test validation error creation."""
        error = ValidationError("Invalid input", field="origin")
        assert error.field == "origin"
        assert "field" in error.details


class TestNetworkError:
    """Tests for NetworkError."""

    def test_network_error(self):
        """Test network error creation."""
        original = Exception("Connection refused")
        error = NetworkError("Network failed", original_error=original)
        assert error.original_error is original


class TestTimeoutError:
    """Tests for TimeoutError."""

    def test_timeout_error(self):
        """Test timeout error is a NetworkError."""
        error = TimeoutError("Request timed out")
        assert isinstance(error, NetworkError)


class TestParseError:
    """Tests for ParseError."""

    def test_parse_error(self):
        """Test parse error creation."""
        raw_data = {"malformed": "data"}
        error = ParseError("Failed to parse", raw_data=raw_data)
        assert error.raw_data == raw_data


class TestConfigurationError:
    """Tests for ConfigurationError."""

    def test_configuration_error(self):
        """Test configuration error creation."""
        error = ConfigurationError("Invalid configuration")
        assert isinstance(error, FlightFinderError)
