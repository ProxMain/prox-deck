from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class SteamGameButtonDefinition:
    app_id: str
    name: str
    icon: str
    target: str


class SteamGameDiscovery:
    def __init__(self, steam_root: Path | None = None) -> None:
        self._steam_root = steam_root or Path(r"C:\Program Files (x86)\Steam")

    def discover_buttons(self, limit: int) -> list[dict[str, object]]:
        if limit <= 0 or not self._steam_root.exists():
            return []
        buttons: list[dict[str, object]] = []
        for manifest_path in self._manifest_paths():
            game = self._parse_manifest(manifest_path)
            if game is None:
                continue
            buttons.append(
                {
                    "id": f"steam-{game.app_id}",
                    "label": game.name,
                    "icon": game.icon,
                    "action_type": "launch",
                    "action_config": {"target": game.target},
                }
            )
            if len(buttons) >= limit:
                break
        return buttons

    def _manifest_paths(self) -> list[Path]:
        paths: list[Path] = []
        for library_path in self._library_paths():
            steamapps_path = library_path / "steamapps"
            if not steamapps_path.exists():
                continue
            paths.extend(sorted(steamapps_path.glob("appmanifest_*.acf")))
        return paths

    def _library_paths(self) -> list[Path]:
        libraryfolders_path = self._steam_root / "steamapps" / "libraryfolders.vdf"
        libraries = [self._steam_root]
        if not libraryfolders_path.exists():
            return libraries
        try:
            content = libraryfolders_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return libraries
        for raw_path in re.findall(r'"path"\s+"([^"]+)"', content):
            library_path = Path(raw_path.replace("\\\\", "\\"))
            if library_path.exists() and library_path not in libraries:
                libraries.append(library_path)
        return libraries

    def _parse_manifest(self, manifest_path: Path) -> SteamGameButtonDefinition | None:
        try:
            content = manifest_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return None
        app_id = _extract_vdf_value(content, "appid")
        name = _extract_vdf_value(content, "name")
        if not app_id or not name:
            return None
        return SteamGameButtonDefinition(
            app_id=app_id,
            name=name,
            icon=self._resolve_icon(app_id),
            target=f"steam://rungameid/{app_id}",
        )

    def _resolve_icon(self, app_id: str) -> str:
        librarycache_dir = self._steam_root / "appcache" / "librarycache" / app_id
        candidates: list[Path] = []
        if librarycache_dir.exists():
            candidates.extend(
                sorted(
                    path
                    for path in librarycache_dir.iterdir()
                    if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
                )
            )
        if candidates:
            return str(candidates[0])
        return "asset:stream_deck_steam.svg"


def _extract_vdf_value(content: str, key: str) -> str:
    match = re.search(rf'"{re.escape(key)}"\s+"([^"]+)"', content)
    if match is None:
        return ""
    return match.group(1).strip()
