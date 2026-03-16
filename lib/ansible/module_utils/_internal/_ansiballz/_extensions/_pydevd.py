"""
Remote debugging support for AnsiballZ modules.

To use with PyCharm:

1) Choose an available port for PyCharm to listen on (e.g. 5678).
2) Create a Python Debug Server using that port.
3) Start the Python Debug Server.
4) Ensure the correct version of `pydevd-pycharm` is installed for the interpreter(s) which will run the code being debugged.
5) Configure Ansible with the `_ANSIBALLZ_PYDEVD_CONFIG` option.
   See `Options` below for the structure of the debugger configuration.
   Example configuration using an environment variable:
     export _ANSIBLE_ANSIBALLZ_PYDEVD_CONFIG='{"module": "pydevd_pycharm", "settrace": {"host": "localhost", "port": 5678, "suspend": false}}'
6) Set any desired breakpoints.
7) Run Ansible commands.
"""

from __future__ import annotations

import dataclasses
import importlib
import json
import os
import pathlib

import typing as t


@dataclasses.dataclass(frozen=True)
class Options:
    """Debugger options for pydevd and its derivatives."""

    module: str = 'pydevd'
    """The Python module which will be imported and which provides the `settrace` method."""
    settrace: dict[str, object] = dataclasses.field(default_factory=dict)
    """The options to pass to the `{module}.settrace` method."""
    source_mapping: dict[str, str] = dataclasses.field(default_factory=dict)
    """
    A mapping of source paths to provide to pydevd.
    This setting is used internally by AnsiballZ and is not required unless Ansible CLI commands are run from a different system than your IDE.
    In that scenario, use this setting instead of configuring source mapping in your IDE.
    The key is a path known to the IDE.
    The value is the same path as known to the Ansible CLI.
    Both file paths and directories are supported.
    """


def run(args: dict[str, t.Any]) -> None:  # pragma: nocover
    """Enable remote debugging."""

    options = Options(**args)
    temp_dir = pathlib.Path(__file__).parent.parent.parent.parent.parent.parent
    path_mapping = [[key, str(temp_dir / value)] for key, value in options.source_mapping.items()]

    os.environ['PATHS_FROM_ECLIPSE_TO_PYTHON'] = json.dumps(path_mapping)

    debugging_module = importlib.import_module(options.module)
    debugging_module.settrace(**options.settrace)

    pass  # when suspend is True, execution pauses here -- it's also a convenient place to put a breakpoint
