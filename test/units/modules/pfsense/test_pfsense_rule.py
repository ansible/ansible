# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest

from copy import copy
from xml.etree.ElementTree import fromstring, ElementTree

from units.compat.mock import patch
from units.modules.utils import set_module_args
from ansible.modules.pfsense import pfsense_rule

from .pfsense_module import TestPFSenseModule, load_fixture


def args_from_var(var, state='present', **kwargs):
    """ return arguments for pfsense_rule module from var """
    args = {}
    fields = ['name', 'source', 'destination', 'descr', 'interface', 'action']
    fields.extend(['log', 'disabled', 'floating', 'direction', 'ipprotocol'])
    fields.extend(['protocol', 'statetype', 'after', 'before'])
    for field in fields:
        if field in var:
            args[field] = var[field]

    args['state'] = state
    for key, value in kwargs.items():
        args[key] = value

    return args


class TestPFSenseRuleModule(TestPFSenseModule):

    module = pfsense_rule

    def setUp(self):
        """ mocking up """
        super(TestPFSenseRuleModule, self).setUp()

        self.mock_parse = patch('xml.etree.ElementTree.parse')
        self.parse = self.mock_parse.start()

        self.mock_shutil_move = patch('shutil.move')
        self.shutil_move = self.mock_shutil_move.start()

        self.mock_phpshell = patch('ansible.module_utils.pfsense.pfsense.PFSenseModule.phpshell')
        self.phpshell = self.mock_phpshell.start()
        self.phpshell.return_value = (0, '', '')

        self.maxDiff = None

    def tearDown(self):
        """ mocking down """
        super(TestPFSenseRuleModule, self).tearDown()

        self.mock_parse.stop()
        self.mock_shutil_move.stop()
        self.mock_phpshell.stop()

    def load_fixtures(self, commands=None):
        """ loading data """
        config_file = 'pfsense_rule_config.xml'
        self.parse.return_value = ElementTree(fromstring(load_fixture(config_file)))

    ########################################################
    # Generic set of funcs used for testing rules
    # First we run the module
    # Then, we check return values
    # Finally, we check the xml
    @staticmethod
    def unalias_interface(interface):
        """ return real alias name if required """
        interfaces = dict(lan='lan', wan='wan', vpn='opt1', vt1='opt2', lan_100='opt3')
        if interface in interfaces:
            return interfaces[interface]
        return interface

    def parse_address(self, addr):
        """ return address parsed in dict """
        parts = addr.split(':')
        res = {}
        if parts[0] == 'any':
            res['any'] = None
        elif parts[0] == '(self)':
            res['network'] = '(self)'
        elif parts[0] == 'NET':
            res['network'] = parts[1]
            return res
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

    def check_rule_elt(self, rule):
        """ test the xml definition of rule """
        rule['interface'] = self.unalias_interface(rule['interface'])
        rule_elt = self.assert_has_xml_tag('filter', dict(descr=rule['name'], interface=rule['interface']))

        # checking source address and ports
        self.check_rule_elt_addr(rule, rule_elt, 'source')

        # checking destination address and ports
        self.check_rule_elt_addr(rule, rule_elt, 'destination')

        # checking log option
        if 'log' in rule and rule['log'] == 'yes':
            self.assert_xml_elt_is_none(rule_elt, 'log')
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
        if 'direction' in rule:
            self.assert_xml_elt_equal(rule_elt, 'direction', rule['direction'])
        else:
            self.assert_not_find_xml_elt(rule_elt, 'direction')

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

    def check_rule_idx(self, rule, target_idx):
        """ test the xml position of rule """
        rule['interface'] = self.unalias_interface(rule['interface'])
        rules_elt = self.assert_find_xml_elt(self.xml_result, 'filter')
        idx = -1
        for rule_elt in rules_elt:
            interface_elt = rule_elt.find('interface')
            if interface_elt is None or interface_elt.text is None or interface_elt.text != rule['interface']:
                continue
            idx += 1
            descr_elt = rule_elt.find('descr')
            self.assertIsNotNone(descr_elt)
            self.assertIsNotNone(descr_elt.text)
            if descr_elt.text == rule['name']:
                self.assertEqual(idx, target_idx)
                return
        self.fail('rule not found ' + str(idx))

    def do_rule_creation_test(self, rule, failed=False):
        """ test creation of a new rule """
        set_module_args(args_from_var(rule))
        self.execute_module(changed=True, failed=failed)
        if failed:
            self.assertFalse(self.load_xml_result())
        else:
            self.check_rule_elt(rule)

    def do_rule_deletion_test(self, rule):
        """ test deletion of a rule """
        set_module_args(args_from_var(rule, 'absent'))
        self.execute_module(changed=True)
        self.assert_has_xml_tag('filter', dict(name=rule['name'], interface=rule['interface']), absent=True)

    def do_rule_update_test(self, rule, failed=False, **kwargs):
        """ test updating field of an host alias """
        target = copy(rule)
        target.update(kwargs)
        set_module_args(args_from_var(target))
        self.execute_module(changed=True)
        if failed:
            self.assertFalse(self.load_xml_result())
        else:
            self.check_rule_elt(target)

    ############################
    # rule creation tests
    #
    def test_rule_create_one_rule(self):
        """ test creation of a new rule """
        rule = dict(name='one_rule', source='any', destination='any', interface='lan')
        self.do_rule_creation_test(rule)

    @unittest.expectedFailure
    def test_rule_create_log(self):
        """ test creation of a new rule with logging """
        rule = dict(name='one_rule', source='any', destination='any', interface='lan', log='yes')
        self.do_rule_creation_test(rule)

    def test_rule_create_nolog(self):
        """ test creation of a new rule without logging """
        rule = dict(name='one_rule', source='any', destination='any', interface='lan', log='no')
        self.do_rule_creation_test(rule)

    def test_rule_create_pass(self):
        """ test creation of a new rule explictly passing """
        rule = dict(name='one_rule', source='any', destination='any', interface='lan', action='pass')
        self.do_rule_creation_test(rule)

    def test_rule_create_block(self):
        """ test creation of a new rule blocking """
        rule = dict(name='one_rule', source='any', destination='any', interface='lan', action='block')
        self.do_rule_creation_test(rule)

    def test_rule_create_reject(self):
        """ test creation of a new rule rejecting """
        rule = dict(name='one_rule', source='any', destination='any', interface='lan', action='reject')
        self.do_rule_creation_test(rule)

    def test_rule_create_disabled(self):
        """ test creation of a new disabled rule """
        rule = dict(name='one_rule', source='any', destination='any', interface='lan', disabled=True)
        self.do_rule_creation_test(rule)

    def test_rule_create_floating(self):
        """ test creation of a new floating rule """
        rule = dict(name='one_rule', source='any', destination='any', interface='lan', floating='yes', direction='any')
        self.do_rule_creation_test(rule)

    def test_rule_create_nofloating(self):
        """ test creation of a new non-floating rule """
        rule = dict(name='one_rule', source='any', destination='any', interface='lan', floating='no')
        self.do_rule_creation_test(rule)

    @unittest.expectedFailure
    def test_rule_create_floating_interfaces(self):
        """ test creation of a floating rule on two interfaces """
        rule = dict(name='one_rule', source='any', destination='any', interface='lan,wan', floating='yes', direction='any')
        self.do_rule_creation_test(rule)

    def test_rule_create_inet46(self):
        """ test creation of a new rule using ipv4 and ipv6 """
        rule = dict(name='one_rule', source='any', destination='any', interface='lan', ipprotocol='inet46')
        self.do_rule_creation_test(rule)

    def test_rule_create_inet6(self):
        """ test creation of a new rule using ipv6 """
        rule = dict(name='one_rule', source='any', destination='any', interface='lan', ipprotocol='inet6')
        self.do_rule_creation_test(rule)

    def test_rule_create_tcp(self):
        """ test creation of a new rule for tcp protocol """
        rule = dict(name='one_rule', source='any', destination='any', interface='lan', protocol='tcp')
        self.do_rule_creation_test(rule)

    def test_rule_create_udp(self):
        """ test creation of a new rule for udp protocol """
        rule = dict(name='one_rule', source='any', destination='any', interface='lan', protocol='udp')
        self.do_rule_creation_test(rule)

    def test_rule_create_tcp_udp(self):
        """ test creation of a new rule for tcp/udp protocols """
        rule = dict(name='one_rule', source='any', destination='any', interface='lan', protocol='tcp/udp')
        self.do_rule_creation_test(rule)

    def test_rule_create_icmp(self):
        """ test creation of a new rule for icmp protocol """
        rule = dict(name='one_rule', source='any', destination='any', interface='lan', protocol='icmp')
        self.do_rule_creation_test(rule)

    def test_rule_create_protocol_any(self):
        """ test creation of a new rule for (self) """
        rule = dict(name='one_rule', source='any', destination='any', interface='lan', protocol='any')
        self.do_rule_creation_test(rule)

    def test_rule_create_state_keep(self):
        """ test creation of a new rule with explicit keep state """
        rule = dict(name='one_rule', source='any', destination='any', interface='lan', statetype='keepstate')
        self.do_rule_creation_test(rule)

    def test_rule_create_state_sloppy(self):
        """ test creation of a new rule with sloppy state """
        rule = dict(name='one_rule', source='any', destination='any', interface='lan', statetype='sloppy state')
        self.do_rule_creation_test(rule)

    def test_rule_create_state_synproxy(self):
        """ test creation of a new rule with synproxy state """
        # todo: synproxy is only valid with tcp
        rule = dict(name='one_rule', source='any', destination='any', interface='lan', statetype='synproxy state')
        self.do_rule_creation_test(rule)

    def test_rule_create_state_none(self):
        """ test creation of a new rule with no state """
        rule = dict(name='one_rule', source='any', destination='any', interface='lan', statetype=None)
        self.do_rule_creation_test(rule)

    @unittest.expectedFailure
    def test_rule_create_state_invalid(self):
        """ test creation of a new rule with invalid state """
        rule = dict(name='one_rule', source='any', destination='any', interface='lan', statetype='acme state')
        self.do_rule_creation_test(rule, failed=True)

    def test_rule_create_after(self):
        """ test creation of a new rule after another """
        rule = dict(name='one_rule', source='any', destination='any', interface='vpn', after='admin_bypass')
        self.do_rule_creation_test(rule)
        self.check_rule_idx(rule, 13)

    def test_rule_create_after_top(self):
        """ test creation of a new rule at top """
        rule = dict(name='one_rule', source='any', destination='any', interface='wan', after='top')
        self.do_rule_creation_test(rule)
        self.check_rule_idx(rule, 0)

    def test_rule_create_after_invalid(self):
        """ test creation of a new rule after an invalid rule """
        rule = dict(name='one_rule', source='any', destination='any', interface='lan', after='admin_bypass')
        self.do_rule_creation_test(rule, failed=True)

    def test_rule_create_before(self):
        """ test creation of a new rule before another """
        rule = dict(name='one_rule', source='any', destination='any', interface='vpn', before='admin_bypass')
        self.do_rule_creation_test(rule)
        self.check_rule_idx(rule, 12)

    def test_rule_create_before_bottom(self):
        """ test creation of a new rule at bottom """
        rule = dict(name='one_rule', source='any', destination='any', interface='wan', before='bottom')
        self.do_rule_creation_test(rule)
        self.check_rule_idx(rule, 5)

    def test_rule_create_before_bottom_default(self):
        """ test creation of a new rule at bottom (default) """
        rule = dict(name='one_rule', source='any', destination='any', interface='wan', action='pass')
        self.do_rule_creation_test(rule)
        self.check_rule_idx(rule, 5)

    def test_rule_create_before_invalid(self):
        """ test creation of a new rule before an invalid rule """
        rule = dict(name='one_rule', source='any', destination='any', interface='lan', before='admin_bypass')
        self.do_rule_creation_test(rule, failed=True)

    def test_rule_create_source_alias_invalid(self):
        """ test creation of a new rule with an invalid source alias """
        rule = dict(name='one_rule', source='acme', destination='any', interface='lan')
        self.do_rule_creation_test(rule, failed=True)

    def test_rule_create_source_ip_invalid(self):
        """ test creation of a new rule with an invalid source ip """
        rule = dict(name='one_rule', source='192.193.194.195.196', destination='any', interface='lan')
        self.do_rule_creation_test(rule, failed=True)

    def test_rule_create_source_net_invalid(self):
        """ test creation of a new rule with an invalid source network """
        rule = dict(name='one_rule', source='192.193.194.195/256', destination='any', interface='lan')
        self.do_rule_creation_test(rule, failed=True)

    def test_rule_create_destination_alias_invalid(self):
        """ test creation of a new rule with an invalid destination alias """
        rule = dict(name='one_rule', source='any', destination='acme', interface='lan')
        self.do_rule_creation_test(rule, failed=True)

    def test_rule_create_destination_ip_invalid(self):
        """ test creation of a new rule with an invalid destination ip """
        rule = dict(name='one_rule', source='any', destination='192.193.194.195.196', interface='lan')
        self.do_rule_creation_test(rule, failed=True)

    def test_rule_create_destination_net_invalid(self):
        """ test creation of a new rule with an invalid destination network """
        rule = dict(name='one_rule', source='any', destination='192.193.194.195/256', interface='lan')
        self.do_rule_creation_test(rule, failed=True)

    def test_rule_create_source_self_lan(self):
        """ test creation of a new rule with self"""
        rule = dict(name='one_rule', source='(self)', destination='any', interface='lan')
        self.do_rule_creation_test(rule)

    def test_rule_create_ip_to_ip(self):
        """ test creation of a new rule with valid ips """
        rule = dict(name='one_rule', source='10.10.1.1', destination='10.10.10.1', interface='lan')
        self.do_rule_creation_test(rule)

    def test_rule_create_net_to_net(self):
        """ test creation of a new rule valid networks """
        rule = dict(name='one_rule', source='10.10.1.0/24', destination='10.10.10.0/24', interface='lan')
        self.do_rule_creation_test(rule)

    def test_rule_create_net_interface(self):
        """ test creation of a new rule with valid interface """
        rule = dict(name='one_rule', source='NET:lan', destination='any', interface='lan')
        self.do_rule_creation_test(rule)

    def test_rule_create_interface(self):
        """ test creation of a new rule with valid interface """
        rule = dict(name='one_rule', source='vpn', destination='any', interface='lan')
        self.do_rule_creation_test(rule)

    def test_rule_create_port_number(self):
        """ test creation of a new rule with port """
        rule = dict(name='one_rule', source='10.10.1.1', destination='10.10.10.1:80', interface='lan')
        self.do_rule_creation_test(rule)

    def test_rule_create_port_alias(self):
        """ test creation of a new rule with port alias """
        rule = dict(name='one_rule', source='10.10.1.1', destination='10.10.10.1:port_http', interface='lan')
        self.do_rule_creation_test(rule)

    @unittest.expectedFailure
    def test_rule_create_port_range(self):
        """ test creation of a new rule with range of ports """
        rule = dict(name='one_rule', source='10.10.1.1:30000-40000', destination='10.10.10.1', interface='lan')
        self.do_rule_creation_test(rule)

    @unittest.expectedFailure
    def test_rule_create_port_alias_range(self):
        """ test creation of a new rule with range of alias ports """
        rule = dict(name='one_rule', source='10.10.1.1:port_ssh-port_http', destination='10.10.10.1', interface='lan')
        self.do_rule_creation_test(rule)

    def test_rule_create_invalid_port_number(self):
        """ test creation of a new rule with invalid port number """
        rule = dict(name='one_rule', source='10.10.1.1:65536', destination='10.10.10.1', interface='lan')
        self.do_rule_creation_test(rule, failed=True)

    def test_rule_create_invalid_port_alias(self):
        """ test creation of a new rule with invalid port alias """
        rule = dict(name='one_rule', source='10.10.1.1:openvpn_port', destination='10.10.10.1', interface='lan')
        self.do_rule_creation_test(rule, failed=True)

    @unittest.expectedFailure
    def test_rule_create_net_invalid_interface(self):
        """ test creation of a new rule with invalid interface """
        rule = dict(name='one_rule', source='NET:ran', destination='any', interface='lan')
        self.do_rule_creation_test(rule, failed=True)

    ############################
    # rule update tests
    #
    def test_rule_update_action(self):
        """ test updating action of a rule to block """
        rule = dict(name='test_rule', source='any', destination='any', interface='wan', action='block', protocol='tcp')
        self.do_rule_update_test(rule)

    def test_rule_update_disabled(self):
        """ test updating disabled of a rule to True """
        rule = dict(name='test_rule', source='any', destination='any', interface='wan', disabled='True', protocol='tcp')
        self.do_rule_update_test(rule)

    def test_rule_update_floating_direction(self):
        """ test updating direction of a rule to out """
        rule = dict(name='test_rule_floating', source='any', destination='any', interface='wan', floating='yes', direction='out', protocol='tcp')
        self.do_rule_update_test(rule)

    def test_rule_update_floating_yes(self):
        """ test updating floating of a rule to yes """
        rule = dict(name='test_rule', source='any', destination='any', interface='wan', floating='yes', direction='any', protocol='tcp')
        self.do_rule_update_test(rule)

    @unittest.expectedFailure
    def test_rule_update_floating_no(self):
        """ test updating floating of a rule to no """
        rule = dict(name='test_rule_floating', source='any', destination='any', interface='wan', floating='no', direction='any', protocol='tcp')
        self.do_rule_update_test(rule)

    @unittest.expectedFailure
    def test_rule_update_floating_default(self):
        """ test updating floating of a rule to default """
        rule = dict(name='test_rule_floating', source='any', destination='any', interface='wan', protocol='tcp')
        self.do_rule_update_test(rule)

    def test_rule_update_inet(self):
        """ test updating ippprotocol of a rule to ipv4 and ipv6 """
        rule = dict(name='test_rule', source='any', destination='any', interface='wan', ipprotocol='inet46', protocol='tcp')
        self.do_rule_update_test(rule)

    def test_rule_update_protocol_udp(self):
        """ test updating protocol of a rule to udp """
        rule = dict(name='test_rule', source='any', destination='any', interface='wan', protocol='udp')
        self.do_rule_update_test(rule)

    def test_rule_update_protocol_tcp_udp(self):
        """ test updating protocol of a rule to tcp/udp """
        rule = dict(name='test_rule', source='any', destination='any', interface='wan', protocol='tcp/udp')
        self.do_rule_update_test(rule)

    @unittest.expectedFailure
    def test_rule_update_log_yes(self):
        """ test updating log of a rule to yes """
        rule = dict(name='test_rule', source='any', destination='any', interface='wan', log='yes', direction='any', protocol='tcp')
        self.do_rule_update_test(rule)

    @unittest.expectedFailure
    def test_rule_update_log_no(self):
        """ test updating log of a rule to no """
        rule = dict(name='test_rule_2', source='any', destination='any', interface='wan', log='no', direction='any', protocol='tcp')
        self.do_rule_update_test(rule)

    @unittest.expectedFailure
    def test_rule_update_log_default(self):
        """ test updating log of a rule to default """
        rule = dict(name='test_rule_2', source='any', destination='any', interface='wan', protocol='tcp')
        self.do_rule_update_test(rule)

    @unittest.expectedFailure
    def test_rule_update_before(self):
        """ test updating position of a rule to before another """
        rule = dict(name='test_rule_3', source='any', destination='any', interface='wan', protocol='tcp', before='test_rule')
        self.do_rule_update_test(rule)
        self.check_rule_idx(rule, 0)

    @unittest.expectedFailure
    def test_rule_update_before_bottom(self):
        """ test updating position of a rule to bottom """
        rule = dict(name='test_rule_3', source='any', destination='any', interface='wan', protocol='tcp', before='bottom')
        self.do_rule_update_test(rule)
        self.check_rule_idx(rule, 5)

    @unittest.expectedFailure
    def test_rule_update_after(self):
        """ test updating position of a rule to after another """
        rule = dict(name='test_rule_3', source='any', destination='any', interface='wan', protocol='tcp', after='test_rule_3')
        self.do_rule_update_test(rule)
        self.check_rule_idx(rule, 4)

    @unittest.expectedFailure
    def test_rule_update_after_top(self):
        """ test updating position of a rule to top """
        rule = dict(name='test_rule_3', source='any', destination='any', interface='wan', protocol='tcp', after='top')
        self.do_rule_update_test(rule)
        self.check_rule_idx(rule, 0)

    ##############
    # delete
    #
    def test_rule_delete(self):
        """ test updating position of a rule to top """
        rule = dict(name='test_rule_3', source='any', destination='any', interface='wan', protocol='tcp')
        self.do_rule_deletion_test(rule)

    ##############
    # misc
    #
    def test_check_mode(self):
        """ test updating an host alias without generating result """
        rule = dict(name='one_rule', source='any', destination='any', interface='lan')
        set_module_args(args_from_var(rule, _ansible_check_mode=True))
        self.execute_module(changed=True)
        self.assertFalse(self.load_xml_result())
