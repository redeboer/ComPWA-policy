"""File operations."""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from typing import IO, TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self


class ModifiableFile(AbstractContextManager, ABC):
    @property
    @abstractmethod
    def changelog(self) -> list[str]: ...
    @abstractmethod
    def dump(self, target: IO | Path | str | None = None) -> None: ...
    @abstractmethod
    def dumps(self) -> str: ...
    @classmethod
    @abstractmethod
    def load(cls, source: IO | Path | str | None = None) -> Self: ...
