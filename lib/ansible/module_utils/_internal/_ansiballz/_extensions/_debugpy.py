"""
Remote debugging support for AnsiballZ modules with debugpy.

To use with VSCode:

1) Choose an available port for VSCode to listen on (e.g. 5678).
2) Ensure `debugpy` is installed for the interpreter(s) which will run the code being debugged.
3) Create the following launch.json configuration

    {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Python Debug Server",
                "type": "debugpy",
                "request": "attach",
                "listen": {
                    "host": "localhost",
                    "port": 5678,
                },
            },
            {
                "name": "ansible-playbook main.yml",
                "type": "debugpy",
                "request": "launch",
                "module": "ansible",
                "args": [
                    "playbook",
                    "main.yml"
                ],
                "env": {
                    "_ANSIBLE_ANSIBALLZ_DEBUGGER_CONFIG": "{\"ansiballz_extension\": \"_debugpy\", \"port\": 5678}"
                },
                "console": "integratedTerminal",
            }
        ],
        "compounds": [
            {
                "name": "Test Module Debugging",
                "configurations": [
                    "Python Debug Server",
                    "ansible-playbook main.yml"
                ],
                "stopAll": true
            }
        ]
    }

4) Set any desired breakpoints.
5) Configure the Run and Debug view to use the "Test Module Debugging" compound configuration.
6) Press F5 to start debugging.
"""

from __future__ import annotations

import dataclasses

import typing as t

from . import _debugger

HAS_DEBUGPY = False
try:
    import debugpy

    HAS_DEBUGPY = True
except ImportError:
    pass


@dataclasses.dataclass(frozen=True)
class Options(_debugger.Options):
    """Debugger options for debugpy."""

    connect: dict[str, object] = dataclasses.field(default_factory=dict)
    """The options to pass to `debugpy.connect`."""


def run(args: dict[str, t.Any]) -> None:  # pragma: nocover
    """Enable remote debugging with debugpy."""

    options = Options(**args)

    _debugger.setup_pydevd_source_mapping(options)

    debugpy.connect((options.host, options.port), **options.connect)

    pass  # a convenient place to put a breakpoint post connection.
