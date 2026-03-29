from __future__ import annotations

from proxdeck.application.services.default_screen_factory import DefaultScreenFactory
from proxdeck.domain.contracts.screen_repository import ScreenRepository
from proxdeck.domain.contracts.widget_catalog import WidgetCatalog
from proxdeck.domain.models.screen import Screen
from proxdeck.domain.models.widget_definition import WidgetDefinition
from proxdeck.domain.models.widget_instance import WidgetInstance
from proxdeck.domain.policies.layout_policy import LayoutPolicy
from proxdeck.domain.policies.screen_availability_policy import ScreenAvailabilityPolicy


class ScreenService:
    def __init__(
        self,
        screen_repository: ScreenRepository,
        widget_catalog: WidgetCatalog,
        default_screen_factory: DefaultScreenFactory,
        layout_policy: LayoutPolicy,
        availability_policy: ScreenAvailabilityPolicy,
    ) -> None:
        self._screen_repository = screen_repository
        self._widget_catalog = widget_catalog
        self._default_screen_factory = default_screen_factory
        self._layout_policy = layout_policy
        self._availability_policy = availability_policy

    def list_screens(self) -> list[Screen]:
        screens = self._screen_repository.list_screens()
        if screens:
            return screens

        defaults = self._default_screen_factory.create_defaults()
        self._screen_repository.save_screens(defaults)
        return defaults

    def get_active_screen(self) -> Screen:
        for screen in self.list_screens():
            if screen.is_available():
                return screen
        raise ValueError("No available runtime screen was found")

    def switch_screen(self, screen_id: str) -> Screen:
        screen = self._find_screen(screen_id)
        self._availability_policy.ensure_accessible(screen)
        return screen

    def add_widget_instance(self, screen_id: str, widget_instance: WidgetInstance) -> Screen:
        widget_definition = self._widget_catalog.get_widget_definition(widget_instance.widget_id)
        self._validate_widget_instance(widget_definition, widget_instance)

        screens = self.list_screens()
        updated_screens: list[Screen] = []
        updated_screen: Screen | None = None

        for screen in screens:
            if screen.screen_id != screen_id:
                updated_screens.append(screen)
                continue

            self._availability_policy.ensure_accessible(screen)
            self._layout_policy.ensure_widget_can_be_added(screen.layout, widget_instance)
            updated_screen = Screen(
                screen_id=screen.screen_id,
                name=screen.name,
                availability=screen.availability,
                layout=screen.layout.with_widget_instance(widget_instance),
                state=screen.state,
            )
            updated_screens.append(updated_screen)

        if updated_screen is None:
            raise ValueError(f"Unknown screen id: {screen_id}")

        self._screen_repository.save_screens(updated_screens)
        return updated_screen

    def remove_widget_instance(self, screen_id: str, instance_id: str) -> Screen:
        screens = self.list_screens()
        updated_screens: list[Screen] = []
        updated_screen: Screen | None = None

        for screen in screens:
            if screen.screen_id != screen_id:
                updated_screens.append(screen)
                continue

            self._availability_policy.ensure_accessible(screen)
            updated_screen = Screen(
                screen_id=screen.screen_id,
                name=screen.name,
                availability=screen.availability,
                layout=screen.layout.without_widget_instance(instance_id),
                state=screen.state,
            )
            updated_screens.append(updated_screen)

        if updated_screen is None:
            raise ValueError(f"Unknown screen id: {screen_id}")

        self._screen_repository.save_screens(updated_screens)
        return updated_screen

    def update_widget_instance_settings(
        self,
        screen_id: str,
        instance_id: str,
        settings: dict[str, object],
    ) -> Screen:
        screens = self.list_screens()
        updated_screens: list[Screen] = []
        updated_screen: Screen | None = None

        for screen in screens:
            if screen.screen_id != screen_id:
                updated_screens.append(screen)
                continue

            self._availability_policy.ensure_accessible(screen)
            updated_instances = []
            instance_updated = False
            for instance in screen.layout.widget_instances:
                if instance.instance_id != instance_id:
                    updated_instances.append(instance)
                    continue

                instance_updated = True
                updated_instances.append(
                    WidgetInstance(
                        instance_id=instance.instance_id,
                        widget_id=instance.widget_id,
                        screen_id=instance.screen_id,
                        placement=instance.placement,
                        settings=settings,
                        runtime_state=instance.runtime_state,
                    )
                )

            if not instance_updated:
                raise ValueError(f"Unknown widget instance id: {instance_id}")

            updated_screen = Screen(
                screen_id=screen.screen_id,
                name=screen.name,
                availability=screen.availability,
                layout=type(screen.layout)(
                    grid_size=screen.layout.grid_size,
                    widget_instances=tuple(updated_instances),
                ),
                state=screen.state,
            )
            updated_screens.append(updated_screen)

        if updated_screen is None:
            raise ValueError(f"Unknown screen id: {screen_id}")

        self._screen_repository.save_screens(updated_screens)
        return updated_screen

    def _find_screen(self, screen_id: str) -> Screen:
        for screen in self.list_screens():
            if screen.screen_id == screen_id:
                return screen
        raise ValueError(f"Unknown screen id: {screen_id}")

    def _validate_widget_instance(
        self, widget_definition: WidgetDefinition, widget_instance: WidgetInstance
    ) -> None:
        if widget_definition.widget_id != widget_instance.widget_id:
            raise ValueError("Widget instance does not match the requested definition")
