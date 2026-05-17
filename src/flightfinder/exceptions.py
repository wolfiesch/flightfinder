"""Custom exceptions for FlightFinder."""


class FlightFinderError(Exception):
    """Base exception for all FlightFinder errors."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class APIError(FlightFinderError):
    """Error returned by the Skypicker/Kiwi API."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: str | None = None,
    ):
        super().__init__(message, {"status_code": status_code})
        self.status_code = status_code
        self.response_body = response_body


class RateLimitError(APIError):
    """API rate limit exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
    ):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class ValidationError(FlightFinderError):
    """Invalid input parameters."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message, {"field": field})
        self.field = field


class NetworkError(FlightFinderError):
    """Network connectivity error."""

    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.original_error = original_error


class TimeoutError(NetworkError):
    """Request timeout error."""

    pass


class ParseError(FlightFinderError):
    """Error parsing API response."""

    def __init__(self, message: str, raw_data: dict | None = None):
        super().__init__(message, {"raw_data_keys": list(raw_data.keys()) if raw_data else None})
        self.raw_data = raw_data


class ConfigurationError(FlightFinderError):
    """Configuration or setup error."""

    pass
