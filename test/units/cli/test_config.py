# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.cli.config import ConfigCLI


def parse_args(args: list[str]):
    # parse with the CLI's parser without initializing the global (write-once)
    # context singleton, so multiple parses can be tested in one process
    cli = ConfigCLI(args=['ansible-config', *args])
    cli.init_parser()
    options = cli.parser.parse_args(cli.args[1:])
    return cli.post_process_args(options)


def test_validate_defaults_to_all():
    """The validate action defaults to checking base settings and all plugins (#86398)."""
    assert parse_args(['validate']).type == 'all'


def test_validate_type_narrowing():
    """An explicit -t still narrows validation."""
    assert parse_args(['validate', '-t', 'base']).type == 'base'


def test_other_actions_default_to_base():
    """Other actions keep the base default."""
    assert parse_args(['dump']).type == 'base'
