#!/usr/bin/env python3
"""Project Manager - Desktop application for viewing and navigating programming projects."""

import sys


def main():
    """Application entry point."""
    from src.app import ProjectManagerApp

    app = ProjectManagerApp()

    try:
        sys.exit(app.run())
    finally:
        app.cleanup()


if __name__ == '__main__':
    main()
