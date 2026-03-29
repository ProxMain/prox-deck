from __future__ import annotations

from abc import ABC, abstractmethod

from proxdeck.domain.models.widget_definition import WidgetDefinition


class WidgetCatalog(ABC):
    @abstractmethod
    def list_widget_definitions(self) -> list[WidgetDefinition]:
        raise NotImplementedError

    @abstractmethod
    def get_widget_definition(self, widget_id: str) -> WidgetDefinition:
        raise NotImplementedError
