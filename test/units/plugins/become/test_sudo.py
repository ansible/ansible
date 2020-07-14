# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2020 Ansible Project
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re

from ansible import context
from ansible.playbook.play_context import PlayContext
from ansible.plugins.loader import become_loader


def test_sudo(mocker, parser, reset_cli_args):
    options = parser.parse_args([])
    context._init_global_context(options)
    play_context = PlayContext()

    default_cmd = "/bin/foo"
    default_exe = "/bin/bash"
    sudo_exe = 'sudo'
    sudo_flags = '-H -s -n'

    cmd = play_context.make_become_cmd(cmd=default_cmd, executable=default_exe)
    assert cmd == default_cmd

    success = 'BECOME-SUCCESS-.+?'

    play_context.become = True
    play_context.become_user = 'foo'
    play_context.set_become_plugin(become_loader.get('sudo'))
    play_context.become_flags = sudo_flags
    cmd = play_context.make_become_cmd(cmd=default_cmd, executable=default_exe)

    assert (re.match("""%s %s  -u %s %s -c 'echo %s; %s'""" % (sudo_exe, sudo_flags, play_context.become_user,
                                                               default_exe, success, default_cmd), cmd) is not None)

    play_context.become_pass = 'testpass'
    cmd = play_context.make_become_cmd(cmd=default_cmd, executable=default_exe)
    assert (re.match("""%s %s -p "%s" -u %s %s -c 'echo %s; %s'""" % (sudo_exe, sudo_flags.replace('-n', ''),
                                                                      r"\[sudo via ansible, key=.+?\] password:", play_context.become_user,
                                                                      default_exe, success, default_cmd), cmd) is not None)
