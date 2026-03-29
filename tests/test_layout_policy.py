from proxdeck.domain.exceptions.layout_errors import (
    LayoutValidationError,
    WidgetCapacityExceededError,
)
from proxdeck.domain.models.screen_layout import ScreenLayout
from proxdeck.domain.models.widget_instance import WidgetInstance
from proxdeck.domain.policies.layout_policy import LayoutPolicy
from proxdeck.domain.value_objects.widget_placement import WidgetPlacement


def test_layout_policy_rejects_overlap() -> None:
    policy = LayoutPolicy()
    existing = WidgetInstance(
        instance_id="clock-1",
        widget_id="clock",
        screen_id="gaming",
        placement=WidgetPlacement(column=0, row=0, width=1, height=1),
    )
    layout = ScreenLayout().with_widget_instance(existing)
    candidate = WidgetInstance(
        instance_id="notes-1",
        widget_id="notes",
        screen_id="gaming",
        placement=WidgetPlacement(column=0, row=0, width=2, height=1),
    )

    try:
        policy.ensure_widget_can_be_added(layout, candidate)
    except LayoutValidationError:
        return

    raise AssertionError("Expected overlapping placement to be rejected")


def test_layout_policy_rejects_capacity_overflow() -> None:
    policy = LayoutPolicy()
    full = WidgetInstance(
        instance_id="full",
        widget_id="web",
        screen_id="gaming",
        placement=WidgetPlacement(column=0, row=0, width=3, height=2),
    )
    layout = ScreenLayout().with_widget_instance(full)
    candidate = WidgetInstance(
        instance_id="clock-2",
        widget_id="clock",
        screen_id="gaming",
        placement=WidgetPlacement(column=0, row=0, width=1, height=1),
    )

    try:
        policy.ensure_widget_can_be_added(layout, candidate)
    except (LayoutValidationError, WidgetCapacityExceededError):
        return

    raise AssertionError("Expected capacity overflow to be rejected")
