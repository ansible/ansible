# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import sys

if sys.version_info < (2, 7):
    pytestmark = pytest.mark.skip("pfSense Ansible modules require Python >= 2.7")

from xml.etree.ElementTree import fromstring, ElementTree
from units.compat.mock import patch
from ansible.modules.network.pfsense import pfsense_rule
from .pfsense_module import TestPFSenseModule, load_fixture


def args_from_var(var, state='present', **kwargs):
    """ return arguments for pfsense_rule module from var """
    args = {}
    fields = ['name', 'source', 'destination', 'descr', 'interface', 'action']
    fields.extend(['log', 'disabled', 'floating', 'direction', 'ipprotocol', 'gateway'])
    fields.extend(['protocol', 'statetype', 'after', 'before', 'queue', 'ackqueue', 'in_queue', 'out_queue'])
    for field in fields:
        if field in var:
            args[field] = var[field]

    args['state'] = state
    for key, value in kwargs.items():
        args[key] = value

    return args


class TestPFSenseRuleModule(TestPFSenseModule):

    module = pfsense_rule

    def load_fixtures(self, commands=None):
        """ loading data """
        config_file = 'pfsense_rule_config.xml'
        self.parse.return_value = ElementTree(fromstring(load_fixture(config_file)))

    ########################################################
    # Generic set of funcs used for testing rules
    # First we run the module
    # Then, we check return values
    # Finally, we check the xml
    def parse_address(self, addr):
        """ return address parsed in dict """
        parts = addr.split(':')
        res = {}
        if parts[0][0] == '!':
            res['not'] = None
            parts[0] = parts[0][1:]
        if parts[0] == 'any':
            res['any'] = None
        elif parts[0] == '(self)':
            res['network'] = '(self)'
        elif parts[0] == 'NET':
            res['network'] = self.unalias_interface(parts[1])
            del parts[1]
        elif parts[0] == 'IP':
            res['network'] = self.unalias_interface(parts[1]) + 'ip'
            del parts[1]
        elif parts[0] in ['lan', 'lan', 'vpn', 'vt1', 'lan_100']:
            res['network'] = self.unalias_interface(parts[0])
        else:
            res['address'] = parts[0]

        if len(parts) > 1:
            res['port'] = parts[1]

        return res

    def check_rule_elt_addr(self, rule, rule_elt, addr):
        """ test the addresses definition of rule """
        addr_dict = self.parse_address(rule[addr])
        addr_elt = self.assert_find_xml_elt(rule_elt, addr)
        for key, value in addr_dict.items():
            self.assert_xml_elt_equal(addr_elt, key, value)
        if 'any' in addr_dict:
            self.assert_not_find_xml_elt(addr_elt, 'address')
            self.assert_not_find_xml_elt(addr_elt, 'network')
        if 'network' in addr_dict:
            self.assert_not_find_xml_elt(addr_elt, 'address')
            self.assert_not_find_xml_elt(addr_elt, 'any')
        if 'address' in addr_dict:
            self.assert_not_find_xml_elt(addr_elt, 'network')
            self.assert_not_find_xml_elt(addr_elt, 'any')

        if 'not' not in addr_dict:
            self.assert_not_find_xml_elt(addr_elt, 'not')

    def get_target_elt(self, rule, absent=False):
        rule['interface'] = self.unalias_interface(rule['interface'])
        if 'floating' in rule and rule['floating'] == 'yes':
            return self.assert_has_xml_tag('filter', dict(descr=rule['name'], floating='yes'))
        return self.assert_has_xml_tag('filter', dict(descr=rule['name'], interface=rule['interface']))

    def check_target_elt(self, rule, rule_elt):
        """ test the xml definition of rule """

        # checking source address and ports
        self.check_rule_elt_addr(rule, rule_elt, 'source')

        # checking destination address and ports
        self.check_rule_elt_addr(rule, rule_elt, 'destination')

        # checking log option
        if 'log' in rule and rule['log'] == 'yes':
            self.assert_xml_elt_is_none_or_empty(rule_elt, 'log')
        elif 'log' not in rule or rule['log'] == 'no':
            self.assert_not_find_xml_elt(rule_elt, 'log')

        # checking action option
        if 'action' in rule:
            action = rule['action']
        else:
            action = 'pass'
        self.assert_xml_elt_equal(rule_elt, 'type', action)

        # checking floating option
        if 'floating' in rule and rule['floating'] == 'yes':
            self.assert_xml_elt_equal(rule_elt, 'floating', 'yes')
        elif 'floating' not in rule or rule['floating'] == 'no':
            self.assert_not_find_xml_elt(rule_elt, 'floating')

        # checking direction option
        self.check_param_equal_or_not_find(rule, rule_elt, 'direction')

        # checking default queue option
        self.check_param_equal_or_not_find(rule, rule_elt, 'queue', 'defaultqueue')

        # checking acknowledge queue option
        self.check_param_equal_or_not_find(rule, rule_elt, 'ackqueue')

        # limiters
        self.check_param_equal_or_not_find(rule, rule_elt, 'in_queue', 'dnpipe')
        self.check_param_equal_or_not_find(rule, rule_elt, 'out_queue', 'pdnpipe')

        # checking ipprotocol option
        if 'ipprotocol' in rule:
            action = rule['ipprotocol']
        else:
            action = 'inet'
        self.assert_xml_elt_equal(rule_elt, 'ipprotocol', action)

        # checking protocol option
        if 'protocol' in rule and rule['protocol'] != 'any':
            self.assert_xml_elt_equal(rule_elt, 'protocol', rule['protocol'])
        else:
            self.assert_not_find_xml_elt(rule_elt, 'protocol')

        # checking statetype option
        if 'statetype' in rule and rule['statetype'] != 'keep state':
            statetype = rule['statetype']
        else:
            statetype = 'keep state'
        self.assert_xml_elt_equal(rule_elt, 'statetype', statetype)

        # checking disabled option
        if 'disabled' in rule and rule['disabled'] == 'yes':
            self.assert_xml_elt_is_none_or_empty(rule_elt, 'disabled')
        elif 'disabled' not in rule or rule['disabled'] == 'no':
            self.assert_not_find_xml_elt(rule_elt, 'disabled')

        # checking gateway option
        if 'gateway' in rule and rule['gateway'] != 'default':
            self.assert_xml_elt_equal(rule_elt, 'gateway', rule['gateway'])
        else:
            self.assert_not_find_xml_elt(rule_elt, 'gateway')

    def check_rule_idx(self, rule, target_idx):
        """ test the xml position of rule """
        floating = 'floating' in rule and rule['floating'] == 'yes'
        rule['interface'] = self.unalias_interface(rule['interface'])
        rules_elt = self.assert_find_xml_elt(self.xml_result, 'filter')
        idx = -1
        for rule_elt in rules_elt:
            interface_elt = rule_elt.find('interface')
            floating_elt = rule_elt.find('floating')
            floating_rule = floating_elt is not None and floating_elt.text == 'yes'
            if floating and not floating_rule:
                continue
            elif not floating:
                if floating_rule or interface_elt is None or interface_elt.text is None or interface_elt.text != rule['interface']:
                    continue
            idx += 1
            descr_elt = rule_elt.find('descr')
            self.assertIsNotNone(descr_elt)
            self.assertIsNotNone(descr_elt.text)
            if descr_elt.text == rule['name']:
                self.assertEqual(idx, target_idx)
                return
        self.fail('rule not found ' + str(idx))

    def check_separator_idx(self, interface, sep_name, expected_idx):
        """ test the logical position of separator """
        filter_elt = self.assert_find_xml_elt(self.xml_result, 'filter')
        separator_elt = self.assert_find_xml_elt(filter_elt, 'separator')
        iface_elt = self.assert_find_xml_elt(separator_elt, interface)
        for separator in iface_elt:
            text_elt = separator.find('text')
            if text_elt is not None and text_elt.text == sep_name:
                row_elt = self.assert_find_xml_elt(separator, 'row')
                idx = int(row_elt.text.replace('fr', ''))
                if idx != expected_idx:
                    self.fail('Idx of separator ' + sep_name + ' if wrong: ' + str(idx) + ', expected: ' + str(expected_idx))
                return
        self.fail('Separator ' + sep_name + 'not found on interface ' + interface)
