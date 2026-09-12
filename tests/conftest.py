"""Workspace-local test scratch space compatible with Windows restricted tokens."""

import os
from pathlib import Path
import shutil
import uuid

import pytest


@pytest.fixture
def tmp_path(request):
    # Python's Windows mode=0o700 installs a private DACL that can exclude
    # restricted tokens. Inherit the existing workspace ACL instead; do not
    # alter OS permissions or patch pytest/Python globally.
    if os.name != "nt":
        yield request.getfixturevalue("tmp_path_factory").mktemp(request.node.name)
        return

    workspace = Path(__file__).resolve().parents[1]
    scratch = workspace / "results" / "pytest-scratch"
    if scratch.resolve() != scratch:
        raise RuntimeError("Test scratch directory must not redirect outside its path")
    scratch.mkdir(parents=True, exist_ok=True)
    path = scratch / uuid.uuid4().hex
    path.mkdir()  # Default mode: inherit the parent Windows ACL.
    try:
        yield path
    finally:
        # Delete only this fixture's fresh directory, never a supplied basetemp.
        if path.resolve().parent != scratch or path.is_symlink():
            raise RuntimeError("Refusing to clean a redirected test directory")
        shutil.rmtree(path)
