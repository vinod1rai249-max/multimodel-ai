class StudioError(Exception):
    """Base exception for the AI Studio."""
    def __init__(self, message: str, metadata: dict = None):
        super().__init__(message)
        self.metadata = metadata or {}

class ProviderError(StudioError):
    """Base exception for provider-related issues."""
    pass

class ProviderNotConfigured(ProviderError):
    """Raised when a provider's API key is missing or invalid."""
    pass

class ProviderAuthError(ProviderError):
    """Raised when authentication fails."""
    pass

class ProviderRateLimitError(ProviderError):
    """Raised when rate limits are exceeded."""
    pass

class ProviderTimeoutError(ProviderError):
    """Raised when a request to a provider times out."""
    pass

class ProviderResponseError(ProviderError):
    """Raised when a provider returns an unexpected response."""
    pass

class UnsupportedRouteError(StudioError):
    """Raised when a requested multimodal route is not supported."""
    pass

class ProviderQuotaError(ProviderError):
    """Raised when a provider's quota is exceeded."""
    pass

class ProviderCreditError(ProviderError):
    """Raised when a provider has insufficient credits or requested tokens are too high."""
    pass

class ProviderModerationError(ProviderError):
    """Raised when a request is rejected by safety filters."""
    pass

class NetworkDNSError(ProviderError):
    """Raised when a provider's API is unreachable due to DNS issues."""
    pass

class AllProvidersFailedError(StudioError):
    """Raised when all attempted providers in a chain fail."""
    def __init__(self, message: str, failures: list = None, trace_id: str = None):
        super().__init__(message)
        self.failures = failures or []
        self.trace_id = trace_id
