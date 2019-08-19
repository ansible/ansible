# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2017 Ansible Project
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
import pytest

from ansible import constants as C
from ansible import context
from ansible.cli.arguments import option_helpers as opt_help
from ansible.errors import AnsibleError
from ansible.playbook.play_context import PlayContext
from ansible.playbook.play import Play
from ansible.plugins.loader import become_loader
from ansible.utils import context_objects as co


@pytest.fixture
def parser():
    parser = opt_help.create_base_parser('testparser')

    opt_help.add_runas_options(parser)
    opt_help.add_meta_options(parser)
    opt_help.add_runtask_options(parser)
    opt_help.add_vault_options(parser)
    opt_help.add_async_options(parser)
    opt_help.add_connect_options(parser)
    opt_help.add_subset_options(parser)
    opt_help.add_check_options(parser)
    opt_help.add_inventory_options(parser)

    return parser


@pytest.fixture
def reset_cli_args():
    co.GlobalCLIArgs._Singleton__instance = None
    yield
    co.GlobalCLIArgs._Singleton__instance = None


def test_play_context(mocker, parser, reset_cli_args):
    options = parser.parse_args(['-vv', '--check'])
    context._init_global_context(options)
    play = Play.load({})
    play_context = PlayContext(play=play)

    assert play_context.remote_addr is None
    assert play_context.remote_user is None
    assert play_context.password == ''
    assert play_context.private_key_file == C.DEFAULT_PRIVATE_KEY_FILE
    assert play_context.timeout == C.DEFAULT_TIMEOUT
    assert play_context.verbosity == 2
    assert play_context.check_mode is True

    mock_play = mocker.MagicMock()
    mock_play.force_handlers = True

    play_context = PlayContext(play=mock_play)
    assert play_context.force_handlers is True

    mock_task = mocker.MagicMock()
    mock_task.connection = 'mocktask'
    mock_task.remote_user = 'mocktask'
    mock_task.port = 1234
    mock_task.no_log = True
    mock_task.become = True
    mock_task.become_method = 'mocktask'
    mock_task.become_user = 'mocktaskroot'
    mock_task.become_pass = 'mocktaskpass'
    mock_task._local_action = False
    mock_task.delegate_to = None

    all_vars = dict(
        ansible_connection='mock_inventory',
        ansible_ssh_port=4321,
    )

    mock_templar = mocker.MagicMock()

    play_context = PlayContext()
    play_context = play_context.set_task_and_variable_override(task=mock_task, variables=all_vars, templar=mock_templar)

    assert play_context.connection == 'mock_inventory'
    assert play_context.remote_user == 'mocktask'
    assert play_context.no_log is True

    mock_task.no_log = False
    play_context = play_context.set_task_and_variable_override(task=mock_task, variables=all_vars, templar=mock_templar)
    assert play_context.no_log is False


def test_play_context_make_become_cmd(mocker, parser, reset_cli_args):
    options = parser.parse_args([])
    context._init_global_context(options)
    play_context = PlayContext()

    default_cmd = "/bin/foo"
    default_exe = "/bin/bash"
    sudo_exe = 'sudo'
    sudo_flags = '-H -s -n'
    su_exe = 'su'
    su_flags = ''
    pbrun_exe = 'pbrun'
    pbrun_flags = ''
    pfexec_exe = 'pfexec'
    pfexec_flags = ''
    doas_exe = 'doas'
    doas_flags = '-n'
    ksu_exe = 'ksu'
    ksu_flags = ''
    dzdo_exe = 'dzdo'
    dzdo_flags = ''

    cmd = play_context.make_become_cmd(cmd=default_cmd, executable=default_exe)
    assert cmd == default_cmd

    success = 'BECOME-SUCCESS-.+?'

    play_context.become = True
    play_context.become_user = 'foo'
    play_context.set_become_plugin(become_loader.get('sudo'))
    play_context.become_flags = sudo_flags
    cmd = play_context.make_become_cmd(cmd=default_cmd, executable="/bin/bash")

    assert (re.match("""%s %s  -u %s %s -c 'echo %s; %s'""" % (sudo_exe, sudo_flags, play_context.become_user,
                                                               default_exe, success, default_cmd), cmd) is not None)

    play_context.become_pass = 'testpass'
    cmd = play_context.make_become_cmd(cmd=default_cmd, executable=default_exe)
    assert (re.match("""%s %s -p "%s" -u %s %s -c 'echo %s; %s'""" % (sudo_exe, sudo_flags.replace('-n', ''),
                                                                      r"\[sudo via ansible, key=.+?\] password:", play_context.become_user,
                                                                      default_exe, success, default_cmd), cmd) is not None)

    play_context.become_pass = None
    play_context.become_method = 'su'
    play_context.set_become_plugin(become_loader.get('su'))
    play_context.become_flags = su_flags
    cmd = play_context.make_become_cmd(cmd=default_cmd, executable="/bin/bash")
    assert (re.match("""%s  %s -c '%s -c '"'"'echo %s; %s'"'"''""" % (su_exe, play_context.become_user, default_exe,
                                                                      success, default_cmd), cmd) is not None)

    play_context.set_become_plugin(become_loader.get('pbrun'))
    play_context.become_method = 'pbrun'
    play_context.become_flags = pbrun_flags
    cmd = play_context.make_become_cmd(cmd=default_cmd, executable="/bin/bash")
    assert re.match("""%s %s -u %s 'echo %s; %s'""" % (pbrun_exe, pbrun_flags, play_context.become_user,
                                                       success, default_cmd), cmd) is not None

    play_context.set_become_plugin(become_loader.get('pfexec'))
    play_context.become_method = 'pfexec'
    play_context.become_flags = pfexec_flags
    cmd = play_context.make_become_cmd(cmd=default_cmd, executable="/bin/bash")
    assert re.match('''%s %s "'echo %s; %s'"''' % (pfexec_exe, pfexec_flags, success, default_cmd), cmd) is not None

    play_context.set_become_plugin(become_loader.get('doas'))
    play_context.become_method = 'doas'
    play_context.become_flags = doas_flags
    cmd = play_context.make_become_cmd(cmd=default_cmd, executable="/bin/bash")
    assert (re.match("""%s %s -u %s %s -c 'echo %s; %s'""" % (doas_exe, doas_flags, play_context.become_user, default_exe, success,
                                                              default_cmd), cmd) is not None)

    play_context.set_become_plugin(become_loader.get('ksu'))
    play_context.become_method = 'ksu'
    play_context.become_flags = ksu_flags
    cmd = play_context.make_become_cmd(cmd=default_cmd, executable="/bin/bash")
    assert (re.match("""%s %s %s -e %s -c 'echo %s; %s'""" % (ksu_exe, play_context.become_user, ksu_flags,
                                                              default_exe, success, default_cmd), cmd) is not None)

    play_context.set_become_plugin(become_loader.get('bad'))
    play_context.become_method = 'bad'
    with pytest.raises(AnsibleError):
        play_context.make_become_cmd(cmd=default_cmd, executable="/bin/bash")

    play_context.set_become_plugin(become_loader.get('dzdo'))
    play_context.become_method = 'dzdo'
    play_context.become_flags = dzdo_flags
    cmd = play_context.make_become_cmd(cmd=default_cmd, executable="/bin/bash")
    assert re.match("""%s %s -u %s %s -c 'echo %s; %s'""" % (dzdo_exe, dzdo_flags, play_context.become_user, default_exe,
                                                             success, default_cmd), cmd) is not None
    play_context.become_pass = 'testpass'
    play_context.set_become_plugin(become_loader.get('dzdo'))
    cmd = play_context.make_become_cmd(cmd=default_cmd, executable="/bin/bash")
    assert re.match("""%s %s -p %s -u %s %s -c 'echo %s; %s'""" % (dzdo_exe, dzdo_flags, r'\"\[dzdo via ansible, key=.+?\] password:\"',
                                                                   play_context.become_user, default_exe, success, default_cmd), cmd) is not None
