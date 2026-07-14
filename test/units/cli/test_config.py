# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.cli.config import ConfigCLI


def parse_type(args: list[str]) -> str:
    """Return the resolved ``type`` after parsing ``args``.

    Parses with the CLI's own parser without initializing the global
    (write-once) context singleton, so multiple parses can be tested in one
    process.
    """
    cli = ConfigCLI(args=['ansible-config', *args])
    cli.init_parser()
    options = cli.parser.parse_args(cli.args[1:])
    return cli.post_process_args(options).type


@pytest.mark.parametrize(
    ('args', 'expected_type'),
    (
        pytest.param(['list'], 'all', id='list-defaults-to-all'),
        pytest.param(['dump'], 'all', id='dump-defaults-to-all'),
        pytest.param(['view'], 'all', id='view-defaults-to-all'),
        pytest.param(['init'], 'all', id='init-defaults-to-all'),
        pytest.param(['validate'], 'all', id='validate-defaults-to-all'),
        pytest.param(['dump', '-t', 'base'], 'base', id='base-compatibility-override'),
        pytest.param(['validate', '-t', 'connection'], 'connection', id='specific-type-override'),
    ),
)
def test_config_type_default(args: list[str], expected_type: str) -> None:
    # All actions default to checking base settings and all plugins (#86398),
    # while an explicit ``-t`` can restore the previous base-only behavior or narrow further.
    assert parse_type(args) == expected_type
