"""Common logic for the `coverage analyze` subcommand."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ... import types as t

from .. import (
    CoverageConfig,
)


class CoverageAnalyzeConfig(CoverageConfig):
    """Configuration for the `coverage analyze` command."""
    def __init__(self, args):  # type: (t.Any) -> None
        super(CoverageAnalyzeConfig, self).__init__(args)

        # avoid mixing log messages with file output when using `/dev/stdout` for the output file on commands
        # this may be worth considering as the default behavior in the future, instead of being dependent on the command or options used
        self.info_stderr = True
