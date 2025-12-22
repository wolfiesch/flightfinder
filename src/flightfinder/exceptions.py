"""Custom exceptions for FlightFinder."""

from typing import Optional


class FlightFinderError(Exception):
    """Base exception for all FlightFinder errors."""

    def __init__(self, message: str, details: Optional[dict] = None):
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
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ):
        super().__init__(message, {"status_code": status_code})
        self.status_code = status_code
        self.response_body = response_body


class RateLimitError(APIError):
    """API rate limit exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
    ):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class ValidationError(FlightFinderError):
    """Invalid input parameters."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, {"field": field})
        self.field = field


class NetworkError(FlightFinderError):
    """Network connectivity error."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class TimeoutError(NetworkError):
    """Request timeout error."""

    pass


class ParseError(FlightFinderError):
    """Error parsing API response."""

    def __init__(self, message: str, raw_data: Optional[dict] = None):
        super().__init__(message, {"raw_data_keys": list(raw_data.keys()) if raw_data else None})
        self.raw_data = raw_data


class ConfigurationError(FlightFinderError):
    """Configuration or setup error."""

    pass
