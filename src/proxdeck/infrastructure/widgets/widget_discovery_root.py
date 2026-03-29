from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from proxdeck.domain.models.widget_kind import WidgetKind


@dataclass(frozen=True)
class WidgetDiscoveryRoot:
    path: Path
    expected_kind: WidgetKind
