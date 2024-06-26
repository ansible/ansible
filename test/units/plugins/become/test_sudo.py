# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2020 Ansible Project
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import re

from ansible import context
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
