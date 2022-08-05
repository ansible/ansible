"""Command line parsing for the `network-integration` command."""
from __future__ import annotations

import argparse
import collections.abc as c
import os
import typing as t

from ....commands.integration.network import (
    command_network_integration,
)

from ....config import (
    NetworkIntegrationConfig,
)

from ....target import (
    walk_network_integration_targets,
)

from ....data import (
    data_context,
)

from ...environments import (
    CompositeActionCompletionFinder,
    ControllerMode,
    TargetMode,
    add_environments,
)

from ...completers import (
    register_completer,
)


def do_network_integration(
        subparsers,
        parent: argparse.ArgumentParser,
        add_integration_common: c.Callable[[argparse.ArgumentParser], None],
        completer: CompositeActionCompletionFinder,
):
    """Command line parsing for the `network-integration` command."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        'network-integration',
        parents=[parent],
        help='network integration tests',
    )

    parser.set_defaults(
        func=command_network_integration,
        targets_func=walk_network_integration_targets,
        config=NetworkIntegrationConfig)

    network_integration = t.cast(argparse.ArgumentParser, parser.add_argument_group(title='network integration test arguments'))

    add_integration_common(network_integration)

    register_completer(network_integration.add_argument(
        '--testcase',
        metavar='TESTCASE',
        help='limit a test to a specified testcase',
    ), complete_network_testcase)

    add_environments(parser, completer, ControllerMode.DELEGATED, TargetMode.NETWORK_INTEGRATION)  # network-integration


def complete_network_testcase(prefix: str, parsed_args: argparse.Namespace, **_) -> list[str]:
    """Return a list of test cases matching the given prefix if only one target was parsed from the command line, otherwise return an empty list."""
    testcases = []

    # since testcases are module specific, don't autocomplete if more than one
    # module is specified
    if len(parsed_args.include) != 1:
        return []

    target = parsed_args.include[0]
    test_dir = os.path.join(data_context().content.integration_targets_path, target, 'tests')
    connection_dirs = data_context().content.get_dirs(test_dir)

    for connection_dir in connection_dirs:
        for testcase in [os.path.basename(path) for path in data_context().content.get_files(connection_dir)]:
            if testcase.startswith(prefix):
                testcases.append(testcase.split('.', 1)[0])

    return testcases
