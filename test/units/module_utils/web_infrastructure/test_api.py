# (c) 2018 Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import sys
import copy

from units.compat import unittest
from units.compat.mock import patch, MagicMock, Mock
from ansible.module_utils.web_infrastructure.ansible_tower import api

class TestWebInfrastructureTowerApi(unittest.TestCase):

    def setUp(self):
        super(TestWebInfrastructureTowerApi, self).setUp()

        self.module = MagicMock(name='AnsibleModule')
        self.module.check_mode = False
        self.module.params = {'provider': None}

        self.mock_connector = patch('ansible.module_utils.web_infrastructure.ansible_tower.api.AnsibleTowerBase')
        self.mock_connector.start()

    def tearDown(self):
        super(TestWebInfrastructureTowerApi, self).tearDown()

        self.mock_connector.stop()

    def get_connection(self, test_object):
        wapi = api.AnsibleTowerBase(self.module)
        wapi.get_object = Mock(name='get_object', return_value=test_object)
        wapi.create_object = Mock(name='create_object')
        wapi.update_object = Mock(name='update_object')
        wapi.delete_object = Mock(name='delete_object')
        return wapi
