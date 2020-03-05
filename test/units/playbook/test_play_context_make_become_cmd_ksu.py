# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2020 Ansible Project
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
import pytest

from .test_play_context import parser, reset_cli_args
from ansible import constants as C
from ansible import context
from ansible.cli.arguments import option_helpers as opt_help
from ansible.errors import AnsibleError
from ansible.playbook.play_context import PlayContext
from ansible.playbook.play import Play
from ansible.plugins.loader import become_loader
from ansible.utils import context_objects as co


def test_play_context_make_become_cmd_ksu(mocker, parser, reset_cli_args):
    options = parser.parse_args([])
    context._init_global_context(options)
    play_context = PlayContext()

    default_cmd = "/bin/foo"
    default_exe = "/bin/bash"
    ksu_exe = 'ksu'
    ksu_flags = ''

    cmd = play_context.make_become_cmd(cmd=default_cmd, executable=default_exe)
    assert cmd == default_cmd

    success = 'BECOME-SUCCESS-.+?'

    play_context.become = True
    play_context.become_user = 'foo'
    play_context.set_become_plugin(become_loader.get('ksu'))
    play_context.become_method = 'ksu'
    play_context.become_flags = ksu_flags
    cmd = play_context.make_become_cmd(cmd=default_cmd, executable="/bin/bash")
    assert (re.match("""%s %s %s -e %s -c 'echo %s; %s'""" % (ksu_exe, play_context.become_user, ksu_flags,
                                                              default_exe, success, default_cmd), cmd) is not None)
