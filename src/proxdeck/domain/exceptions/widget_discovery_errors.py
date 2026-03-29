from __future__ import annotations

from pathlib import Path


class WidgetDiscoveryError(ValueError):
    """Base error for widget discovery failures."""


class WidgetManifestLoadError(WidgetDiscoveryError):
    """Raised when a widget manifest cannot be parsed or validated."""

    def __init__(self, manifest_path: Path, reason: str) -> None:
        super().__init__(f"Invalid widget manifest at '{manifest_path}': {reason}")
        self.manifest_path = manifest_path
        self.reason = reason


class DuplicateWidgetIdError(WidgetDiscoveryError):
    """Raised when multiple manifests declare the same widget id."""

    def __init__(self, widget_id: str) -> None:
        super().__init__(f"Duplicate widget id discovered: {widget_id}")
        self.widget_id = widget_id


class IncompatibleWidgetError(WidgetDiscoveryError):
    """Raised when a widget requires a newer app version than supported."""

    def __init__(self, widget_id: str, required_version: str, current_version: str) -> None:
        super().__init__(
            f"Widget '{widget_id}' requires app version {required_version} but current version is {current_version}"
        )
        self.widget_id = widget_id
        self.required_version = required_version
        self.current_version = current_version
