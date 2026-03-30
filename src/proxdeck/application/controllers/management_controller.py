from __future__ import annotations

from proxdeck.application.dto.management_state import ManagementState
from proxdeck.application.services.widget_management_service import WidgetManagementService
from proxdeck.domain.models.screen import Screen
from proxdeck.domain.value_objects.widget_placement import WidgetPlacement


class ManagementController:
    def __init__(self, widget_management_service: WidgetManagementService) -> None:
        self._widget_management_service = widget_management_service

    def load_management_state(self) -> ManagementState:
        return self._widget_management_service.load_management_state()

    def add_widget_instance(
        self,
        screen_id: str,
        widget_id: str,
        column: int,
        row: int,
        width: int,
        height: int,
    ) -> Screen:
        return self._widget_management_service.add_widget_instance(
            screen_id=screen_id,
            widget_id=widget_id,
            column=column,
            row=row,
            width=width,
            height=height,
        )

    def add_widget_instance_from_preset(
        self,
        screen_id: str,
        widget_id: str,
        column: int,
        row: int,
        size_preset: str,
    ) -> Screen:
        return self._widget_management_service.add_widget_instance_from_preset(
            screen_id=screen_id,
            widget_id=widget_id,
            column=column,
            row=row,
            size_preset=size_preset,
        )

    def add_widget_instance_smart(
        self,
        screen_id: str,
        widget_id: str,
        preferred_column: int,
        preferred_row: int,
        size_preset: str = "1/6",
    ) -> Screen:
        return self._widget_management_service.add_widget_instance_smart(
            screen_id=screen_id,
            widget_id=widget_id,
            preferred_column=preferred_column,
            preferred_row=preferred_row,
            size_preset=size_preset,
        )

    def remove_widget_instance(self, screen_id: str, instance_id: str) -> Screen:
        return self._widget_management_service.remove_widget_instance(screen_id, instance_id)

    def suggest_placement(
        self,
        screen_id: str,
        widget_id: str,
        width: int,
        height: int,
    ) -> WidgetPlacement | None:
        return self._widget_management_service.suggest_placement(
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
        return self._widget_management_service.suggest_placement_for_preset(
            screen_id=screen_id,
            widget_id=widget_id,
            size_preset=size_preset,
        )

    def configure_web_widget(
        self,
        screen_id: str,
        instance_id: str,
        url: str,
        force_mobile: bool,
    ) -> Screen:
        return self._widget_management_service.configure_web_widget(
            screen_id=screen_id,
            instance_id=instance_id,
            url=url,
            force_mobile=force_mobile,
        )

    def configure_launcher_widget(
        self,
        screen_id: str,
        instance_id: str,
        items: list[dict[str, str]],
    ) -> Screen:
        return self._widget_management_service.configure_launcher_widget(
            screen_id=screen_id,
            instance_id=instance_id,
            items=items,
        )

    def configure_stream_deck_widget(
        self,
        screen_id: str,
        instance_id: str,
        size_variant: str,
        buttons: list[dict[str, object]],
    ) -> Screen:
        return self._widget_management_service.configure_stream_deck_widget(
            screen_id=screen_id,
            instance_id=instance_id,
            size_variant=size_variant,
            buttons=buttons,
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
        return self._widget_management_service.update_widget_instance_placement(
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
        return self._widget_management_service.move_widget_instance_smart(
            screen_id=screen_id,
            instance_id=instance_id,
            preferred_column=preferred_column,
            preferred_row=preferred_row,
        )

    def resize_widget_instance_smart(
        self,
        screen_id: str,
        instance_id: str,
        size_preset: str,
    ) -> Screen:
        return self._widget_management_service.resize_widget_instance_smart(
            screen_id=screen_id,
            instance_id=instance_id,
            size_preset=size_preset,
        )
