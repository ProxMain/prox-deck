from __future__ import annotations

import os
import subprocess
import webbrowser

from proxdeck.application.services.stream_deck_action_executor import StreamDeckActionResult


def _build_windows_subprocess_kwargs() -> dict[str, object]:
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        return {"creationflags": subprocess.CREATE_NO_WINDOW}
    return {}


class DesktopLaunchExecutor:
    def launch(self, target: str, arguments: list[str]) -> StreamDeckActionResult:
        try:
            if _looks_like_shell_target(target):
                self._open_associated_target(target)
            else:
                subprocess.Popen(
                    [target, *arguments],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    **_build_windows_subprocess_kwargs(),
                )
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            return StreamDeckActionResult(
                success=False,
                message=f"Launch failed for {target}: {error}",
            )
        return StreamDeckActionResult(success=True, message=f"Launched {target}")

    def _open_associated_target(self, target: str) -> None:
        if hasattr(os, "startfile"):
            os.startfile(target)  # type: ignore[attr-defined]
            return
        if not webbrowser.open(target):
            raise OSError("No launcher is available for that target")


def _looks_like_shell_target(target: str) -> bool:
    normalized = target.strip().lower()
    return "://" in normalized or normalized.startswith(("mailto:", "ms-settings:"))

