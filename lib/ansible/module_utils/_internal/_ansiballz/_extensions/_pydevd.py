"""
Remote debugging support for AnsiballZ modules with pydevd.

To use with PyCharm:

1) Choose an available port for PyCharm to listen on (e.g. 5678).
2) Create a Python Debug Server using that port.
3) Start the Python Debug Server.
4) Ensure the correct version of `pydevd-pycharm` is installed for the interpreter(s) which will run the code being debugged.
5) Configure Ansible with the `_ANSIBALLZ_DEBUGGER_CONFIG` option.
   See `Options` below for the structure of the debugger configuration.
   Example configuration using an environment variable:
     export _ANSIBLE_ANSIBALLZ_DEBUGGER_CONFIG='{"ansiballz_extension": "_pydevd", "port": 5978, "module": "pydevd_pycharm", "settrace": {"suspend": false}}'
6) Set any desired breakpoints.
7) Run Ansible commands.
"""

from __future__ import annotations

import dataclasses
import importlib

import typing as t

from . import _debugger


@dataclasses.dataclass(frozen=True)
class Options(_debugger.Options):
    """Debugger options for pydevd and its derivatives."""

    module: str = 'pydevd'
    """The Python module which will be imported and which provides the `settrace` method."""
    settrace: dict[str, object] = dataclasses.field(default_factory=dict)
    """The options to pass to the `{module}.settrace` method."""

def run(args: dict[str, t.Any]) -> None:  # pragma: nocover
    """Enable remote debugging for pydevd."""

    options = Options(**args)

    _debugger.setup_pydevd_source_mapping(options)

    debugging_module = importlib.import_module(options.module)
    debugging_module.settrace(host=options.host, port=options.port, **options.settrace)

    pass  # when suspend is True, execution pauses here -- it's also a convenient place to put a breakpoint
