from __future__ import annotations

import functools
import typing as t

from .. import _rpc_host
from .._plugins import _strategy

if t.TYPE_CHECKING:
    from .. import _task


def dispatch_to_strategy_result_thread(func: t.Callable) -> t.Callable:
    """Decorator to force a function to be run serially under the strategy result thread."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        request = _rpc_host.AsyncRPCOperation(impl=func, args=args, kwargs=kwargs)

        _strategy.StrategyContext.current().strategy._rpc_queue.put(request)

        request.event.wait()

        return request.result

    return wrapper


class InventoryRPC(_rpc_host.AutoRegisterRPC):
    """
    RPC server implementation for managing inventory from a worker.
    Also used as the type annotation for the RPC client on the worker.
    """

    @staticmethod
    @dispatch_to_strategy_result_thread
    def add_host(host_info: _task.AddHost) -> bool:
        """Add a host to inventory."""
        ctx = _strategy.StrategyContext.current()
        changed = ctx.tqm._inventory.add_dynamic_host(host_info)

        if changed and host_info.host_name not in ctx.strategy._hosts_cache_all:
            ctx.strategy._hosts_cache_all.append(host_info.host_name)

        return changed

    @staticmethod
    @dispatch_to_strategy_result_thread
    def add_group(host_name: str, group_info: _task.AddGroup) -> bool:
        """Add a group to inventory."""
        ctx = _strategy.StrategyContext.current()

        return ctx.tqm._inventory.add_dynamic_group(host_name, group_info)
