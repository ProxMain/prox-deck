from __future__ import annotations

import uuid

from proxdeck.application.dto.management_state import ManagementState
from proxdeck.application.services.screen_service import ScreenService
from proxdeck.domain.contracts.widget_catalog import WidgetCatalog
from proxdeck.domain.models.screen import Screen
from proxdeck.domain.models.widget_definition import WidgetDefinition
from proxdeck.domain.models.widget_instance import WidgetInstance
from proxdeck.domain.policies.widget_placement_finder import WidgetPlacementFinder
from proxdeck.domain.value_objects.widget_placement import WidgetPlacement
from proxdeck.domain.value_objects.widget_size import WidgetSize


class WidgetManagementService:
    def __init__(
        self,
        screen_service: ScreenService,
        widget_catalog: WidgetCatalog,
        widget_placement_finder: WidgetPlacementFinder,
    ) -> None:
        self._screen_service = screen_service
        self._widget_catalog = widget_catalog
        self._widget_placement_finder = widget_placement_finder

    def load_management_state(self) -> ManagementState:
        return ManagementState(
            screens=tuple(self._screen_service.list_screens()),
            widget_definitions=tuple(self._widget_catalog.list_widget_definitions()),
        )

    def add_widget_instance(
        self,
        screen_id: str,
        widget_id: str,
        column: int,
        row: int,
        width: int,
        height: int,
    ) -> Screen:
        widget_instance = WidgetInstance(
            instance_id=self._generate_instance_id(widget_id),
            widget_id=widget_id,
            screen_id=screen_id,
            placement=WidgetPlacement(
                column=column,
                row=row,
                width=width,
                height=height,
            ),
            settings=self._build_default_settings(widget_id),
        )
        return self._screen_service.add_widget_instance(screen_id, widget_instance)

    def add_widget_instance_from_preset(
        self,
        screen_id: str,
        widget_id: str,
        column: int,
        row: int,
        size_preset: str,
    ) -> Screen:
        _, width, height = WidgetSize.from_preset(size_preset)
        return self.add_widget_instance(
            screen_id=screen_id,
            widget_id=widget_id,
            column=column,
            row=row,
            width=width,
            height=height,
        )

    def add_widget_instance_smart(
        self,
        screen_id: str,
        widget_id: str,
        preferred_column: int,
        preferred_row: int,
        size_preset: str = "1/6",
    ) -> Screen:
        _, width, height = WidgetSize.from_preset(size_preset)
        placement = self._find_best_available_placement(
            screen_id=screen_id,
            widget_id=widget_id,
            width=width,
            height=height,
            preferred_column=preferred_column,
            preferred_row=preferred_row,
        )
        if placement is None:
            raise ValueError("No room is available for that widget right now")
        return self.add_widget_instance(
            screen_id=screen_id,
            widget_id=widget_id,
            column=placement.column,
            row=placement.row,
            width=placement.width,
            height=placement.height,
        )

    def remove_widget_instance(self, screen_id: str, instance_id: str) -> Screen:
        return self._screen_service.remove_widget_instance(screen_id, instance_id)

    def suggest_placement(
        self,
        screen_id: str,
        widget_id: str,
        width: int,
        height: int,
    ) -> WidgetPlacement | None:
        screen = next(
            (item for item in self._screen_service.list_screens() if item.screen_id == screen_id),
            None,
        )
        if screen is None:
            raise ValueError(f"Unknown screen id: {screen_id}")

        return self._widget_placement_finder.find_first_available(
            layout=screen.layout,
            screen_id=screen_id,
            widget_id=widget_id,
            width=width,
            height=height,
        )

    def suggest_placement_for_preset(
        self,
        screen_id: str,
        widget_id: str,
        size_preset: str,
    ) -> WidgetPlacement | None:
        _, width, height = WidgetSize.from_preset(size_preset)
        return self.suggest_placement(
            screen_id=screen_id,
            widget_id=widget_id,
            width=width,
            height=height,
        )

    def configure_web_widget(
        self,
        screen_id: str,
        instance_id: str,
        url: str,
        force_mobile: bool,
    ) -> Screen:
        screen = next(
            (item for item in self._screen_service.list_screens() if item.screen_id == screen_id),
            None,
        )
        if screen is None:
            raise ValueError(f"Unknown screen id: {screen_id}")

        widget_instance = next(
            (item for item in screen.layout.widget_instances if item.instance_id == instance_id),
            None,
        )
        if widget_instance is None:
            raise ValueError(f"Unknown widget instance id: {instance_id}")
        if widget_instance.widget_id != "web":
            raise ValueError("Only web widgets support URL and mobile configuration")

        return self._screen_service.update_widget_instance_settings(
            screen_id=screen_id,
            instance_id=instance_id,
            settings={
                **widget_instance.settings,
                "url": url.strip(),
                "force_mobile": force_mobile,
            },
        )

    def configure_launcher_widget(
        self,
        screen_id: str,
        instance_id: str,
        items: list[dict[str, str]],
    ) -> Screen:
        screen = next(
            (item for item in self._screen_service.list_screens() if item.screen_id == screen_id),
            None,
        )
        if screen is None:
            raise ValueError(f"Unknown screen id: {screen_id}")

        widget_instance = next(
            (item for item in screen.layout.widget_instances if item.instance_id == instance_id),
            None,
        )
        if widget_instance is None:
            raise ValueError(f"Unknown widget instance id: {instance_id}")
        if widget_instance.widget_id != "launcher":
            raise ValueError("Only launcher widgets support launcher item configuration")

        normalized_items = []
        for item in items:
            label = str(item.get("label", "")).strip()
            target = str(item.get("target", "")).strip()
            if not label or not target:
                continue
            normalized_items.append({"label": label, "target": target})

        if not normalized_items:
            raise ValueError("Launcher widgets require at least one valid launcher item")

        return self._screen_service.update_widget_instance_settings(
            screen_id=screen_id,
            instance_id=instance_id,
            settings={
                **widget_instance.settings,
                "items": normalized_items,
            },
        )

    def update_widget_instance_placement(
        self,
        screen_id: str,
        instance_id: str,
        column: int,
        row: int,
        width: int,
        height: int,
    ) -> Screen:
        return self._screen_service.update_widget_instance_placement(
            screen_id=screen_id,
            instance_id=instance_id,
            column=column,
            row=row,
            width=width,
            height=height,
        )

    def move_widget_instance_smart(
        self,
        screen_id: str,
        instance_id: str,
        preferred_column: int,
        preferred_row: int,
    ) -> Screen:
        screen = self._get_screen(screen_id)
        widget_instance = self._get_widget_instance(screen, instance_id)
        base_layout = screen.layout.without_widget_instance(instance_id)
        placement = self._widget_placement_finder.find_best_available(
            layout=base_layout,
            screen_id=screen_id,
            widget_id=widget_instance.widget_id,
            width=widget_instance.placement.width,
            height=widget_instance.placement.height,
            preferred_column=preferred_column,
            preferred_row=preferred_row,
        )
        if placement is None:
            raise ValueError("No room is available to move that widget there")
        return self.update_widget_instance_placement(
            screen_id=screen_id,
            instance_id=instance_id,
            column=placement.column,
            row=placement.row,
            width=placement.width,
            height=placement.height,
        )

    def resize_widget_instance_smart(
        self,
        screen_id: str,
        instance_id: str,
        size_preset: str,
    ) -> Screen:
        screen = self._get_screen(screen_id)
        widget_instance = self._get_widget_instance(screen, instance_id)
        _, width, height = WidgetSize.from_preset(size_preset)
        base_layout = screen.layout.without_widget_instance(instance_id)
        placement = self._widget_placement_finder.find_best_available(
            layout=base_layout,
            screen_id=screen_id,
            widget_id=widget_instance.widget_id,
            width=width,
            height=height,
            preferred_column=widget_instance.placement.column,
            preferred_row=widget_instance.placement.row,
        )
        if placement is None:
            raise ValueError("No room is available for that widget size")
        return self.update_widget_instance_placement(
            screen_id=screen_id,
            instance_id=instance_id,
            column=placement.column,
            row=placement.row,
            width=placement.width,
            height=placement.height,
        )

    def _generate_instance_id(self, widget_id: str) -> str:
        return f"{widget_id}-{uuid.uuid4().hex[:8]}"

    def _find_best_available_placement(
        self,
        screen_id: str,
        widget_id: str,
        width: int,
        height: int,
        preferred_column: int,
        preferred_row: int,
    ) -> WidgetPlacement | None:
        screen = self._get_screen(screen_id)
        return self._widget_placement_finder.find_best_available(
            layout=screen.layout,
            screen_id=screen_id,
            widget_id=widget_id,
            width=width,
            height=height,
            preferred_column=preferred_column,
            preferred_row=preferred_row,
        )

    def _get_screen(self, screen_id: str) -> Screen:
        screen = next(
            (item for item in self._screen_service.list_screens() if item.screen_id == screen_id),
            None,
        )
        if screen is None:
            raise ValueError(f"Unknown screen id: {screen_id}")
        return screen

    def _get_widget_instance(self, screen: Screen, instance_id: str) -> WidgetInstance:
        widget_instance = next(
            (item for item in screen.layout.widget_instances if item.instance_id == instance_id),
            None,
        )
        if widget_instance is None:
            raise ValueError(f"Unknown widget instance id: {instance_id}")
        return widget_instance

    def _build_default_settings(self, widget_id: str) -> dict[str, object]:
        if widget_id == "launcher":
            return {
                "items": [
                    {"label": "GitHub", "target": "https://github.com"},
                    {"label": "OpenAI", "target": "https://openai.com"},
                    {"label": "YouTube", "target": "https://youtube.com"},
                    {"label": "Settings", "target": "ms-settings:"},
                ]
            }
        if widget_id == "web":
            return {
                "url": "https://example.com",
                "force_mobile": False,
            }
        return {}
