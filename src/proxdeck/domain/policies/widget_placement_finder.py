from __future__ import annotations

from proxdeck.domain.exceptions.layout_errors import LayoutValidationError
from proxdeck.domain.models.screen_layout import ScreenLayout
from proxdeck.domain.models.widget_instance import WidgetInstance
from proxdeck.domain.policies.layout_policy import LayoutPolicy
from proxdeck.domain.value_objects.widget_placement import WidgetPlacement


class WidgetPlacementFinder:
    def __init__(self, layout_policy: LayoutPolicy) -> None:
        self._layout_policy = layout_policy

    def find_first_available(
        self,
        layout: ScreenLayout,
        screen_id: str,
        widget_id: str,
        width: int,
        height: int,
    ) -> WidgetPlacement | None:
        max_row = layout.grid_size.rows - height
        max_column = layout.grid_size.columns - width

        for row in range(max_row + 1):
            for column in range(max_column + 1):
                placement = WidgetPlacement(
                    column=column,
                    row=row,
                    width=width,
                    height=height,
                )
                candidate = WidgetInstance(
                    instance_id="placement-preview",
                    widget_id=widget_id,
                    screen_id=screen_id,
                    placement=placement,
                )
                try:
                    self._layout_policy.ensure_widget_can_be_added(layout, candidate)
                except LayoutValidationError:
                    continue
                return placement
        return None
