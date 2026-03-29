from __future__ import annotations

from abc import ABC, abstractmethod

from proxdeck.domain.models.runtime_target import RuntimeTarget


class RuntimeTargetDetector(ABC):
    @abstractmethod
    def detect_target(self) -> RuntimeTarget | None:
        raise NotImplementedError
