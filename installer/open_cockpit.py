"""Open the local Cockpit after the background service becomes healthy."""

from __future__ import annotations

import os
import webbrowser

from .background_service import wait_for_health
from .service_config import get_node_role, get_service_port


def main() -> int:
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if get_node_role(root_dir) != "master":
        return 0
    port = get_service_port(root_dir)
    if wait_for_health(port, timeout=120):
        webbrowser.open(f"http://127.0.0.1:{port}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
