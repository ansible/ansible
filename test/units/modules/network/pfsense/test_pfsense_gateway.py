# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import sys

if sys.version_info < (2, 7):
    pytestmark = pytest.mark.skip("pfSense Ansible modules require Python >= 2.7")

from ansible.modules.network.pfsense import pfsense_gateway
from .pfsense_module import TestPFSenseModule


class TestPFSenseGatewayModule(TestPFSenseModule):

    module = pfsense_gateway

    def __init__(self, *args, **kwargs):
        super(TestPFSenseGatewayModule, self).__init__(*args, **kwargs)
        self.config_file = 'pfsense_gateway_config.xml'

    @staticmethod
    def get_args_fields():
        """ return params fields """
        fields = ['descr', 'interface', 'disabled', 'name', 'ipprotocol', 'gateway', 'monitor']
        fields += ['monitor_disable', 'action_disable', 'force_down', 'weight']
        return fields

    def check_target_elt(self, params, target_elt):
        """ test the xml definition """

        self.check_param_equal_or_not_find(params, target_elt, 'disabled')
        self.check_param_equal_or_not_find(params, target_elt, 'monitor_disable')
        self.check_param_equal_or_not_find(params, target_elt, 'action_disable')
        self.check_param_equal_or_not_find(params, target_elt, 'force_down')
        self.check_param_equal_or_not_find(params, target_elt, 'monitor')

        self.check_value_equal(target_elt, 'interface', self.unalias_interface(params['interface']))
        self.check_param_equal(params, target_elt, 'descr')
        self.check_param_equal(params, target_elt, 'weight', '1')
        self.check_param_equal(params, target_elt, 'gateway')
        self.check_param_equal(params, target_elt, 'ipprotocol', 'inet')

    def get_target_elt(self, obj, absent=False):
        """ get the generated xml definition """
        rules_elt = self.assert_find_xml_elt(self.xml_result, 'gateways')

        for item in rules_elt:
            name_elt = item.find('name')
            if name_elt is not None and name_elt.text == obj['name']:
                return item

        return None

    ##############
    # tests
    #
    def test_gateway_create(self):
        """ test """
        obj = dict(name='test_gw', interface='lan', gateway='192.168.1.1')
        command = "create gateway 'test_gw', interface='lan', gateway='192.168.1.1'"
        self.do_module_test(obj, command=command)

    def test_gateway_create_with_params(self):
        """ test """
        obj = dict(name='test_gw', interface='lan', gateway='192.168.1.1', descr='a test gw', monitor='8.8.8.8', weight=10)
        command = "create gateway 'test_gw', interface='lan', gateway='192.168.1.1', descr='a test gw', monitor='8.8.8.8', weight='10'"
        self.do_module_test(obj, command=command)

    def test_gateway_create_ipv6(self):
        """ test """
        obj = dict(name='test_gw', interface='wan', ipprotocol='inet6', gateway='2001::1')
        command = "create gateway 'test_gw', interface='wan', ipprotocol='inet6', gateway='2001::1'"
        self.do_module_test(obj, command=command)

    def test_gateway_create_in_vip(self):
        """ test """
        obj = dict(name='test_gw', interface='lan', gateway='10.255.2.1')
        command = "create gateway 'test_gw', interface='lan', gateway='10.255.2.1'"
        self.do_module_test(obj, command=command)

    def test_gateway_create_invalid_name(self):
        """ test """
        obj = dict(name='___', interface='lan', gateway='192.168.1.1')
        msg = 'The gateway name must be less than 32 characters long, may not consist of only numbers, '
        msg += 'may not consist of only underscores, and may only contain the following characters: a-z, A-Z, 0-9, _'
        self.do_module_test(obj, msg=msg, failed=True)

    def test_gateway_create_invalid_interface(self):
        """ test """
        obj = dict(name='test_gw', interface='lan_232', gateway='192.168.1.1')
        msg = 'Interface lan_232 not found'
        self.do_module_test(obj, msg=msg, failed=True)

    def test_gateway_create_invalid_ip(self):
        """ test """
        obj = dict(name='test_gw', interface='lan', gateway='acme.dyndns.org')
        msg = 'gateway must use an IPv4 address'
        self.do_module_test(obj, msg=msg, failed=True)

    def test_gateway_create_invalid_ip2(self):
        """ test """
        obj = dict(name='test_gw', interface='lan', gateway='1.2.3.4')
        msg = "The gateway address 1.2.3.4 does not lie within one of the chosen interface's subnets."
        self.do_module_test(obj, msg=msg, failed=True)

    def test_gateway_create_invalid_ip3(self):
        """ test """
        obj = dict(name='test_gw', interface='lan', gateway='2001::1')
        msg = 'gateway must use an IPv4 address'
        self.do_module_test(obj, msg=msg, failed=True)

    def test_gateway_create_invalid_ip4(self):
        """ test """
        obj = dict(name='test_gw', interface='vt1', gateway='192.168.1.1')
        msg = 'Cannot add IPv4 Gateway Address because no IPv4 address could be found on the interface.'
        self.do_module_test(obj, msg=msg, failed=True)

    def test_gateway_create_invalid_monitor(self):
        """ test """
        obj = dict(name='test_gw', interface='lan', gateway='192.168.1.1', monitor='2001::1')
        msg = 'monitor must use an IPv4 address'
        self.do_module_test(obj, msg=msg, failed=True)

    def test_gateway_create_invalid_ipv6(self):
        """ test """
        obj = dict(name='test_gw', interface='lan', gateway='2001::1', ipprotocol='inet6')
        msg = "Cannot add IPv6 Gateway Address because no IPv6 address could be found on the interface."
        self.do_module_test(obj, msg=msg, failed=True)

    def test_gateway_create_invalid_ipv6_2(self):
        """ test """
        obj = dict(name='test_gw', interface='wan', gateway='192.168.1.2', ipprotocol='inet6')
        msg = "gateway must use an IPv6 address"
        self.do_module_test(obj, msg=msg, failed=True)

    def test_gateway_create_invalid_ipv6_monitor(self):
        """ test """
        obj = dict(name='test_gw', interface='wan', ipprotocol='inet6', gateway='2001::1', monitor='192.168.1.1')
        msg = 'monitor must use an IPv6 address'
        self.do_module_test(obj, msg=msg, failed=True)

    def test_gateway_create_invalid_weight(self):
        """ test """
        obj = dict(name='test_gw', interface='lan', gateway='192.168.1.1', weight='40')
        msg = 'weight must be between 1 and 30'
        self.do_module_test(obj, msg=msg, failed=True)

    def test_gateway_update_noop(self):
        """ test """
        obj = dict(name='GW_WAN', interface='wan', gateway='192.168.240.1', descr='Interface wan Gateway')
        self.do_module_test(obj, changed=False)

    def test_gateway_update_dynamic(self):
        """ test """
        obj = dict(name='OPT3_VTIV4', interface='lan', gateway='dynamic')
        msg = "The gateway use 'dynamic' as a target. You can not change the interface"
        self.do_module_test(obj, msg=msg, failed=True)

    def test_gateway_update_dynamic2(self):
        """ test """
        obj = dict(name='OPT3_VTIV4', interface='lan_100', gateway='1.2.3.4')
        msg = "The gateway use 'dynamic' as a target. This is read-only, so you must set gateway as dynamic too"
        self.do_module_test(obj, msg=msg, failed=True)

    def test_gateway_update_dynamic3(self):
        """ test """
        obj = dict(name='OPT3_VTIV4', interface='lan_100', gateway='dynamic', ipprotocol='inet6')
        msg = "The gateway use 'dynamic' as a target. You can not change ipprotocol"
        self.do_module_test(obj, msg=msg, failed=True)

    def test_gateway_update_dynamic4(self):
        """ test """
        obj = dict(name='OPT3_VTIV4', interface='lan_100', gateway='dynamic', weight=2)
        command = "update gateway 'OPT3_VTIV4' set weight='2'"
        self.do_module_test(obj, command=command)

    def test_gateway_update_interface(self):
        """ test """
        obj = dict(name='GW_WAN', interface='lan', gateway='192.168.1.1', descr='Interface wan Gateway')
        command = "update gateway 'GW_WAN' set interface='lan', gateway='192.168.1.1'"
        self.do_module_test(obj, command=command)

    def test_gateway_update_bools_and_monitor(self):
        """ test """
        obj = dict(name='GW_LAN', interface='lan', gateway='192.168.1.1', descr='Interface lan Gateway')
        command = "update gateway 'GW_LAN' set disabled=False, monitor=none, monitor_disable=False, action_disable=False, force_down=False"
        self.do_module_test(obj, command=command)

    def test_gateway_delete(self):
        """ test """
        obj = dict(name='GW_WAN2')
        command = "delete gateway 'GW_WAN2'"
        self.do_module_test(obj, command=command, delete=True)

    def test_gateway_delete_static(self):
        """ test """
        obj = dict(name='OPT3_VTIV4')
        msg = "The gateway use 'dynamic' as a target. You can not delete it"
        self.do_module_test(obj, msg=msg, delete=True, failed=True)

    def test_gateway_delete_default(self):
        """ test """
        obj = dict(name='GW_DEFAULT')
        msg = "The gateway is still in use. You can not delete it"
        self.do_module_test(obj, msg=msg, delete=True, failed=True)

    def test_gateway_delete_in_group(self):
        """ test """
        obj = dict(name='GW_LAN')
        msg = "The gateway is still in use. You can not delete it"
        self.do_module_test(obj, msg=msg, delete=True, failed=True)

    def test_gateway_delete_in_route(self):
        """ test """
        obj = dict(name='GW_WAN')
        msg = "The gateway is still in use. You can not delete it"
        self.do_module_test(obj, msg=msg, delete=True, failed=True)
