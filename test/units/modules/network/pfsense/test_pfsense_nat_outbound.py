# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import sys

if sys.version_info < (2, 7):
    pytestmark = pytest.mark.skip("pfSense Ansible modules require Python >= 2.7")

from ansible.modules.network.pfsense import pfsense_nat_outbound
from .pfsense_module import TestPFSenseModule
from ansible.module_utils.compat.ipaddress import ip_address, IPv4Address


class TestPFSenseNatOutboutModule(TestPFSenseModule):

    module = pfsense_nat_outbound

    def __init__(self, *args, **kwargs):
        super(TestPFSenseNatOutboutModule, self).__init__(*args, **kwargs)
        self.config_file = 'pfsense_nat_outbound.xml'

    @staticmethod
    def get_args_fields():
        """ return params fields """
        fields = ['descr', 'interface', 'disabled', 'nonat', 'interface', 'ipprotocol', 'protocol', 'source']
        fields += ['destination', 'invert', 'address', 'poolopts', 'source_hash_key', 'staticnatport', 'nosync']
        fields += ['after', 'before']
        return fields

    @staticmethod
    def is_ipv4_address(address):
        """ test if address is a valid ipv4 address """
        try:
            addr = ip_address(u'{0}'.format(address))
            return isinstance(addr, IPv4Address)
        except ValueError:
            pass
        return False

    def parse_address(self, addr, field):
        """ return address parsed in dict """
        parts = addr.split(':')
        res = {}
        port = None
        if parts[0] == 'any':
            if field == 'network':
                res[field] = 'any'
            else:
                res['any'] = None
        elif parts[0] == '(self)':
            res[field] = '(self)'
        elif parts[0] in ['lan', 'vpn', 'vt1', 'lan_100']:
            res[field] = self.unalias_interface(parts[0])
        else:
            res[field] = parts[0]

        if field in res and self.is_ipv4_address(res[field]) and res[field].find('/') == -1:
            res[field] += '/32'

        if len(parts) > 1:
            port = parts[1].replace('-', ':')

        return (res, port)

    @staticmethod
    def reparse_network(value):
        if value == '1.2.3.4/24':
            return '1.2.3.0/24'
        elif value == '2.3.4.5/24':
            return '2.3.4.0/24'
        return value

    def check_addr(self, params, target_elt, addr, field, port):
        """ test the addresses definition """
        (addr_dict, port_value) = self.parse_address(params[addr], field)
        addr_elt = self.assert_find_xml_elt(target_elt, addr)
        for key, value in addr_dict.items():
            self.check_value_equal(addr_elt, key, self.reparse_network(value))
            # self.assert_xml_elt_equal(addr_elt, key, value)
        for item_elt in addr_elt:
            self.assertTrue(item_elt.tag in addr_dict)

        self.check_value_equal(target_elt, port, port_value, port == 'sourceport')

    def check_target_addr(self, params, target_elt):
        """ test the addresses definition """
        if 'address' not in params or params['address'] == '':
            self.assert_xml_elt_is_none_or_empty(target_elt, 'target')
            self.assert_xml_elt_is_none_or_empty(target_elt, 'targetip')
            self.assert_xml_elt_is_none_or_empty(target_elt, 'targetip_subnet')
            self.assert_not_find_xml_elt(target_elt, 'natport')
        elif params['address'] == '4.5.6.7:888-999':
            self.assert_xml_elt_equal(target_elt, 'target', 'other-subnet')
            self.assert_xml_elt_equal(target_elt, 'targetip', '4.5.6.7')
            self.assert_xml_elt_equal(target_elt, 'targetip_subnet', '32')
            self.assert_xml_elt_equal(target_elt, 'natport', '888:999')
        elif params['address'] == '4.5.6.7/24:888-999':
            self.assert_xml_elt_equal(target_elt, 'target', 'other-subnet')
            self.assert_xml_elt_equal(target_elt, 'targetip', '4.5.6.0')
            self.assert_xml_elt_equal(target_elt, 'targetip_subnet', '24')
            self.assert_xml_elt_equal(target_elt, 'natport', '888:999')

    @staticmethod
    def md5(value):
        if value == 'acme_key':
            return '0xfdc529cc680c4e8c74efbf114ec436fb'
        return value

    def check_target_elt(self, params, target_elt, target_idx=-1):
        """ test the xml definition """
        self.check_addr(params, target_elt, 'source', 'network', 'sourceport')
        self.check_addr(params, target_elt, 'destination', 'address', 'dstport')
        self.check_target_addr(params, target_elt)

        self.check_param_equal_or_not_find(params, target_elt, 'disabled')
        self.check_param_equal_or_not_find(params, target_elt, 'nonat')
        self.check_param_equal_or_not_find(params, target_elt, 'invert')
        self.check_param_equal_or_not_find(params, target_elt, 'staticnatport')
        self.check_param_equal_or_not_find(params, target_elt, 'nosync')
        self.check_param_equal_or_not_find(params, target_elt, 'nonat')

        self.check_value_equal(target_elt, 'interface', self.unalias_interface(params['interface']))
        self.check_param_equal(params, target_elt, 'ipprotocol', 'inet46', not_find_val='inet46')
        self.check_param_equal(params, target_elt, 'protocol', 'any', not_find_val='any')
        self.check_param_equal(params, target_elt, 'poolopts')
        self.check_value_equal(target_elt, 'source_hash_key', self.md5(params.get('source_hash_key')))

        self.check_rule_idx(params, target_idx)

    def check_rule_idx(self, params, target_idx):
        """ test the xml position """
        nat_elt = self.assert_find_xml_elt(self.xml_result, 'nat')
        rules_elt = self.assert_find_xml_elt(nat_elt, 'outbound')

        idx = -1
        for rule_elt in rules_elt:
            if rule_elt.tag != 'rule':
                continue
            idx += 1
            descr_elt = rule_elt.find('descr')
            self.assertIsNotNone(descr_elt)
            self.assertIsNotNone(descr_elt.text)
            if descr_elt.text == params['descr']:
                self.assertEqual(idx, target_idx)
                return
        self.fail('rule not found ' + str(idx))

    def get_target_elt(self, obj, absent=False):
        """ get the generated xml definition """
        nat_elt = self.assert_find_xml_elt(self.xml_result, 'nat')
        outbount_elt = self.assert_find_xml_elt(nat_elt, 'outbound')

        for item in outbount_elt:
            descr_elt = item.find('descr')
            if descr_elt is not None and descr_elt.text == obj['descr']:
                return item

        return None

    ##############
    # tests
    #
    def test_nat_outbound_create(self):
        """ test """
        obj = dict(descr='https-source-rewriting', interface='lan', source='any', destination='1.2.3.4:443')
        command = "create nat_outbound 'https-source-rewriting', interface='lan', source='any', destination='1.2.3.4:443'"
        self.do_module_test(obj, command=command, target_idx=3)

    def test_nat_outbound_create_aliases(self):
        """ test """
        obj = dict(descr='https-source-rewriting', interface='lan', source='srv_admin:port_ssh', destination='srv_admin:port_ssh', address='srv_admin:port_ssh')
        command = (
            "create nat_outbound 'https-source-rewriting', interface='lan', source='srv_admin:port_ssh', "
            "destination='srv_admin:port_ssh', address='srv_admin:port_ssh'"
        )
        self.do_module_test(obj, command=command, target_idx=3)

    def test_nat_outbound_create_address(self):
        """ test """
        obj = dict(descr='https-source-rewriting', interface='lan', source='any', destination='1.2.3.4:443', address='4.5.6.7:888-999')
        command = "create nat_outbound 'https-source-rewriting', interface='lan', source='any', destination='1.2.3.4:443', address='4.5.6.7/32:888-999'"
        self.do_module_test(obj, command=command, target_idx=3)

    def test_nat_outbound_create_address_net(self):
        """ test """
        obj = dict(descr='https-source-rewriting', interface='lan', source='any', destination='1.2.3.4:443', address='4.5.6.7/24:888-999')
        command = "create nat_outbound 'https-source-rewriting', interface='lan', source='any', destination='1.2.3.4:443', address='4.5.6.0/24:888-999'"
        self.do_module_test(obj, command=command, target_idx=3)

    def test_nat_outbound_create_networks(self):
        """ test """
        obj = dict(descr='https-source-rewriting', interface='lan', source='1.2.3.4/24', destination='2.3.4.5/24:443')
        command = "create nat_outbound 'https-source-rewriting', interface='lan', source='1.2.3.4/24', destination='2.3.4.5/24:443'"
        self.do_module_test(obj, command=command, target_idx=3)

    def test_nat_outbound_create_top(self):
        """ test """
        obj = dict(descr='https-source-rewriting', interface='lan', source='any', destination='1.2.3.4:443', after='top')
        command = "create nat_outbound 'https-source-rewriting', interface='lan', source='any', destination='1.2.3.4:443', after='top'"
        self.do_module_test(obj, command=command, target_idx=0)

    def test_nat_outbound_create_after(self):
        """ test """
        obj = dict(descr='https-source-rewriting', interface='lan', source='any', destination='1.2.3.4:443', after='one rule')
        command = "create nat_outbound 'https-source-rewriting', interface='lan', source='any', destination='1.2.3.4:443', after='one rule'"
        self.do_module_test(obj, command=command, target_idx=1)

    def test_nat_outbound_create_before(self):
        """ test """
        obj = dict(descr='https-source-rewriting', interface='lan', source='any', destination='1.2.3.4:443', before='another rule')
        command = "create nat_outbound 'https-source-rewriting', interface='lan', source='any', destination='1.2.3.4:443', before='another rule'"
        self.do_module_test(obj, command=command, target_idx=1)

    def test_nat_outbound_create_with_sourcehashkey(self):
        """ test """
        obj = dict(descr='valid', interface='lan', source='any', destination='1.2.3.4:443', source_hash_key='0x12345678901234567890123456789012')
        command = "create nat_outbound 'valid', interface='lan', source='any', destination='1.2.3.4:443', source_hash_key='0x12345678901234567890123456789012'"
        self.do_module_test(obj, command=command, target_idx=3)

    def test_nat_outbound_create_with_sourcehashkey_str(self):
        """ test """
        obj = dict(descr='valid', interface='lan', source='any', destination='1.2.3.4:443', source_hash_key='acme_key')
        command = "create nat_outbound 'valid', interface='lan', source='any', destination='1.2.3.4:443', source_hash_key='0xfdc529cc680c4e8c74efbf114ec436fb'"
        self.do_module_test(obj, command=command, target_idx=3)

    def test_nat_outbound_update_noop(self):
        """ test """
        obj = dict(descr='one rule', interface='wan', source='any', destination='any')
        self.do_module_test(obj, target_idx=0, changed=False)

    def test_nat_outbound_update_bottom(self):
        """ test """
        obj = dict(descr='one rule', interface='wan', source='any', destination='any', before='bottom')
        command = "update nat_outbound 'one rule' set before='bottom'"
        self.do_module_test(obj, command=command, target_idx=2)

    def test_nat_outbound_update_top(self):
        """ test """
        obj = dict(descr='another rule', interface='wan', source='any', destination='any', after='top')
        command = "update nat_outbound 'another rule' set after='top'"
        self.do_module_test(obj, command=command, target_idx=0)

    def test_nat_outbound_update_source(self):
        """ test """
        obj = dict(descr='one rule', interface='wan', source='(self):123', destination='any')
        command = "update nat_outbound 'one rule' set source='(self):123'"
        self.do_module_test(obj, command=command, target_idx=0)

    def test_nat_outbound_update_destination(self):
        """ test """
        obj = dict(descr='one rule', interface='wan', source='any', destination='1.2.3.4:555')
        command = "update nat_outbound 'one rule' set destination='1.2.3.4/32:555'"
        self.do_module_test(obj, command=command, target_idx=0)

    def test_nat_outbound_update_interface(self):
        """ test """
        obj = dict(descr='one rule', interface='lan_100', source='any', destination='any')
        command = "update nat_outbound 'one rule' set interface='lan_100'"
        self.do_module_test(obj, command=command, target_idx=0)

    def test_nat_outbound_delete(self):
        """ test """
        obj = dict(descr='one rule')
        command = "delete nat_outbound 'one rule'"
        self.do_module_test(obj, command=command, delete=True)

    def test_nat_outbound_invalid_sourcehashkey_hex(self):
        """ test """
        obj = dict(descr='invalid', interface='lan', source='any', destination='1.2.3.4:443', source_hash_key='0xg2345678901234567890123456789012')
        msg = 'Incorrect format for source-hash key, "0x" must be followed by exactly 32 hexadecimal characters.'
        self.do_module_test(obj, msg=msg, failed=True)

    def test_nat_outbound_invalid_sourcehashkey_len(self):
        """ test """
        obj = dict(descr='invalid', interface='lan', source='any', destination='1.2.3.4:443', source_hash_key='0x1234567890123456789012345678901')
        msg = 'Incorrect format for source-hash key, "0x" must be followed by exactly 32 hexadecimal characters.'
        self.do_module_test(obj, msg=msg, failed=True)
