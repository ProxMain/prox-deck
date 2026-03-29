from __future__ import annotations

from proxdeck.domain.exceptions.layout_errors import (
    LayoutValidationError,
    WidgetCapacityExceededError,
)
from proxdeck.domain.models.screen_layout import ScreenLayout
from proxdeck.domain.models.widget_instance import WidgetInstance


class LayoutPolicy:
    """Validate widget placements against the fixed Edge dashboard grid."""

    def ensure_widget_can_be_added(
        self, layout: ScreenLayout, widget_instance: WidgetInstance
    ) -> None:
        placement = widget_instance.placement
        grid = layout.grid_size

        for column, row in placement.cells():
            if not grid.contains(column, row):
                raise LayoutValidationError("Widget placement exceeds dashboard bounds")

        new_cells = placement.cells()
        if layout.occupied_cells.intersection(new_cells):
            raise LayoutValidationError("Widget placement overlaps an existing widget")

        total_cells = len(layout.occupied_cells) + placement.area
        if total_cells > grid.capacity:
            raise WidgetCapacityExceededError("Dashboard capacity would exceed 6/6")
