from __future__ import annotations

from abc import ABC, abstractmethod

from proxdeck.domain.models.screen import Screen


class ScreenRepository(ABC):
    @abstractmethod
    def list_screens(self) -> list[Screen]:
        raise NotImplementedError

    @abstractmethod
    def save_screens(self, screens: list[Screen]) -> None:
        raise NotImplementedError
