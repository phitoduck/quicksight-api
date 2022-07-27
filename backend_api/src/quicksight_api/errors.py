"""
Define all errors specific to quicksight_api Api.

As a pattern, errors used in quicksight_api Api define custom error classes for different error types. This
is useful in helping the calling application discern tool errors from those generated by upstream
tools.
"""


class QuicksightApiError(Exception):
    """Base error class for the QuickSight API."""


class ConfigurationError(QuicksightApiError):
    """Raised when there is a configuration error."""


class AuthServiceError(QuicksightApiError):
    """Raised when there is an error regarding the auth service"""


class MalformedTokenError(QuicksightApiError):
    def __init__(self, token: str, stacktrace_error: Exception):
        self.token = token

    @property
    def message(self):
        return f"Error: malformed JWT Token. Got this error: {str(self)}" + f"\n\nToken: {str(self.token)}"

class UserAlreadyRegisteredError(QuicksightApiError):
    """Raised if an attempt is made to register a user that is already registered."""

class DuplicateExampleTitle(QuicksightApiError):
    """
    Raised when an HTTP route has two documented example responses
    in one HTTP status code with the same title
    """
