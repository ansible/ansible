# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import sys

if sys.version_info < (2, 7):
    pytestmark = pytest.mark.skip("pfSense Ansible modules require Python >= 2.7")

from ansible.modules.network.pfsense import pfsense_route
from .pfsense_module import TestPFSenseModule
from units.compat.mock import patch


class TestPFSenseRouteModule(TestPFSenseModule):

    module = pfsense_route

    def __init__(self, *args, **kwargs):
        super(TestPFSenseRouteModule, self).__init__(*args, **kwargs)
        self.config_file = 'pfsense_route_config.xml'

    def setUp(self):
        """ mocking up """

        super(TestPFSenseRouteModule, self).setUp()

        self.mock_run_command = patch('ansible.module_utils.basic.AnsibleModule.run_command')
        self.run_command = self.mock_run_command.start()
        self.run_command.return_value = (0, '', '')

    @staticmethod
    def get_args_fields():
        """ return params fields """
        fields = ['descr', 'network', 'disabled', 'gateway']
        return fields

    def check_target_elt(self, params, target_elt):
        """ test the xml definition """

        self.check_param_equal_or_not_find(params, target_elt, 'disabled')
        self.check_param_equal(params, target_elt, 'gateway')
        self.check_param_equal(params, target_elt, 'network')

    def get_target_elt(self, obj, absent=False):
        """ get the generated xml definition """
        root_elt = self.assert_find_xml_elt(self.xml_result, 'staticroutes')

        for item in root_elt:
            name_elt = item.find('descr')
            if name_elt is not None and name_elt.text == obj['descr']:
                return item

        return None

    ##############
    # tests
    #
    def test_route_create(self):
        """ test """
        obj = dict(descr='test_route', network='1.2.3.4/24', gateway='GW_LAN')
        command = "create route 'test_route', network='1.2.3.4/24', gateway='GW_LAN'"
        self.do_module_test(obj, command=command)

    def test_route_create_invalid_gw(self):
        """ test """
        obj = dict(descr='test_route', network='1.2.3.4/24', gateway='GW_INVALID')
        msg = "The gateway GW_INVALID does not exist"
        self.do_module_test(obj, msg=msg, failed=True)

    def test_route_create_invalid_ip(self):
        """ test """
        obj = dict(descr='test_route', network='2001::1', gateway='GW_LAN')
        msg = 'The gateway "192.168.1.1" is a different Address Family than network "2001::1".'
        self.do_module_test(obj, msg=msg, failed=True)

    def test_route_create_invalid_ip2(self):
        """ test """
        obj = dict(descr='test_route', network='1.2.3.4', gateway='GW_LAN_V6')
        msg = 'The gateway "2002::1" is a different Address Family than network "1.2.3.4".'
        self.do_module_test(obj, msg=msg, failed=True)

    def test_route_create_invalid_alias(self):
        """ test """
        obj = dict(descr='test_route', network='invalid_alias', gateway='GW_LAN')
        msg = 'A valid IPv4 or IPv6 destination network or alias must be specified.'
        self.do_module_test(obj, msg=msg, failed=True)

    def test_route_update_noop(self):
        """ test """
        obj = dict(descr='GW_WAN route', network='10.3.0.0/16', gateway='GW_WAN')
        self.do_module_test(obj, changed=False)

    def test_route_update_network(self):
        """ test """
        obj = dict(descr='GW_WAN route', network='10.4.0.0/16', gateway='GW_WAN')
        command = "update route 'GW_WAN route' set network='10.4.0.0/16'"
        self.do_module_test(obj, command=command)

    def test_route_update_gateway(self):
        """ test """
        obj = dict(descr='GW_WAN route', network='10.3.0.0/16', gateway='GW_LAN')
        command = "update route 'GW_WAN route' set gateway='GW_LAN'"
        self.do_module_test(obj, command=command)

    def test_route_delete(self):
        """ test """
        obj = dict(descr='GW_WAN route')
        command = "delete route 'GW_WAN route'"
        self.do_module_test(obj, command=command, delete=True)

    def test_route_delete_alias(self):
        """ test """
        obj = dict(descr='GW_WAN alias')
        command = "delete route 'GW_WAN alias'"
        self.do_module_test(obj, command=command, delete=True)
