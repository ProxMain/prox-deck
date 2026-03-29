from __future__ import annotations

from dataclasses import dataclass

from proxdeck.domain.value_objects.app_version import AppVersion


@dataclass(frozen=True)
class WidgetCompatibility:
    minimum_app_version: AppVersion
