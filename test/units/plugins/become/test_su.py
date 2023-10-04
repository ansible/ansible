# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2020 Ansible Project
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import re

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
