#!/usr/bin/env python3
"""PyInstaller entry point that handles package imports correctly."""

import sys

# Patch mimetypes BEFORE any other imports to avoid App Sandbox issues
# This must happen before markitdown or any dependency imports mimetypes
if getattr(sys, "frozen", False):
    import mimetypes

    # Clear the list of known files so mimetypes won't try to read system files
    # App Sandbox blocks access to /etc/apache2/mime.types
    mimetypes.knownfiles = []
    mimetypes.init(files=[])

from pathlib import Path


def main():
    """Launch XtoMarkdown application."""
    # Import here to ensure proper module resolution
    from xtomarkdown.app import main as app_main

    app_main()


if __name__ == "__main__":
    main()
