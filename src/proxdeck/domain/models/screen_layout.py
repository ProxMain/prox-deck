from __future__ import annotations

from dataclasses import dataclass, field

from proxdeck.domain.models.widget_instance import WidgetInstance
from proxdeck.domain.value_objects.grid_size import GridSize


EDGE_GRID_SIZE = GridSize(columns=3, rows=2)


@dataclass(frozen=True)
class ScreenLayout:
    grid_size: GridSize = EDGE_GRID_SIZE
    widget_instances: tuple[WidgetInstance, ...] = field(default_factory=tuple)

    @property
    def occupied_cells(self) -> set[tuple[int, int]]:
        cells: set[tuple[int, int]] = set()
        for instance in self.widget_instances:
            cells.update(instance.placement.cells())
        return cells

    def with_widget_instance(self, widget_instance: WidgetInstance) -> "ScreenLayout":
        return ScreenLayout(
            grid_size=self.grid_size,
            widget_instances=(*self.widget_instances, widget_instance),
        )

    def without_widget_instance(self, instance_id: str) -> "ScreenLayout":
        remaining = tuple(
            instance for instance in self.widget_instances if instance.instance_id != instance_id
        )
        return ScreenLayout(grid_size=self.grid_size, widget_instances=remaining)
