from __future__ import annotations

import dataclasses
import json
import os
import pathlib


@dataclasses.dataclass(frozen=True)
class Options:
    """Base Debugger options for any debugging extension modules."""

    ansiballz_extension: str
    """The name of the AnsiballZ extension module to use."""
    host: str = 'localhost'
    """The host to connect the debugger to."""
    port: int = 5678
    """The port to connect the debugger to."""
    source_mapping: dict[str, str] = dataclasses.field(default_factory=dict)
    """
    A mapping of source paths to provide to the debugger.
    This setting is used internally by AnsiballZ and is not required unless Ansible CLI commands are run from a different system than your IDE.
    In that scenario, use this setting instead of configuring source mapping in your IDE.
    The key is a path known to the IDE.
    The value is the same path as known to the Ansible CLI.
    Both file paths and directories are supported.
    """


def setup_pydevd_source_mapping(options: Options) -> None:
    """Setup the source mapping for pydevd based debuggers."""
    temp_dir = pathlib.Path(__file__).parent.parent.parent.parent.parent.parent
    path_mapping = [[key, str(temp_dir / value)] for key, value in options.source_mapping.items()]

    os.environ['PATHS_FROM_ECLIPSE_TO_PYTHON'] = json.dumps(path_mapping)
