"""Fakeable filesystem and command-runner seams.

Real implementations call the actual OS; tests inject in-memory fakes so
detection and write logic can be exercised hermetically with no risk of
touching the user's home directory.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Protocol


class FilesystemSeam(Protocol):
    def home(self) -> Path: ...
    def exists(self, path: Path) -> bool: ...
    def is_dir(self, path: Path) -> bool: ...
    def is_file(self, path: Path) -> bool: ...
    def read_text(self, path: Path) -> str: ...
    def write_text(self, path: Path, content: str) -> None: ...
    def mkdir(self, path: Path) -> None: ...
    def list_writes(self) -> dict[Path, str]: ...


class CommandRunnerSeam(Protocol):
    def which(self, executable: str) -> str | None: ...


class RealFilesystem:
    def home(self) -> Path:
        return Path.home()

    def exists(self, path: Path) -> bool:
        return path.exists()

    def is_dir(self, path: Path) -> bool:
        return path.is_dir()

    def is_file(self, path: Path) -> bool:
        return path.is_file()

    def read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def mkdir(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)

    def list_writes(self) -> dict[Path, str]:
        return {}


class RealCommandRunner:
    def which(self, executable: str) -> str | None:
        return shutil.which(executable)


class FakeFilesystem:
    """In-memory filesystem for tests. Stores text content by absolute path."""

    def __init__(self, home: Path, files: dict[Path, str] | None = None) -> None:
        self._home = home
        self._files: dict[Path, str] = {Path(k): v for k, v in (files or {}).items()}
        self._dirs: set[Path] = {home}
        for p in self._files:
            for parent in p.parents:
                self._dirs.add(parent)

    def home(self) -> Path:
        return self._home

    def exists(self, path: Path) -> bool:
        return path in self._files or path in self._dirs

    def is_dir(self, path: Path) -> bool:
        return path in self._dirs and path not in self._files

    def is_file(self, path: Path) -> bool:
        return path in self._files

    def read_text(self, path: Path) -> str:
        if path not in self._files:
            raise FileNotFoundError(str(path))
        return self._files[path]

    def write_text(self, path: Path, content: str) -> None:
        self._files[path] = content
        for parent in path.parents:
            self._dirs.add(parent)

    def mkdir(self, path: Path) -> None:
        self._dirs.add(path)
        for parent in path.parents:
            self._dirs.add(parent)

    def list_writes(self) -> dict[Path, str]:
        return dict(self._files)


class FakeCommandRunner:
    def __init__(self, available: dict[str, str] | None = None) -> None:
        self._available = dict(available or {})

    def which(self, executable: str) -> str | None:
        return self._available.get(executable)


def is_tty(stream: object | None = None) -> bool:
    """True only if attached to a real terminal. Used to gate non-interactive safety."""
    import sys

    target = stream if stream is not None else sys.stdin
    isatty = getattr(target, "isatty", None)
    if isatty is None:
        return False
    try:
        return bool(isatty()) and os.environ.get("LANGUAGE_TUTOR_NO_TTY") != "1"
    except Exception:
        return False
