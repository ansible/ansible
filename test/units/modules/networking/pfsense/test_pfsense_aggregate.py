# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import sys

if sys.version_info < (2, 7):
    pytestmark = pytest.mark.skip("pfSense Ansible modules require Python >= 2.7")

from xml.etree.ElementTree import fromstring, ElementTree

from units.modules.utils import set_module_args
from ansible.modules.networking.pfsense import pfsense_aggregate

from .pfsense_module import TestPFSenseModule, load_fixture


def args_from_var(var, state='present', **kwargs):
    """ return arguments for pfsense_alias module from var """
    args = {}
    for field in ['name', 'address', 'descr', 'type', 'updatefreq', 'detail']:
        if field in var and (state == 'present' or field == 'name'):
            args[field] = var[field]

    args['state'] = state
    for key, value in kwargs.items():
        args[key] = value

    return args


class TestPFSenseAggregateModule(TestPFSenseModule):

    module = pfsense_aggregate

    def load_fixtures(self, commands=None):
        """ loading data """
        config_file = 'pfsense_aggregate_config.xml'
        self.parse.return_value = ElementTree(fromstring(load_fixture(config_file)))

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

    ############
    # as we rely on pfsense_alias and pfsense_rule for modifying the xml
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
        result_separators.append("create rule_separator 'one_separator', interface='lan', color='info'")
        result_separators.append("create rule_separator 'another_separator', interface='lan_100', color='info'")
        result_separators.append("delete rule_separator 'another_test_separator', interface='lan'")
        result_separators.append("update rule_separator 'test_separator' set interface='lan', color='warning', before='bottom'")

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
        result_separators.append("create rule_separator 'one_separator', interface='lan', color='info'")
        result_separators.append("create rule_separator 'another_separator', interface='lan_100', color='info'")
        result_separators.append("delete rule_separator 'another_test_separator', interface='lan'")
        result_separators.append("update rule_separator 'test_separator' set interface='lan', color='warning', before='bottom'")
        result_separators.append("delete rule_separator 'test_separator', interface='wan'")
        result_separators.append("delete rule_separator 'last_test_separator', interface='lan'")
        result_separators.append("delete rule_separator 'test_sep_floating', floating=True")

        self.assertEqual(result['result_rule_separators'], result_separators)
        self.assert_find_rule_separator('one_separator', 'lan')
        self.assert_find_rule_separator('another_separator', 'lan_100')
        self.assert_not_find_rule_separator('another_test_separator', 'lan')
        self.assert_find_rule_separator('test_separator', 'lan')
        self.assert_not_find_rule_separator('last_test_separator', 'lan')
        self.assert_not_find_rule_separator('test_sep_floating', 'floatingrules')
