from pathlib import Path
import shutil
import uuid

from proxdeck.bootstrap import settings


def test_build_app_paths_uses_project_storage_when_not_frozen(monkeypatch) -> None:
    temp_root = build_temp_root()
    monkeypatch.setattr(settings.sys, "frozen", False, raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.delenv("APPDATA", raising=False)

    try:
        paths = settings.build_app_paths(temp_root)

        assert paths.storage_root == temp_root / ".proxdeck"
        assert paths.screen_state_path == temp_root / ".proxdeck" / "screens.json"
        assert paths.builtin_widgets_root == temp_root / "widgets"
        assert paths.bundled_installable_widgets_root == temp_root / "installable_widgets"
        assert paths.user_installable_widgets_root == temp_root / ".proxdeck" / "installable_widgets"
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def test_build_app_paths_uses_meipass_and_localappdata_when_frozen(monkeypatch) -> None:
    temp_root = build_temp_root()
    bundle_root = temp_root / "bundle"
    storage_root = temp_root / "local-app-data"
    bundle_root.mkdir()
    storage_root.mkdir()
    monkeypatch.setattr(settings.sys, "frozen", True, raising=False)
    monkeypatch.setattr(settings.sys, "_MEIPASS", str(bundle_root), raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(storage_root))
    monkeypatch.delenv("APPDATA", raising=False)

    try:
        paths = settings.build_app_paths(temp_root / "ignored-project-root")

        assert paths.storage_root == storage_root / "ProxDeck"
        assert paths.builtin_widgets_root == bundle_root / "widgets"
        assert paths.bundled_installable_widgets_root == bundle_root / "installable_widgets"
        assert paths.user_installable_widgets_root == storage_root / "ProxDeck" / "installable_widgets"
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def test_resolve_storage_root_falls_back_to_appdata_when_localappdata_is_missing(monkeypatch) -> None:
    temp_root = build_temp_root()
    app_data = temp_root / "roaming"
    app_data.mkdir()
    monkeypatch.setattr(settings.sys, "frozen", True, raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setenv("APPDATA", str(app_data))

    try:
        resolved = settings.resolve_storage_root(Path("unused"))

        assert resolved == app_data / "ProxDeck"
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def build_temp_root() -> Path:
    root = Path.cwd() / ".test-artifacts" / f"bootstrap-settings-{uuid.uuid4().hex[:8]}"
    root.mkdir(parents=True, exist_ok=False)
    return root
