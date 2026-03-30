from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from proxdeck.domain.models.stream_deck import (
    STREAM_DECK_LAUNCH_ACTION,
    STREAM_DECK_NOOP_ACTION,
    StreamDeckButtonDefinition,
)


@dataclass(frozen=True)
class StreamDeckActionResult:
    success: bool
    message: str


class LaunchTargetExecutor(Protocol):
    def launch(self, target: str, arguments: list[str]) -> StreamDeckActionResult: ...


class StreamDeckActionExecutor:
    def __init__(self, launch_target_executor: LaunchTargetExecutor) -> None:
        self._launch_target_executor = launch_target_executor

    def execute(self, button: StreamDeckButtonDefinition) -> StreamDeckActionResult:
        if button.action_type == STREAM_DECK_NOOP_ACTION:
            return StreamDeckActionResult(
                success=False,
                message=f"{button.label} has no action assigned.",
            )

        if button.action_type != STREAM_DECK_LAUNCH_ACTION:
            return StreamDeckActionResult(
                success=False,
                message=f"{button.label} uses unsupported action type '{button.action_type}'.",
            )

        target = str(button.action_config.get("target", "")).strip()
        arguments = button.action_config.get("arguments", [])
        if not target:
            return StreamDeckActionResult(
                success=False,
                message=f"{button.label} is missing a launch target.",
            )
        if not isinstance(arguments, list):
            arguments = []
        normalized_arguments = [str(argument).strip() for argument in arguments if str(argument).strip()]
        return self._launch_target_executor.launch(target, normalized_arguments)

