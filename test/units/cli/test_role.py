# Copyright: (c) 2017, 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import logging

import pytest

from ansible.cli.role import RoleCLI

from ansible.errors import AnsibleOptionsError

log = logging.getLogger(__name__)


def test_role_cli_no_args():
    with pytest.raises(TypeError):
        RoleCLI()


def test_role_cli_empty_args():
    cli = RoleCLI(args=[])
    assert isinstance(cli, RoleCLI)
    log.debug('cli: %s', cli)


def test_parse_empty_args():
    args = []
    cli = RoleCLI(args=args)
    with pytest.raises(AnsibleOptionsError):
        cli.parse()

    log.debug('cli.parser: %s', cli.parser)

    assert cli.parser is not None


def test_parse():
    args = ['ansible-role', 'localhost', '-r', 'somenamespace.somerepo', '-a', 'some_arg=some_value']
    cli = RoleCLI(args=args)
    cli.parse()

    log.debug('cli.parser: %s', cli.parser)

    assert cli.parser is not None

    log.debug('cli.options: %s', cli.options)
    log.debug('cli.options.role_name: %s', cli.options.role_name)
    log.debug('cli.options.role_args_string: %s', cli.options.role_args_string)
    assert cli.options.role_args_string == 'some_arg=some_value'


def test_run(mocker):

    mocker.patch('ansible.playbook.role.include.RoleInclude._load_role_path',
                 return_value=('somenamespace.somerepo', '/dev/null/not/a/path'))
    args = ['ansible-role', 'localhost', '-r', 'somenamespace.somerepo']
    cli = RoleCLI(args=args)
    cli.parse()

    rc = cli.run()

    log.debug('rc: %s', rc)

    assert rc == 0
