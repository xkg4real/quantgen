"""Entry point of the packaged native desktop app (OS-P0-b). PyInstaller starts this file.

The same as `quantgen-desktop` from pyproject.toml ([project.gui-scripts], quantgen_desktop.app:main),
with multiprocessing's frozen-app support first, so worker processes start correctly in a packaged app.
"""
import multiprocessing
import sys


def run() -> int:
    multiprocessing.freeze_support()
    from quantgen_desktop.app import main
    return main()


if __name__ == "__main__":
    sys.exit(run())
