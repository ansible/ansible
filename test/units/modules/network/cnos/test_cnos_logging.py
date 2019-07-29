#
# (c) 2018 Red Hat Inc.
# Copyright (C) 2017 Lenovo.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.cnos import cnos_logging
from units.modules.utils import set_module_args
from .cnos_module import TestCnosModule, load_fixture


class TestCnosLoggingModule(TestCnosModule):

    module = cnos_logging

    def setUp(self):
        super(TestCnosLoggingModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.cnos.cnos_logging.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.cnos.cnos_logging.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestCnosLoggingModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None):
        self.get_config.return_value = load_fixture('cnos_logging_config.cfg')
        self.load_config.return_value = None

    def test_cnos_logging_buffer_size_changed_implicit(self):
        set_module_args(dict(dest='logfile', name='anil'))
        commands = ['logging logfile anil 5 size 10485760']
        self.execute_module(changed=True, commands=commands)

    def test_cnos_logging_logfile_size_changed_explicit(self):
        set_module_args(dict(dest='logfile', name='anil', level='4', size=6000))
        commands = ['logging logfile anil 4 size 6000']
        self.execute_module(changed=True, commands=commands)
