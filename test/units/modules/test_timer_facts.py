# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from units.compat import unittest
from units.compat.mock import patch

from ansible.module_utils import basic
from ansible.modules.timer_facts import SystemctlScanTimer

# Linux # systemctl list-units --no-pager --type timer --all
STMCTL_OUTPUT = """
  UNIT                         LOAD   ACTIVE SUB     DESCRIPTION
  man-db.timer                 loaded active waiting Daily man-db regeneration
  shadow.timer                 loaded active waiting Daily verification of password and group files
  systemd-tmpfiles-clean.timer loaded active waiting Daily Cleanup of Temporary Directories
  updatedb.timer               loaded active waiting Daily locate database update

LOAD   = Reflects whether the unit definition was properly loaded.
ACTIVE = The high-level unit activation state, i.e. generalization of SUB.
SUB    = The low-level unit activation state, values depend on unit type.
4 loaded units listed.
To show all installed unit files use 'systemctl list-unit-files'.
"""


class TestSystemctlScanTimer(unittest.TestCase):

    def setUp(self):
        self.mock1 = patch.object(basic.AnsibleModule, 'get_bin_path', return_value='/bin/systemctl')
        self.mock1.start()
        self.addCleanup(self.mock1.stop)
        self.mock2 = patch.object(basic.AnsibleModule, 'run_command', return_value=(0, STMCTL_OUTPUT, ''))
        self.mock2.start()
        self.addCleanup(self.mock2.stop)
        self.mock3 = patch('platform.system', return_value='Linux')
        self.mock3.start()
        self.addCleanup(self.mock3.stop)

    def test_gather_timers(self):
        tmrmod = SystemctlScanTimer(basic.AnsibleModule)
        result = tmrmod.gather_timers()

        self.assertIsInstance(result, dict)

        self.assertIn('systemd-tmpfiles-clean.timer', result)
        self.assertEqual(result['systemd-tmpfiles-clean.timer'], {
            'name': 'systemd-tmpfiles-clean.timer',
            'source': 'systemd',
            'state': 'stopped',
            'status': 'loaded',
        })
        self.assertIn('updatedb.timer', result)
        self.assertEqual(result['updatedb.timer'], {
            'name': 'updatedb.timer',
            'source': 'systemd',
            'state': 'stopped',
            'status': 'loaded',
        })
