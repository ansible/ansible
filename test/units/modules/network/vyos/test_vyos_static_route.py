# (c) 2016 Red Hat Inc.
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.compat.tests.mock import patch
from ansible.modules.network.vyos import vyos_static_route
from .vyos_module import TestVyosModule, load_fixture, set_module_args


class TestVyosStaticRouteModule(TestVyosModule):

    module = vyos_static_route

    def setUp(self):
        self.mock_get_config = patch('ansible.modules.network.vyos.vyos_static_route.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.vyos.vyos_static_route.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        self.load_config.return_value = dict(diff=None, session='session')

    def test_vyos_static_route_present(self):
        set_module_args(dict(prefix='172.26.0.0/16', next_hop='172.26.4.1', admin_distance='1'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'],
                         ['set protocols static route 172.26.0.0/16 next-hop 172.26.4.1 distance 1'])
