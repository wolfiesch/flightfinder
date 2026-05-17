"""UI resource utilities for MCP Apps integration.

This module provides functions for loading pre-built HTML bundles
and creating MCP-compatible UI resources for interactive UIs.
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Path to the UI dist directory (relative to this file)
UI_DIST_PATH = Path(__file__).parent.parent.parent / "ui" / "dist"

# MIME type for MCP Apps UI resources
RESOURCE_MIME_TYPE = "text/html;profile=mcp-app"

# View names mapped to their HTML bundle filenames
UI_VIEWS = {
    "flights": "flights.html",
    "roundtrip": "roundtrip.html",
    "hotels": "hotels.html",
    "trip": "trip.html",
    "locations": "locations.html",
}


def get_ui_dist_path() -> Path:
    """Get the path to the UI dist directory.

    Returns:
        Path to the ui/dist directory.

    Raises:
        FileNotFoundError: If the dist directory doesn't exist.
    """
    if not UI_DIST_PATH.exists():
        raise FileNotFoundError(
            f"UI dist directory not found at {UI_DIST_PATH}. "
            "Run 'cd ui && ./scripts/build-all.sh' to build the UI."
        )
    return UI_DIST_PATH


def load_ui_bundle(view: str, data: dict[str, Any]) -> str:
    """Load an HTML bundle and inject data.

    The HTML bundles contain a <!--INJECT_DATA--> placeholder that
    gets replaced with a script tag setting window.__FLIGHTFINDER_DATA__.

    Args:
        view: The view name (e.g., "flights", "hotels")
        data: The data to inject into the HTML

    Returns:
        The HTML content with data injected.

    Raises:
        ValueError: If the view name is invalid.
        FileNotFoundError: If the HTML bundle doesn't exist.
    """
    if view not in UI_VIEWS:
        raise ValueError(f"Invalid view '{view}'. Valid views: {list(UI_VIEWS.keys())}")

    dist_path = get_ui_dist_path()
    html_path = dist_path / UI_VIEWS[view]

    if not html_path.exists():
        raise FileNotFoundError(
            f"UI bundle not found at {html_path}. "
            "Run 'cd ui && ./scripts/build-all.sh' to build the UI."
        )

    html = html_path.read_text(encoding="utf-8")

    # Inject data as a script tag
    # Use JSON.dumps with ensure_ascii=False for proper Unicode handling
    data_script = (
        f"<script>window.__FLIGHTFINDER_DATA__ = {json.dumps(data, default=str)};</script>"
    )

    # Replace the placeholder or insert before closing head tag
    if "<!--INJECT_DATA-->" in html:
        html = html.replace("<!--INJECT_DATA-->", data_script)
    elif "</head>" in html:
        html = html.replace("</head>", f"{data_script}</head>")
    else:
        # Fallback: insert at the beginning of body
        html = html.replace("<body>", f"<body>{data_script}")

    return html


def get_resource_uri(view: str) -> str:
    """Get the MCP resource URI for a view.

    Args:
        view: The view name (e.g., "flights", "hotels")

    Returns:
        The resource URI (e.g., "ui://flightfinder/flights")
    """
    return f"ui://flightfinder/{view}"


def create_ui_resource(view: str, data: dict[str, Any]) -> dict[str, Any]:
    """Create an MCP UI resource response.

    This creates a resource dict that can be used in MCP list_resources
    or read_resource responses.

    Args:
        view: The view name (e.g., "flights", "hotels")
        data: The data to inject into the HTML

    Returns:
        A dict with uri, mimeType, and text fields.
    """
    return {
        "uri": get_resource_uri(view),
        "mimeType": RESOURCE_MIME_TYPE,
        "text": load_ui_bundle(view, data),
    }


def is_ui_available() -> bool:
    """Check if the UI bundles are available.

    Returns:
        True if at least one UI bundle exists.
    """
    try:
        dist_path = get_ui_dist_path()
        return any((dist_path / f).exists() for f in UI_VIEWS.values())
    except FileNotFoundError:
        return False


def list_available_views() -> list[str]:
    """List all available UI views that have been built.

    Returns:
        List of view names that have built HTML bundles.
    """
    try:
        dist_path = get_ui_dist_path()
        return [view for view, filename in UI_VIEWS.items() if (dist_path / filename).exists()]
    except FileNotFoundError:
        return []
