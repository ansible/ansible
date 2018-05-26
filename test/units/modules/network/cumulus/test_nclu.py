# -*- coding: utf-8 -*-

# (c) 2016, Cumulus Networks <ce-ceng@cumulusnetworks.com>
#
# This file is part of Ansible
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import os.path
import unittest

from ansible.modules.network.cumulus import nclu


class FakeModule(object):
    """Fake NCLU module to check the logic of the ansible module.

    We have two sets of tests: fake and real. Real tests only run if
    NCLU is installed on the testing machine (it should be a Cumulus VX
    VM or something like that).

    Fake tests are used to test the logic of the ansible module proper - that
    the right things are done when certain feedback is received.

    Real tests are used to test regressions against versions of NCLU. This
    FakeModule mimics the output that is used for screenscraping. If the real
    output differs, the real tests will catch that.

    To prepare a VX:
      sudo apt-get update
      sudo apt-get install python-setuptools git gcc python-dev libssl-dev
      sudo easy_install pip
      sudo pip install ansible nose coverage
      # git the module and cd to the directory
      nosetests --with-coverage --cover-package=nclu --cover-erase --cover-branches

    If a real test fails, it means that there is a risk of a version split, and
    that changing the module will break for old versions of NCLU if not careful.
    """

    def __init__(self, **kwargs):
        self.reset()

    def exit_json(self, **kwargs):
        self.exit_code = kwargs

    def fail_json(self, **kwargs):
        self.fail_code = kwargs

    def run_command(self, command):
        """Run an NCLU command"""

        self.command_history.append(command)
        if command == "/usr/bin/net pending":
            return (0, self.pending, "")
        elif command == "/usr/bin/net abort":
            self.pending = ""
            return (0, "", "")
        elif command.startswith("/usr/bin/net commit"):
            if self.pending:
                self.last_commit = self.pending
                self.pending = ""
                return (0, "", "")
            else:
                return (0, "commit ignored...there were no pending changes", "")
        elif command == "/usr/bin/net show commit last":
            return (0, self.last_commit, "")
        else:
            self.pending += command
            return self.mocks.get(command, (0, "", ""))

    def mock_output(self, command, _rc, output, _err):
        """Prepare a command to mock certain output"""

        self.mocks[command] = (_rc, output, _err)

    def reset(self):
        self.params = {}
        self.exit_code = {}
        self.fail_code = {}
        self.command_history = []
        self.mocks = {}
        self.pending = ""
        self.last_commit = ""


def skipUnlessNcluInstalled(original_function):
    if os.path.isfile('/usr/bin/net'):
        return original_function
    else:
        return unittest.skip('only run if nclu is installed')


class TestNclu(unittest.TestCase):

    def test_command_helper(self):
        module = FakeModule()
        module.mock_output("/usr/bin/net add int swp1", 0, "", "")

        result = nclu.command_helper(module, 'add int swp1', 'error out')
        self.assertEqual(module.command_history[-1], "/usr/bin/net add int swp1")
        self.assertEqual(result, "")

    def test_command_helper_error_code(self):
        module = FakeModule()
        module.mock_output("/usr/bin/net fake fail command", 1, "", "")

        result = nclu.command_helper(module, 'fake fail command', 'error out')
        self.assertEqual(module.fail_code, {'msg': "error out"})

    def test_command_helper_error_msg(self):
        module = FakeModule()
        module.mock_output("/usr/bin/net fake fail command", 0,
                           "ERROR: Command not found", "")

        result = nclu.command_helper(module, 'fake fail command', 'error out')
        self.assertEqual(module.fail_code, {'msg': "error out"})

    def test_command_helper_no_error_msg(self):
        module = FakeModule()
        module.mock_output("/usr/bin/net fake fail command", 0,
                           "ERROR: Command not found", "")

        result = nclu.command_helper(module, 'fake fail command')
        self.assertEqual(module.fail_code, {'msg': "ERROR: Command not found"})

    def test_empty_run(self):
        module = FakeModule()
        changed, output = nclu.run_nclu(module, None, None, False, False, False, "")
        self.assertEqual(module.command_history, ['/usr/bin/net pending',
                                                  '/usr/bin/net pending'])
        self.assertEqual(module.fail_code, {})
        self.assertEqual(changed, False)

    def test_command_list(self):
        module = FakeModule()
        changed, output = nclu.run_nclu(module, ['add int swp1', 'add int swp2'],
                                        None, False, False, False, "")

        self.assertEqual(module.command_history, ['/usr/bin/net pending',
                                                  '/usr/bin/net add int swp1',
                                                  '/usr/bin/net add int swp2',
                                                  '/usr/bin/net pending'])
        self.assertNotEqual(len(module.pending), 0)
        self.assertEqual(module.fail_code, {})
        self.assertEqual(changed, True)

    def test_command_list_commit(self):
        module = FakeModule()
        changed, output = nclu.run_nclu(module,
                                        ['add int swp1', 'add int swp2'],
                                        None, True, False, False, "committed")

        self.assertEqual(module.command_history, ['/usr/bin/net pending',
                                                  '/usr/bin/net add int swp1',
                                                  '/usr/bin/net add int swp2',
                                                  '/usr/bin/net pending',
                                                  "/usr/bin/net commit description 'committed'",
                                                  '/usr/bin/net show commit last'])
        self.assertEqual(len(module.pending), 0)
        self.assertEqual(module.fail_code, {})
        self.assertEqual(changed, True)

    def test_command_atomic(self):
        module = FakeModule()
        changed, output = nclu.run_nclu(module,
                                        ['add int swp1', 'add int swp2'],
                                        None, False, True, False, "atomically")

        self.assertEqual(module.command_history, ['/usr/bin/net abort',
                                                  '/usr/bin/net pending',
                                                  '/usr/bin/net add int swp1',
                                                  '/usr/bin/net add int swp2',
                                                  '/usr/bin/net pending',
                                                  "/usr/bin/net commit description 'atomically'",
                                                  '/usr/bin/net show commit last'])
        self.assertEqual(len(module.pending), 0)
        self.assertEqual(module.fail_code, {})
        self.assertEqual(changed, True)

    def test_command_abort_first(self):
        module = FakeModule()
        module.pending = "dirty"
        nclu.run_nclu(module, None, None, False, False, True, "")

        self.assertEqual(len(module.pending), 0)

    def test_command_template_commit(self):
        module = FakeModule()
        changed, output = nclu.run_nclu(module, None,
                                        "    add int swp1\n    add int swp2",
                                        True, False, False, "committed")

        self.assertEqual(module.command_history, ['/usr/bin/net pending',
                                                  '/usr/bin/net add int swp1',
                                                  '/usr/bin/net add int swp2',
                                                  '/usr/bin/net pending',
                                                  "/usr/bin/net commit description 'committed'",
                                                  '/usr/bin/net show commit last'])
        self.assertEqual(len(module.pending), 0)
        self.assertEqual(module.fail_code, {})
        self.assertEqual(changed, True)

    def test_commit_ignored(self):
        module = FakeModule()
        changed, output = nclu.run_nclu(module, None, None, True, False, False, "ignore me")

        self.assertEqual(module.command_history, ['/usr/bin/net pending',
                                                  '/usr/bin/net pending',
                                                  "/usr/bin/net commit description 'ignore me'",
                                                  '/usr/bin/net abort'])
        self.assertEqual(len(module.pending), 0)
        self.assertEqual(module.fail_code, {})
        self.assertEqual(changed, False)

    def test_check_mode(self):
        module = FakeModule()
        module.check_mode = True
        changed, output = nclu.run_nclu(module,
                                        ['add int swp1', 'add int swp2'],
                                        None, False, True, False, "atomically")

        self.assertEqual(len(module.pending), 0)
        self.assertEqual(module.fail_code, {})
        self.assertEqual(changed, False)
