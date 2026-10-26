"""Safe provider errors for optional external data services."""


class ProviderNotConfiguredError(RuntimeError):
    """Raised when an external provider is requested without its credentials."""


class ProviderRequestError(RuntimeError):
    """Raised when an external provider cannot return a usable response."""


class RouteNotFoundError(RuntimeError):
    """Raised when a provider returns no route for the requested endpoints."""
