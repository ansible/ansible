from __future__ import annotations

import collections.abc as c
import contextlib
import errno
import os
import sys

import pytest

from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play_context import PlayContext
from ansible.playbook.task import Task
from ansible.plugins.strategy import StrategyBase
from ansible.vars.manager import VariableManager

from units.mock.loader import DictDataLoader


@pytest.fixture
def strategy() -> c.Iterator[StrategyBase]:
    loader = DictDataLoader({})
    inventory = InventoryManager(loader=loader, sources='host01,')
    tqm = TaskQueueManager(
        inventory=inventory,
        variable_manager=VariableManager(loader=loader, inventory=inventory),
        loader=loader,
        passwords={},
        forks=1,
    )
    tqm._initialize_processes(1)
    strategy = StrategyBase(tqm)

    yield strategy

    strategy.cleanup()
    tqm.cleanup()


def queue_task(strategy: StrategyBase) -> None:
    strategy._queue_task(strategy._inventory.get_host('host01'), Task.load(dict(command='sleep 1')), {}, PlayContext())


def test_queue_task_raises_when_stdout_reader_has_exited(strategy: StrategyBase, monkeypatch: pytest.MonkeyPatch) -> None:
    """_queue_task raises the BrokenPipeError from starting a worker after the reader of stdout has exited."""
    read_fd, write_fd = os.pipe()
    os.close(read_fd)
    dead_stdout = os.fdopen(write_fd, 'w')
    dead_stdout.write('output nobody will read')

    try:
        with monkeypatch.context() as patched:
            patched.setattr(sys, 'stdout', dead_stdout)

            with pytest.raises(BrokenPipeError):
                queue_task(strategy)
    finally:
        # closing retries the flush into the dead pipe
        with contextlib.suppress(BrokenPipeError):
            dead_stdout.close()


def test_queue_task_raises_when_fork_fails(strategy: StrategyBase, monkeypatch: pytest.MonkeyPatch) -> None:
    """_queue_task raises the BlockingIOError from starting a worker when fork fails with EAGAIN."""
    def fork() -> int:
        raise BlockingIOError(errno.EAGAIN, os.strerror(errno.EAGAIN))

    monkeypatch.setattr(os, 'fork', fork)

    with pytest.raises(BlockingIOError):
        queue_task(strategy)
