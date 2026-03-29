# Prox Deck

Prox Deck is a PySide6 desktop application for the Corsair Xeneon Edge.

Current release target: `v1.0.0-alpha`

The application is intended as a dedicated second-screen dashboard that runs on the Edge in a widget-based fullscreen runtime, while keeping runtime and management responsibilities structurally separated.

## Current Status

This repository currently contains the first production-oriented foundation:

- layered application structure under `src/proxdeck`
- domain models for screens, layouts, placements, widget definitions, and capabilities
- layout and availability policies
- application services for runtime startup and widget management
- JSON-based local screen persistence
- runtime shell with a dashboard grid and screen selector
- management shell for adding, removing, and configuring widget instances

## Project Structure

```text
src/proxdeck/
  application/
  bootstrap/
  domain/
  infrastructure/
  presentation/
docs/
tests/
widgets/
installable_widgets/
```

The architecture follows the project rules in the docs:

- `docs/edge_dashboard_product_requirements.txt`
- `docs/edge_dashboard_technical_architecture.txt`
- `docs/CodeStyle.md`

## Requirements

- Python 3.11+
- PySide6

## Run

Create or activate a virtual environment, install dependencies, then start the app:

```bash
pip install -e .
python -m proxdeck
```

The current runtime target detector uses environment variables as a safe placeholder instead of real monitor enumeration.

Optional runtime target override:

```bash
set PROXDECK_DETECTED_MONITOR=XeneonEdge
set PROXDECK_TARGET_WIDTH=1920
set PROXDECK_TARGET_HEIGHT=1080
set PROXDECK_TARGET_X=0
set PROXDECK_TARGET_Y=0
python -m proxdeck
```

If no target monitor is detected, the app stays in a safe windowed fallback.

## Test

```bash
python -m pytest -q -p no:cacheprovider
```

## Installer Build

Windows release packaging is documented in `docs/release.md`.

## Notes

- `widgets/` is reserved for built-in widgets.
- `installable_widgets/` is reserved for future installable widget discovery.
- `Developing` is intentionally present as a non-active `Soon` screen in v1 foundation work.
- Widget shop, API-key activation, and full permission management are intentionally out of scope for the current slice.
