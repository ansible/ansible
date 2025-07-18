"""
Remote debugging support for AnsiballZ modules with debugpy.

To use with VS Code:

1) Choose an available port for VS Code to listen on (e.g. 5678).
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
                    "_ANSIBLE_ANSIBALLZ_DEBUGPY_CONFIG": "{\"host\": \"localhost\", \"port\": 5678}"
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
import json
import os
import pathlib

import typing as t


@dataclasses.dataclass(frozen=True)
class Options:
    """Debugger options for debugpy."""

    host: str = 'localhost'
    """The host to connect to for remote debugging."""
    port: int = 5678
    """The port to connect to for remote debugging."""
    connect: dict[str, object] = dataclasses.field(default_factory=dict)
    """The options to pass to the `debugpy.connect` method."""
    source_mapping: dict[str, str] = dataclasses.field(default_factory=dict)
    """
    A mapping of source paths to provide to debugpy.
    This setting is used internally by AnsiballZ and is not required unless Ansible CLI commands are run from a different system than your IDE.
    In that scenario, use this setting instead of configuring source mapping in your IDE.
    The key is a path known to the IDE.
    The value is the same path as known to the Ansible CLI.
    Both file paths and directories are supported.
    """


def run(args: dict[str, t.Any]) -> None:  # pragma: nocover
    """Enable remote debugging."""
    import debugpy

    options = Options(**args)
    temp_dir = pathlib.Path(__file__).parent.parent.parent.parent.parent.parent
    path_mapping = [[key, str(temp_dir / value)] for key, value in options.source_mapping.items()]

    os.environ['PATHS_FROM_ECLIPSE_TO_PYTHON'] = json.dumps(path_mapping)

    debugpy.connect((options.host, options.port), **options.connect)

    pass  # A convenient place to put a breakpoint
