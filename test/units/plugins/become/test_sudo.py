# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2020 Ansible Project
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest
import re

from pytest_mock import MockerFixture

from ansible import context
from ansible.errors import AnsibleError
from ansible.plugins.loader import become_loader, shell_loader


def test_sudo(mocker, parser, reset_cli_args):
    options = parser.parse_args([])
    context._init_global_context(options)

    sudo = become_loader.get('sudo')
    sh = shell_loader.get('sh')
    sh.executable = "/bin/bash"

    sudo.set_options(direct={
        'become_user': 'foo',
        'become_flags': '-n -s -H',
    })

    cmd = sudo.build_become_command('/bin/foo', sh)

    assert re.match(r"""sudo\s+-n -s -H\s+-u foo /bin/bash -c 'echo BECOME-SUCCESS-.+? ; /bin/foo'""", cmd), cmd

    sudo.set_options(direct={
        'become_user': 'foo',
        'become_flags': '-n -s -H',
        'become_pass': 'testpass',
    })

    cmd = sudo.build_become_command('/bin/foo', sh)
    assert re.match(r"""sudo\s+-s\s-H\s+-p "\[sudo via ansible, key=.+?\] password:" -u foo /bin/bash -c 'echo BECOME-SUCCESS-.+? ; /bin/foo'""", cmd), cmd

    sudo.set_options(direct={
        'become_user': 'foo',
        'become_flags': '-snH',
        'become_pass': 'testpass',
    })

    cmd = sudo.build_become_command('/bin/foo', sh)
    assert re.match(r"""sudo\s+-sH\s+-p "\[sudo via ansible, key=.+?\] password:" -u foo /bin/bash -c 'echo BECOME-SUCCESS-.+? ; /bin/foo'""", cmd), cmd

    sudo.set_options(direct={
        'become_user': 'foo',
        'become_flags': '--non-interactive -s -H',
        'become_pass': 'testpass',
    })

    cmd = sudo.build_become_command('/bin/foo', sh)
    assert re.match(r"""sudo\s+-s\s-H\s+-p "\[sudo via ansible, key=.+?\] password:" -u foo /bin/bash -c 'echo BECOME-SUCCESS-.+? ; /bin/foo'""", cmd), cmd

    sudo.set_options(direct={
        'become_user': 'foo',
        'become_flags': '--non-interactive -nC5 -s -H',
        'become_pass': 'testpass',
    })

    cmd = sudo.build_become_command('/bin/foo', sh)
    assert re.match(r"""sudo\s+-C5\s-s\s-H\s+-p "\[sudo via ansible, key=.+?\] password:" -u foo /bin/bash -c 'echo BECOME-SUCCESS-.+? ; /bin/foo'""", cmd), cmd


@pytest.mark.parametrize("del_attr_name, expected_error_pattern", (
    ("ECHO", ".*does not support become.*missing the 'ECHO' attribute"),  # BecomeBase
    ("CD", ".*does not support sudo chdir.*missing the 'CD' attribute"),  # sudo
))
def test_invalid_shell_plugin(del_attr_name: str, expected_error_pattern: str, mocker: MockerFixture) -> None:
    def badprop(_self):
        raise AttributeError(del_attr_name)

    sh = shell_loader.get('sh')
    mocker.patch.object(type(sh), del_attr_name, property(fget=badprop))

    sudo = become_loader.get('sudo')
    sudo.set_options(direct=dict(sudo_chdir='/'))

    with pytest.raises(AnsibleError, match=expected_error_pattern):
        sudo.build_become_command('/stuff', sh)


def test_no_flags() -> None:
    sudo = become_loader.get('sudo')
    sudo.set_options(direct=dict(become_pass='x', become_flags=''))

    result = sudo.build_become_command('/stuff', shell_loader.get('sh'))

    # ensure no flags were in the final command other than -p and -u
    assert re.search(r'''^sudo +-p "[^"]*" -u root '[^']*'$''', result)


def test_no_cmd() -> None:
    cmd = ''

    assert become_loader.get('sudo').build_become_command(cmd, shell_loader.get('sh')) is cmd
