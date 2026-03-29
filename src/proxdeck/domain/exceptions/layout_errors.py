class LayoutValidationError(ValueError):
    """Raised when a widget placement violates layout rules."""


class WidgetCapacityExceededError(LayoutValidationError):
    """Raised when a layout exceeds its available capacity."""


class LockedScreenError(ValueError):
    """Raised when an unavailable screen is activated."""
