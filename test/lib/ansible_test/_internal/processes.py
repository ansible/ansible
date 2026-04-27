"""Wrappers around `ps` for querying running processes."""

from __future__ import annotations

import collections
import dataclasses
import os
import pathlib
import shlex

from ansible_test._internal.util import raw_command


@dataclasses.dataclass(frozen=True)
class ProcessData:
    """Data about a running process."""

    pid: int
    ppid: int
    command: str


@dataclasses.dataclass(frozen=True)
class Process:
    """A process in the process tree."""

    pid: int
    command: str
    parent: Process | None = None
    children: tuple[Process, ...] = dataclasses.field(default_factory=tuple)

    @property
    def args(self) -> list[str]:
        """The list of arguments that make up `command`."""
        return shlex.split(self.command)

    @property
    def path(self) -> pathlib.Path:
        """The path to the process."""
        return pathlib.Path(self.args[0])


def get_process_data(pids: list[int] | None = None) -> list[ProcessData]:
    """Return a list of running processes."""
    if pids:
        args = ['-p', ','.join(map(str, pids))]
    else:
        args = ['-A']

    lines = raw_command(['ps'] + args + ['-o', 'pid,ppid,command'], capture=True)[0].splitlines()[1:]
    processes = [ProcessData(pid=int(pid), ppid=int(ppid), command=command) for pid, ppid, command in (line.split(maxsplit=2) for line in lines)]

    return processes


def get_process_tree() -> dict[int, Process]:
    """Return the process tree."""
    processes = get_process_data()
    pid_to_process: dict[int, Process] = {}
    pid_to_children: dict[int, list[Process]] = collections.defaultdict(list)

    for data in processes:
        pid_to_process[data.pid] = process = Process(pid=data.pid, command=data.command)

        if data.ppid:
            pid_to_children[data.ppid].append(process)

    for data in processes:
        pid_to_process[data.pid] = dataclasses.replace(
            pid_to_process[data.pid],
            parent=pid_to_process.get(data.ppid),
            children=tuple(pid_to_children[data.pid]),
        )

    return pid_to_process


def get_current_process() -> Process:
    """Return the current process along with its ancestors and descendants."""
    return get_process_tree()[os.getpid()]
