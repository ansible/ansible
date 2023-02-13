"""Diff parsing functions and classes."""
from __future__ import annotations

import re
import textwrap
import traceback
import typing as t

from .util import (
    ApplicationError,
)


def parse_diff(lines: list[str]) -> list[FileDiff]:
    """Parse the given diff lines and return a list of FileDiff objects representing the changes of each file."""
    return DiffParser(lines).files


class FileDiff:
    """Parsed diff for a single file."""

    def __init__(self, old_path: str, new_path: str) -> None:
        self.old = DiffSide(old_path, new=False)
        self.new = DiffSide(new_path, new=True)
        self.headers: list[str] = []
        self.binary = False

    def append_header(self, line: str) -> None:
        """Append the given line to the list of headers for this file."""
        self.headers.append(line)

    @property
    def is_complete(self) -> bool:
        """True if the diff is complete, otherwise False."""
        return self.old.is_complete and self.new.is_complete


class DiffSide:
    """Parsed diff for a single 'side' of a single file."""

    def __init__(self, path: str, new: bool) -> None:
        self.path = path
        self.new = new
        self.prefix = '+' if self.new else '-'
        self.eof_newline = True
        self.exists = True

        self.lines: list[tuple[int, str]] = []
        self.lines_and_context: list[tuple[int, str]] = []
        self.ranges: list[tuple[int, int]] = []

        self._next_line_number = 0
        self._lines_remaining = 0
        self._range_start = 0

    def set_start(self, line_start: int, line_count: int) -> None:
        """Set the starting line and line count."""
        self._next_line_number = line_start
        self._lines_remaining = line_count
        self._range_start = 0

    def append(self, line: str) -> None:
        """Append the given line."""
        if self._lines_remaining <= 0:
            raise Exception('Diff range overflow.')

        entry = self._next_line_number, line

        if line.startswith(' '):
            pass
        elif line.startswith(self.prefix):
            self.lines.append(entry)

            if not self._range_start:
                self._range_start = self._next_line_number
        else:
            raise Exception('Unexpected diff content prefix.')

        self.lines_and_context.append(entry)

        self._lines_remaining -= 1

        if self._range_start:
            if self.is_complete:
                range_end = self._next_line_number
            elif line.startswith(' '):
                range_end = self._next_line_number - 1
            else:
                range_end = 0

            if range_end:
                self.ranges.append((self._range_start, range_end))
                self._range_start = 0

        self._next_line_number += 1

    @property
    def is_complete(self) -> bool:
        """True if the diff is complete, otherwise False."""
        return self._lines_remaining == 0

    def format_lines(self, context: bool = True) -> list[str]:
        """Format the diff and return a list of lines, optionally including context."""
        if context:
            lines = self.lines_and_context
        else:
            lines = self.lines

        return ['%s:%4d %s' % (self.path, line[0], line[1]) for line in lines]


class DiffParser:
    """Parse diff lines."""

    def __init__(self, lines: list[str]) -> None:
        self.lines = lines
        self.files: list[FileDiff] = []

        self.action = self.process_start
        self.line_number = 0
        self.previous_line: t.Optional[str] = None
        self.line: t.Optional[str] = None
        self.file: t.Optional[FileDiff] = None

        for self.line in self.lines:
            self.line_number += 1

            try:
                self.action()
            except Exception as ex:
                message = textwrap.dedent('''
                %s

                     Line: %d
                 Previous: %s
                  Current: %s
                %s
                ''').strip() % (
                    ex,
                    self.line_number,
                    self.previous_line or '',
                    self.line or '',
                    traceback.format_exc(),
                )

                raise ApplicationError(message.strip())

            self.previous_line = self.line

        self.complete_file()

    def process_start(self) -> None:
        """Process a diff start line."""
        self.complete_file()

        match = re.search(r'^diff --git "?(?:a/)?(?P<old_path>.*)"? "?(?:b/)?(?P<new_path>.*)"?$', self.line)

        if not match:
            raise Exception('Unexpected diff start line.')

        self.file = FileDiff(match.group('old_path'), match.group('new_path'))
        self.action = self.process_continue

    def process_range(self) -> None:
        """Process a diff range line."""
        match = re.search(r'^@@ -((?P<old_start>[0-9]+),)?(?P<old_count>[0-9]+) \+((?P<new_start>[0-9]+),)?(?P<new_count>[0-9]+) @@', self.line)

        if not match:
            raise Exception('Unexpected diff range line.')

        self.file.old.set_start(int(match.group('old_start') or 1), int(match.group('old_count')))
        self.file.new.set_start(int(match.group('new_start') or 1), int(match.group('new_count')))
        self.action = self.process_content

    def process_continue(self) -> None:
        """Process a diff start, range or header line."""
        if self.line.startswith('diff '):
            self.process_start()
        elif self.line.startswith('@@ '):
            self.process_range()
        else:
            self.process_header()

    def process_header(self) -> None:
        """Process a diff header line."""
        if self.line.startswith('Binary files '):
            self.file.binary = True
        elif self.line == '--- /dev/null':
            self.file.old.exists = False
        elif self.line == '+++ /dev/null':
            self.file.new.exists = False
        else:
            self.file.append_header(self.line)

    def process_content(self) -> None:
        """Process a diff content line."""
        if self.line == r'\ No newline at end of file':
            if self.previous_line.startswith(' '):
                self.file.old.eof_newline = False
                self.file.new.eof_newline = False
            elif self.previous_line.startswith('-'):
                self.file.old.eof_newline = False
            elif self.previous_line.startswith('+'):
                self.file.new.eof_newline = False
            else:
                raise Exception('Unexpected previous diff content line.')

            return

        if self.file.is_complete:
            self.process_continue()
            return

        if self.line.startswith(' '):
            self.file.old.append(self.line)
            self.file.new.append(self.line)
        elif self.line.startswith('-'):
            self.file.old.append(self.line)
        elif self.line.startswith('+'):
            self.file.new.append(self.line)
        else:
            raise Exception('Unexpected diff content line.')

    def complete_file(self) -> None:
        """Complete processing of the current file, if any."""
        if not self.file:
            return

        self.files.append(self.file)
