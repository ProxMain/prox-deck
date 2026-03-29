from __future__ import annotations

import json
from pathlib import Path

from proxdeck.domain.contracts.screen_repository import ScreenRepository
from proxdeck.domain.models.screen import Screen
from proxdeck.domain.models.screen_availability import ScreenAvailability
from proxdeck.domain.models.screen_layout import EDGE_GRID_SIZE, ScreenLayout
from proxdeck.domain.models.widget_instance import WidgetInstance
from proxdeck.domain.value_objects.widget_placement import WidgetPlacement


class JsonScreenRepository(ScreenRepository):
    def __init__(self, storage_path: Path) -> None:
        self._storage_path = storage_path

    def list_screens(self) -> list[Screen]:
        if not self._storage_path.exists():
            return []

        payload = json.loads(self._storage_path.read_text(encoding="utf-8"))
        return [self._deserialize_screen(item) for item in payload.get("screens", [])]

    def save_screens(self, screens: list[Screen]) -> None:
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"screens": [self._serialize_screen(screen) for screen in screens]}
        self._storage_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _serialize_screen(self, screen: Screen) -> dict[str, object]:
        return {
            "screen_id": screen.screen_id,
            "name": screen.name,
            "availability": screen.availability.value,
            "state": screen.state,
            "widgets": [
                {
                    "instance_id": instance.instance_id,
                    "widget_id": instance.widget_id,
                    "screen_id": instance.screen_id,
                    "placement": {
                        "column": instance.placement.column,
                        "row": instance.placement.row,
                        "width": instance.placement.width,
                        "height": instance.placement.height,
                    },
                    "settings": instance.settings,
                    "runtime_state": instance.runtime_state,
                }
                for instance in screen.layout.widget_instances
            ],
        }

    def _deserialize_screen(self, payload: dict[str, object]) -> Screen:
        widgets = tuple(
            WidgetInstance(
                instance_id=item["instance_id"],
                widget_id=item["widget_id"],
                screen_id=item["screen_id"],
                placement=WidgetPlacement(
                    column=item["placement"]["column"],
                    row=item["placement"]["row"],
                    width=item["placement"]["width"],
                    height=item["placement"]["height"],
                ),
                settings=dict(item.get("settings", {})),
                runtime_state=dict(item.get("runtime_state", {})),
            )
            for item in payload.get("widgets", [])
        )
        return Screen(
            screen_id=str(payload["screen_id"]),
            name=str(payload["name"]),
            availability=ScreenAvailability(str(payload["availability"])),
            layout=ScreenLayout(grid_size=EDGE_GRID_SIZE, widget_instances=widgets),
            state=dict(payload.get("state", {})),
        )
