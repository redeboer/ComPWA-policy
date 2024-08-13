"""File operations."""

from __future__ import annotations

import io
import sys
from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from copy import copy
from pathlib import Path
from textwrap import indent
from typing import IO, TYPE_CHECKING

from compwa_policy.errors import PrecommitError

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self
if TYPE_CHECKING:
    from types import TracebackType


class ModifiableFile(AbstractContextManager, ABC):
    @property
    @abstractmethod
    def changelog(self) -> list[str]: ...
    @abstractmethod
    def dump(self, target: IO[str] | Path | str | None = None) -> None: ...
    @abstractmethod
    def dumps(self) -> str: ...
    @classmethod
    @abstractmethod
    def load(cls, source: IO[str] | Path | str | None = None) -> Self: ...


class LineEditor(ModifiableFile):
    def __init__(self, source: IO[str] | Path | str | None = None) -> None:
        self.__is_in_context = False
        self.__source = source
        self.__changelog: list[str] = []
        if source is None:
            self.__original_lines: list[str] | None = None
        elif isinstance(source, io.TextIOBase):
            self.__original_lines = source.readlines()
        elif isinstance(source, Path):
            if source.exists():
                with open(source) as stream:
                    self.__original_lines = stream.readlines()
            else:
                self.__original_lines = None
        self.__lines = copy(self.__original_lines)

    @classmethod
    def load(cls, source: IO[str] | Path | str | None = None) -> Self:
        return cls(source)

    def __enter__(self) -> Self:
        self.__is_in_context = True
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        if exc_type is not None and not issubclass(exc_type, PrecommitError):
            return False
        if self.__lines == self.__original_lines:
            return True
        self.dump(self.__source)
        msg = f"The following modifications were made to {self.__source}"
        msg += ":\n"
        msg += indent("\n".join(self.__changelog), prefix="  - ")
        raise PrecommitError(msg)

    def dump(self, target: IO[str] | Path | str | None = None) -> None:
        if self.__lines is None:
            msg = "The original source contains no lines and no new lines were added"
            raise ValueError(msg)
        if target is None:
            target = self.__source
        if isinstance(target, io.TextIOBase):
            current_position = target.tell()
            target.seek(0)
            target.writelines(self.formatted_lines)
            target.seek(current_position)
        elif isinstance(target, Path):
            with open(target, "w") as stream:
                stream.writelines(self.formatted_lines)
        else:
            msg = f"Target of type {type(target).__name__} is not supported"
            raise TypeError(msg)

    def dumps(self) -> str:
        if self.__lines is None:
            msg = "The original source contains no lines and no new lines were added"
            raise ValueError(msg)
        return "\n".join(self.formatted_lines)

    @property
    def formatted_lines(self) -> list[str]:
        if self.__lines is None:
            return []
        lines = [line.rstrip(" \t") for line in self.__lines]
        while not lines[-1].strip():
            lines.pop()
        return lines

    @property
    def changelog(self) -> list[str]:
        self.__assert_is_in_context()
        return self.__changelog

    def append_safe(self, line: str) -> None:
        self.__assert_is_in_context()
        if self.__lines is None:
            self.__lines = []
        if line in {s.strip() for s in self.__lines}:
            return
        self.__lines.append(line)
        msg = f'Appended line "{line}"'
        if isinstance(self.__source, Path):
            msg += f" to {self.__source}"
        self.__changelog.append(msg)

    def __assert_is_in_context(self) -> None:
        if not self.__is_in_context:
            msg = "Modifications can only be made within a context"
            raise RuntimeError(msg)
