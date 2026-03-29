from __future__ import annotations

from dataclasses import dataclass, field

from proxdeck.domain.value_objects.widget_placement import WidgetPlacement


@dataclass(frozen=True)
class WidgetInstance:
    instance_id: str
    widget_id: str
    screen_id: str
    placement: WidgetPlacement
    settings: dict[str, object] = field(default_factory=dict)
    runtime_state: dict[str, object] = field(default_factory=dict)
