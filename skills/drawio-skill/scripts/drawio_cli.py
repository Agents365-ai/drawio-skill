#!/usr/bin/env python3
"""Locate the draw.io desktop CLI for native export.

The executable name depends on the platform: Homebrew and Linux packages
install `drawio` (no dot), while the Windows installer ships `draw.io.exe`
(with the dot) and macOS also keeps `draw.io` inside the app bundle.

Callers must run the absolute path this module returns. A bare `drawio` fails
on Windows twice over: no such file exists there, and even a `.cmd` shim on
PATH is not launched, because `subprocess` on Windows uses `CreateProcess`,
which only appends `.exe`.

Usage:
    from drawio_cli import resolve_drawio
    exe = resolve_drawio()
    if not exe:
        sys.exit("error: draw.io CLI not found on PATH ...")
"""
import os
import shutil

# PATH names to try, in order. `drawio` is Homebrew/Linux, `draw.io` Windows.
NAMES = ("drawio", "draw.io")

MACOS_APP = "/Applications/draw.io.app/Contents/MacOS/draw.io"

# Windows installers: machine-wide, 32-bit, and per-user. Each entry is
# (environment variable, path components under it).
WIN_DIRS = (
    ("ProgramFiles", ("draw.io", "draw.io.exe")),
    ("ProgramFiles(x86)", ("draw.io", "draw.io.exe")),
    ("LOCALAPPDATA", ("Programs", "draw.io", "draw.io.exe")),
)


def _on_path():
    """Absolute path of the first CLI name found on PATH, or None."""
    for name in NAMES:
        found = shutil.which(name)
        if found:
            return found
    return None


def _install_paths():
    """Default install locations, for a CLI that is installed but not on PATH."""
    paths = [MACOS_APP]
    for env, parts in WIN_DIRS:
        base = os.environ.get(env)
        if base:
            paths.append(os.path.join(base, *parts))
    return paths


def resolve_drawio():
    """Absolute path to the draw.io CLI, or None when it is not installed.

    Tries both PATH names first, then the macOS app bundle and the Windows
    default install directories. Never returns a bare command name.
    """
    found = _on_path()
    if found:
        return found
    for path in _install_paths():
        if os.path.isfile(path):
            return path
    return None
