# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2020 Ansible Project
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import re

import pytest

from ansible import context
from ansible.plugins.loader import become_loader, shell_loader


def test_su(mocker, parser, reset_cli_args):
    options = parser.parse_args([])
    context._init_global_context(options)

    su = become_loader.get('su')
    sh = shell_loader.get('sh')
    sh.executable = "/bin/bash"

    su.set_options(direct={
        'become_user': 'foo',
        'become_flags': '',
    })

    cmd = su.build_become_command('/bin/foo', sh)
    assert re.match(r"""su\s+foo -c '/bin/bash -c '"'"'echo BECOME-SUCCESS-.+?; /bin/foo'"'"''""", cmd)


def test_no_cmd() -> None:
    cmd = ''

    assert become_loader.get('su').build_become_command(cmd, shell_loader.get('sh')) is cmd


@pytest.mark.parametrize("prefix, prompt", (
    ("", "Password:"),
    (" ", "Password :"),
    ("\n", "Password ："),
    ("x", "Password ："),
    ("", "口令:"),
    (" ", "口令 :"),
    ("\n", "口令 ："),
    ("x", "口令 ："),
))
def test_check_password_prompt_success(prefix: str, prompt: str) -> None:
    become = become_loader.get('su')

    assert become.check_password_prompt((prefix + prompt).encode()) is True
    assert become.prompt == prompt


@pytest.mark.parametrize("data", (
    "Password",
    "Passwort",
    "Pass:",
))
def test_check_password_prompt_failure(data: str) -> None:
    become = become_loader.get('su')

    assert become.check_password_prompt(data.encode()) is False
    assert become.prompt == ''


def test_check_password_prompt_escaping(mocker) -> None:
    become = become_loader.get('su')

    mocker.patch.object(become, 'get_option', return_value=['(invalid regex'])

    assert become.check_password_prompt('(invalid regex:') is True
