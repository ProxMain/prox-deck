from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WidgetInstallMetadata:
    distribution: str
    installation_scope: str

    def __post_init__(self) -> None:
        if not self.distribution.strip():
            raise ValueError("Install metadata requires a distribution value")
        if not self.installation_scope.strip():
            raise ValueError("Install metadata requires an installation scope value")
