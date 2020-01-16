# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import sys

if sys.version_info < (2, 7):
    pytestmark = pytest.mark.skip("pfSense Ansible modules require Python >= 2.7")

from units.modules.utils import set_module_args
from ansible.modules.network.pfsense import pfsense_aggregate
from .pfsense_module import TestPFSenseModule


class TestPFSenseAggregateModule(TestPFSenseModule):

    module = pfsense_aggregate

    def __init__(self, *args, **kwargs):
        super(TestPFSenseAggregateModule, self).__init__(*args, **kwargs)
        self.config_file = 'pfsense_aggregate_config.xml'

    def assert_find_alias(self, alias):
        """ test if an alias exist """
        self.load_xml_result()
        parent_tag = self.xml_result.find('aliases')
        if parent_tag is None:
            self.fail('Unable to find tag aliases')

        tag = self.find_xml_tag(parent_tag, dict(name=alias))
        if tag is None:
            self.fail('Alias not found: ' + alias)

    def assert_not_find_alias(self, alias):
        """ test if an alias does not exist """
        self.load_xml_result()
        parent_tag = self.xml_result.find('aliases')
        if parent_tag is None:
            self.fail('Unable to find tag aliases')

        tag = self.find_xml_tag(parent_tag, dict(name=alias))
        if tag is not None:
            self.fail('Alias found: ' + alias)

    def assert_find_rule(self, rule, interface):
        """ test if a rule exist on interface """
        self.load_xml_result()
        parent_tag = self.xml_result.find('filter')
        if parent_tag is None:
            self.fail('Unable to find tag filter')

        tag = self.find_xml_tag(parent_tag, dict(descr=rule, interface=interface))
        if tag is None:
            self.fail('Rule not found: ' + rule)

    def assert_not_find_rule(self, rule, interface):
        """ test if a rule does not exist on interface """
        self.load_xml_result()
        parent_tag = self.xml_result.find('filter')
        if parent_tag is None:
            self.fail('Unable to find tag filter')

        tag = self.find_xml_tag(parent_tag, dict(descr=rule, interface=interface))
        if tag is not None:
            self.fail('Rule found: ' + rule)

    def assert_find_rule_separator(self, separator, interface):
        """ test if a rule separator exist on interface """
        self.load_xml_result()
        interface = self.unalias_interface(interface)
        parent_tag = self.xml_result.find('filter')
        if parent_tag is None:
            self.fail('Unable to find tag filter')

        separators_elt = parent_tag.find('separator')
        if parent_tag is None:
            self.fail('Unable to find tag separator')

        interface_elt = separators_elt.find(interface)
        if parent_tag is None:
            self.fail('Unable to find tag ' + interface)

        tag = self.find_xml_tag(interface_elt, dict(text=separator))
        if tag is None:
            self.fail('Separator not found: ' + separator)

    def assert_not_find_rule_separator(self, separator, interface):
        """ test if a rule separator dost exist on interface """
        self.load_xml_result()
        interface = self.unalias_interface(interface)
        parent_tag = self.xml_result.find('filter')
        if parent_tag is None:
            self.fail('Unable to find tag filter')

        separators_elt = parent_tag.find('separator')
        if parent_tag is None:
            self.fail('Unable to find tag separator')

        interface_elt = separators_elt.find(interface)
        if parent_tag is None:
            self.fail('Unable to find tag ' + interface)

        tag = self.find_xml_tag(interface_elt, dict(text=separator))
        if tag is not None:
            self.fail('Separator found: ' + separator)

    def assert_find_vlan(self, interface, vlan_id):
        """ test if a vlan exist """
        self.load_xml_result()
        parent_tag = self.xml_result.find('vlans')
        if parent_tag is None:
            self.fail('Unable to find tag vlans')

        elt_filter = {}
        elt_filter['if'] = interface
        elt_filter['tag'] = vlan_id
        tag = self.find_xml_tag(parent_tag, elt_filter)
        if tag is None:
            self.fail('Vlan not found: {0}.{1}'.format(interface, vlan_id))

    def assert_not_find_vlan(self, interface, vlan_id):
        """ test if an vlan does not exist """
        self.load_xml_result()
        parent_tag = self.xml_result.find('vlans')
        if parent_tag is None:
            self.fail('Unable to find tag vlans')

        elt_filter = {}
        elt_filter['if'] = interface
        elt_filter['vlan_id'] = vlan_id
        tag = self.find_xml_tag(parent_tag, elt_filter)
        if tag is not None:
            self.fail('Vlan found: {0}.{1}'.format(interface, vlan_id))

    ############
    # as we rely on sub modules for modifying the xml
    # we dont perform extensive checks on the xml modifications
    # we just test if elements are created or deleted, and the respective output
    def test_aggregate_aliases(self):
        """ test creation of a some aliases """
        args = dict(
            purge_aliases=False,
            aggregated_aliases=[
                dict(name='one_host', type='host', address='10.9.8.7'),
                dict(name='another_host', type='host', address='10.9.8.6'),
                dict(name='one_server', type='host', address='192.168.1.165', descr='', detail=''),
                dict(name='port_ssh', type='port', address='2222'),
                dict(name='port_http', state='absent'),
            ]
        )
        set_module_args(args)
        result = self.execute_module(changed=True)
        result_aliases = []
        result_aliases.append("create alias 'one_host', type='host', address='10.9.8.7'")
        result_aliases.append("create alias 'another_host', type='host', address='10.9.8.6'")
        result_aliases.append("update alias 'port_ssh' set address='2222', descr=none, detail=none")
        result_aliases.append("delete alias 'port_http'")

        self.assertEqual(result['result_aliases'], result_aliases)
        self.assert_find_alias('one_host')
        self.assert_find_alias('another_host')
        self.assert_find_alias('one_server')
        self.assert_find_alias('port_ssh')
        self.assert_not_find_alias('port_http')
        self.assert_find_alias('port_dns')

    def test_aggregate_aliases_checkmode(self):
        """ test creation of a some aliases with check_mode """
        args = dict(
            purge_aliases=False,
            aggregated_aliases=[
                dict(name='one_host', type='host', address='10.9.8.7'),
                dict(name='another_host', type='host', address='10.9.8.6'),
                dict(name='one_server', type='host', address='192.168.1.165', descr='', detail=''),
                dict(name='port_ssh', type='port', address='2222'),
                dict(name='port_http', state='absent'),
            ],
            _ansible_check_mode=True,
        )
        set_module_args(args)
        result = self.execute_module(changed=True)
        result_aliases = []
        result_aliases.append("create alias 'one_host', type='host', address='10.9.8.7'")
        result_aliases.append("create alias 'another_host', type='host', address='10.9.8.6'")
        result_aliases.append("update alias 'port_ssh' set address='2222', descr=none, detail=none")
        result_aliases.append("delete alias 'port_http'")

        self.assertEqual(result['result_aliases'], result_aliases)
        self.assertFalse(self.load_xml_result())

    def test_aggregate_aliases_purge(self):
        """ test creation of a some aliases with purge """
        args = dict(
            purge_aliases=True,
            purge_rules=False,
            aggregated_aliases=[
                dict(name='one_host', type='host', address='10.9.8.7'),
                dict(name='another_host', type='host', address='10.9.8.6'),
                dict(name='one_server', type='host', address='192.168.1.165', descr='', detail=''),
                dict(name='port_ssh', type='port', address='2222'),
                dict(name='port_http', state='absent'),
            ]
        )
        set_module_args(args)
        result = self.execute_module(changed=True)
        result_aliases = []
        result_aliases.append("create alias 'one_host', type='host', address='10.9.8.7'")
        result_aliases.append("create alias 'another_host', type='host', address='10.9.8.6'")
        result_aliases.append("update alias 'port_ssh' set address='2222', descr=none, detail=none")
        result_aliases.append("delete alias 'port_http'")
        result_aliases.append("delete alias 'port_dns'")

        self.assertEqual(result['result_aliases'], result_aliases)
        self.assert_find_alias('one_host')
        self.assert_find_alias('another_host')
        self.assert_find_alias('one_server')
        self.assert_find_alias('port_ssh')
        self.assert_not_find_alias('port_http')
        self.assert_not_find_alias('port_dns')

    def test_aggregate_rules(self):
        """ test creation of a some rules """
        args = dict(
            purge_rules=False,
            aggregated_rules=[
                dict(name='one_rule', source='any', destination='any', interface='lan'),
                dict(name='any2any_ssh', source='any', destination='any:2222', interface='lan'),
                dict(name='any2any_http', source='any', destination='any:8080', interface='vpn'),
                dict(name='any2any_ssh', state='absent', interface='vpn'),
            ]
        )
        set_module_args(args)
        self.execute_module(changed=True)
        self.assert_find_rule('one_rule', 'lan')
        self.assert_find_rule('any2any_ssh', 'lan')
        self.assert_find_rule('any2any_http', 'lan')
        self.assert_find_rule('any2any_https', 'lan')
        self.assert_not_find_rule('any2any_ssh', 'opt1')
        self.assert_find_rule('any2any_http', 'opt1')
        self.assert_find_rule('any2any_https', 'opt1')

    def test_aggregate_rules_purge(self):
        """ test creation of a some rules with purge """
        args = dict(
            purge_rules=True,
            aggregated_rules=[
                dict(name='one_rule', source='any', destination='any', interface='lan'),
                dict(name='any2any_ssh', source='any', destination='any:2222', interface='lan'),
                dict(name='any2any_http', source='any', destination='any:8080', interface='vpn'),
                dict(name='any2any_ssh', state='absent', interface='vpn'),
            ]
        )
        set_module_args(args)
        self.execute_module(changed=True)
        self.assert_find_rule('one_rule', 'lan')
        self.assert_find_rule('any2any_ssh', 'lan')
        self.assert_not_find_rule('any2any_http', 'lan')
        self.assert_not_find_rule('any2any_https', 'lan')
        self.assert_not_find_rule('any2any_ssh', 'opt1')
        self.assert_find_rule('any2any_http', 'opt1')
        self.assert_not_find_rule('any2any_https', 'opt1')

    def test_aggregate_separators(self):
        """ test creation of a some separators """
        args = dict(
            purge_rule_separators=False,
            aggregated_rule_separators=[
                dict(name='one_separator', interface='lan'),
                dict(name='another_separator', interface='lan_100'),
                dict(name='another_test_separator', interface='lan', state='absent'),
                dict(name='test_separator', interface='lan', before='bottom', color='warning'),
            ]
        )
        set_module_args(args)
        result = self.execute_module(changed=True)
        result_separators = []
        result_separators.append("create rule_separator 'one_separator' on 'lan', color='info'")
        result_separators.append("create rule_separator 'another_separator' on 'lan_100', color='info'")
        result_separators.append("delete rule_separator 'another_test_separator' on 'lan'")
        result_separators.append("update rule_separator 'test_separator' on 'lan' set color='warning', before='bottom'")

        self.assertEqual(result['result_rule_separators'], result_separators)
        self.assert_find_rule_separator('one_separator', 'lan')
        self.assert_find_rule_separator('another_separator', 'lan_100')
        self.assert_not_find_rule_separator('another_test_separator', 'lan')
        self.assert_find_rule_separator('test_separator', 'lan')

    def test_aggregate_separators_purge(self):
        """ test creation of a some separators with purge """
        args = dict(
            purge_rule_separators=True,
            aggregated_rule_separators=[
                dict(name='one_separator', interface='lan'),
                dict(name='another_separator', interface='lan_100'),
                dict(name='another_test_separator', interface='lan', state='absent'),
                dict(name='test_separator', interface='lan', before='bottom', color='warning'),
            ]
        )
        set_module_args(args)
        result = self.execute_module(changed=True)
        result_separators = []
        result_separators.append("create rule_separator 'one_separator' on 'lan', color='info'")
        result_separators.append("create rule_separator 'another_separator' on 'lan_100', color='info'")
        result_separators.append("delete rule_separator 'another_test_separator' on 'lan'")
        result_separators.append("update rule_separator 'test_separator' on 'lan' set color='warning', before='bottom'")
        result_separators.append("delete rule_separator 'test_separator' on 'wan'")
        result_separators.append("delete rule_separator 'last_test_separator' on 'lan'")
        result_separators.append("delete rule_separator 'test_sep_floating' on 'floating'")

        self.assertEqual(result['result_rule_separators'], result_separators)
        self.assert_find_rule_separator('one_separator', 'lan')
        self.assert_find_rule_separator('another_separator', 'lan_100')
        self.assert_not_find_rule_separator('another_test_separator', 'lan')
        self.assert_find_rule_separator('test_separator', 'lan')
        self.assert_not_find_rule_separator('last_test_separator', 'lan')
        self.assert_not_find_rule_separator('test_sep_floating', 'floatingrules')

    def test_aggregate_vlans(self):
        """ test creation of some vlans """
        args = dict(
            purge_vlans=False,
            aggregated_vlans=[
                dict(vlan_id=100, interface='vmx0', descr='voice'),
                dict(vlan_id=1200, interface='vmx1', state='absent'),
                dict(vlan_id=101, interface='vmx1', descr='printers'),
                dict(vlan_id=102, interface='vmx2', descr='users'),
            ]
        )
        set_module_args(args)
        result = self.execute_module(changed=True)
        result_aliases = []
        result_aliases.append("update vlan 'vmx0.100' set descr='voice'")
        result_aliases.append("delete vlan 'vmx1.1200'")
        result_aliases.append("create vlan 'vmx1.101', descr='printers', priority=''")
        result_aliases.append("create vlan 'vmx2.102', descr='users', priority=''")

        self.assertEqual(result['result_vlans'], result_aliases)
        self.assert_find_vlan('vmx0', '100')
        self.assert_not_find_vlan('vmx1', '1200')
        self.assert_find_vlan('vmx1', '101')
        self.assert_find_vlan('vmx2', '102')

    def test_aggregate_vlans_with_purge(self):
        """ test creation of some vlans with purge"""
        args = dict(
            purge_vlans=True,
            aggregated_vlans=[
                dict(vlan_id=1100, interface='vmx1'),
                dict(vlan_id=1200, interface='vmx1', state='absent'),
                dict(vlan_id=101, interface='vmx1', descr='printers'),
                dict(vlan_id=102, interface='vmx2', descr='users'),
            ]
        )
        set_module_args(args)
        result = self.execute_module(changed=True)
        result_aliases = []
        result_aliases.append("delete vlan 'vmx1.1200'")
        result_aliases.append("create vlan 'vmx1.101', descr='printers', priority=''")
        result_aliases.append("create vlan 'vmx2.102', descr='users', priority=''")
        result_aliases.append("delete vlan 'vmx0.100'")

        self.assertEqual(result['result_vlans'], result_aliases)
        self.assert_not_find_vlan('vmx1', '1200')
        self.assert_find_vlan('vmx1', '101')
        self.assert_find_vlan('vmx2', '102')
        self.assert_not_find_vlan('vmx0', '100')
