# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import signal
import typing as t

from unittest.mock import MagicMock

import pytest

from ansible._internal import _rpc_host
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.inventory.host import Host
from ansible.playbook.play_context import PlayContext
from ansible.playbook.task import Task
from ansible.plugins import strategy
from ansible.utils.multiprocessing import context as multiprocessing_context

from units.mock.loader import DictDataLoader


class _QuickWorker(multiprocessing_context.Process):  # type: ignore[name-defined]
    """Stands in for WorkerProcess: a real fork whose child exits at once."""

    def __init__(self, **_kwargs) -> None:
        super().__init__()

    def run(self) -> None:
        pass


class _SignaledWorker(_QuickWorker):
    """A worker that receives a SIGINT before it has installed its own signal handlers, which WorkerProcess.run() does first."""

    def run(self) -> None:
        signal.raise_signal(signal.SIGINT)


@pytest.fixture
def strategy_base() -> t.Iterator[strategy.StrategyBase]:
    """A strategy with one worker slot; the test's signal handlers are restored afterward."""
    handlers = {signum: signal.getsignal(signum) for signum in (signal.SIGINT, signal.SIGTERM)}

    tqm = TaskQueueManager(inventory=MagicMock(), variable_manager=MagicMock(), loader=DictDataLoader({}), passwords={})
    tqm._initialize_processes(1)
    strategy_base = strategy.StrategyBase(tqm)

    try:
        yield strategy_base
    finally:
        strategy_base.cleanup()
        tqm.cleanup()

        for signum, handler in handlers.items():
            signal.signal(signum, handler)


def test_sigint_while_replacing_a_finished_worker(strategy_base: strategy.StrategyBase, monkeypatch: pytest.MonkeyPatch) -> None:
    """A SIGINT that arrives while a finished worker's replacement is made raises KeyboardInterrupt, and the slot holds the open worker until then."""
    finished = _QuickWorker()
    finished.start()
    finished.join()
    strategy_base._workers[0] = finished
    in_slot = []

    def make_worker(**kwargs) -> _QuickWorker:
        in_slot.extend(strategy_base._workers)  # the results thread answers a worker's prompt through its slot
        signal.raise_signal(signal.SIGINT)
        return _QuickWorker(**kwargs)

    monkeypatch.setattr(strategy, 'WorkerProcess', make_worker)

    with pytest.raises(KeyboardInterrupt):
        strategy_base._queue_task(Host('host1'), Task(), {}, PlayContext())

    assert in_slot == [finished]


def test_sigint_stops_a_worker_before_it_installs_its_handlers(strategy_base: strategy.StrategyBase, monkeypatch: pytest.MonkeyPatch) -> None:
    """A worker forked while a SIGINT would be deferred dies of a SIGINT that arrives before it has its own handlers, instead of going on to run its task."""
    monkeypatch.setattr(strategy, 'WorkerProcess', _SignaledWorker)

    strategy_base._queue_task(Host('host1'), Task(), {}, PlayContext())

    worker = strategy_base._workers[0]
    worker.join()

    assert worker.exitcode == -signal.SIGINT


@pytest.mark.parametrize('method', ('_process_pending_results', '_wait_on_pending_results'))
def test_sigint_whose_interrupt_was_lost(strategy_base: strategy.StrategyBase, method: str) -> None:
    """A SIGINT whose KeyboardInterrupt was caught raises one when results are next handled, instead of failing the run on the worker it stopped."""
    stopped = _SignaledWorker()
    stopped.start()
    stopped.join()
    strategy_base._workers[0] = stopped
    strategy_base._pending_results = 1

    # an RPC run on the main thread catches the KeyboardInterrupt
    _rpc_host.AsyncRPCOperation(impl=signal.raise_signal, args=(signal.SIGINT,), kwargs={}).dispatch()

    with pytest.raises(KeyboardInterrupt):
        getattr(strategy_base, method)(MagicMock())
