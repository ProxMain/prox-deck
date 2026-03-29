from __future__ import annotations

from proxdeck.domain.models.screen import Screen
from proxdeck.domain.models.screen_availability import ScreenAvailability
from proxdeck.domain.models.screen_layout import ScreenLayout
from proxdeck.domain.models.widget_instance import WidgetInstance
from proxdeck.domain.value_objects.widget_placement import WidgetPlacement


class DefaultScreenFactory:
    def create_defaults(self) -> list[Screen]:
        return [
            Screen(
                screen_id="gaming",
                name="Gaming",
                availability=ScreenAvailability.AVAILABLE,
                layout=ScreenLayout(
                    widget_instances=(
                        WidgetInstance(
                            instance_id="gaming-clock",
                            widget_id="clock",
                            screen_id="gaming",
                            placement=WidgetPlacement(column=0, row=0, width=1, height=1),
                        ),
                        WidgetInstance(
                            instance_id="gaming-core",
                            widget_id="system-stats",
                            screen_id="gaming",
                            placement=WidgetPlacement(column=1, row=0, width=2, height=2),
                        ),
                        WidgetInstance(
                            instance_id="gaming-memory",
                            widget_id="system-stats",
                            screen_id="gaming",
                            placement=WidgetPlacement(column=0, row=1, width=1, height=1),
                        ),
                    )
                ),
            ),
            Screen(
                screen_id="performance",
                name="Performance",
                availability=ScreenAvailability.AVAILABLE,
                layout=ScreenLayout(
                    widget_instances=(
                        WidgetInstance(
                            instance_id="performance-cpu",
                            widget_id="system-stats",
                            screen_id="performance",
                            placement=WidgetPlacement(column=0, row=0, width=1, height=1),
                        ),
                        WidgetInstance(
                            instance_id="performance-memory",
                            widget_id="system-stats",
                            screen_id="performance",
                            placement=WidgetPlacement(column=1, row=0, width=1, height=1),
                        ),
                        WidgetInstance(
                            instance_id="performance-thermal",
                            widget_id="system-stats",
                            screen_id="performance",
                            placement=WidgetPlacement(column=2, row=0, width=1, height=1),
                        ),
                        WidgetInstance(
                            instance_id="performance-core-stack",
                            widget_id="system-stats",
                            screen_id="performance",
                            placement=WidgetPlacement(column=0, row=1, width=2, height=1),
                        ),
                        WidgetInstance(
                            instance_id="performance-clock",
                            widget_id="clock",
                            screen_id="performance",
                            placement=WidgetPlacement(column=2, row=1, width=1, height=1),
                        ),
                    )
                ),
            ),
            Screen(
                screen_id="streaming",
                name="Streaming",
                availability=ScreenAvailability.AVAILABLE,
                layout=ScreenLayout(
                    widget_instances=(
                        WidgetInstance(
                            instance_id="streaming-clock",
                            widget_id="clock",
                            screen_id="streaming",
                            placement=WidgetPlacement(column=0, row=0, width=1, height=1),
                        ),
                        WidgetInstance(
                            instance_id="streaming-cpu",
                            widget_id="system-stats",
                            screen_id="streaming",
                            placement=WidgetPlacement(column=1, row=0, width=1, height=1),
                        ),
                        WidgetInstance(
                            instance_id="streaming-ram",
                            widget_id="system-stats",
                            screen_id="streaming",
                            placement=WidgetPlacement(column=2, row=0, width=1, height=1),
                        ),
                        WidgetInstance(
                            instance_id="streaming-core",
                            widget_id="system-stats",
                            screen_id="streaming",
                            placement=WidgetPlacement(column=0, row=1, width=3, height=1),
                        ),
                    )
                ),
            ),
            Screen(
                screen_id="developing",
                name="Developing",
                availability=ScreenAvailability.SOON,
                layout=ScreenLayout(),
            ),
        ]
