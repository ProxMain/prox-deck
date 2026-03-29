from proxdeck.domain.models.screen import Screen
from proxdeck.domain.models.screen_availability import ScreenAvailability
from proxdeck.domain.models.screen_layout import ScreenLayout
from proxdeck.presentation.views.runtime_window import RuntimeWindow


def test_management_status_text_for_available_screen() -> None:
    screen = Screen(
        screen_id="gaming",
        name="Gaming",
        availability=ScreenAvailability.AVAILABLE,
        layout=ScreenLayout(),
    )

    status = RuntimeWindow._build_management_status_text(screen)

    assert status == "Gaming is editable."


def test_management_status_text_for_soon_screen() -> None:
    screen = Screen(
        screen_id="developing",
        name="Developing",
        availability=ScreenAvailability.SOON,
        layout=ScreenLayout(),
    )

    status = RuntimeWindow._build_management_status_text(screen)

    assert status == "Developing is not editable yet. This screen is marked Soon."
