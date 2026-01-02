"""
Climatiq API exceptions
"""


class ClimatiqAPIError(Exception):
    """Custom exception for Climatiq API errors"""
    pass


class ClimatiqRateLimitError(ClimatiqAPIError):
    """Raised when API rate limit is exceeded"""
    pass


class ClimatiqAuthenticationError(ClimatiqAPIError):
    """Raised when API authentication fails"""
    pass


class ClimatiqValidationError(ClimatiqAPIError):
    """Raised when API validation fails"""
    pass
