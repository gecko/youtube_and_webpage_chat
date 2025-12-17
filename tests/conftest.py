import os
import sys


def pytest_configure():
    # Ensure the `src` directory is on sys.path so imports like `app.controller`
    # resolve to the modules under src/ during test collection.
    repo_root = os.path.dirname(os.path.dirname(__file__))
    src_path = os.path.join(repo_root, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
