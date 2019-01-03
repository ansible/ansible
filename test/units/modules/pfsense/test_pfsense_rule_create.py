# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import sys

if sys.version_info < (2, 7):
    pytestmark = pytest.mark.skip("pfSense Ansible modules require Python >= 2.7")

from units.modules.utils import set_module_args
from .test_pfsense_rule import TestPFSenseRuleModule, args_from_var


class TestPFSenseRuleCreateModule(TestPFSenseRuleModule):

    def do_rule_creation_test(self, rule, failed=False):
        """ test creation of a new rule """
        set_module_args(args_from_var(rule))
        self.execute_module(changed=True, failed=failed)
        if failed:
            self.assertFalse(self.load_xml_result())
        else:
            self.check_rule_elt(rule)

    ############################
    # rule creation tests
    #
    def test_rule_create_one_rule(self):
        """ test creation of a new rule """
        rule = dict(name='one_rule', source='any', destination='any', interface='lan')
        self.do_rule_creation_test(rule)

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

    def test_rule_create_floating_interfaces(self):
        """ test creation of a floating rule on three interfaces """
        rule = dict(name='one_rule', source='any', destination='any', interface='lan,wan,vt1', floating='yes', direction='any')
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
        rule = dict(name='one_rule', source='any', destination='any', interface='lan', statetype='keep state')
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
        rule = dict(name='one_rule', source='any', destination='any', interface='lan', statetype='none')
        self.do_rule_creation_test(rule)

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
        self.check_rule_idx(rule, 4)

    def test_rule_create_before_bottom_default(self):
        """ test creation of a new rule at bottom (default) """
        rule = dict(name='one_rule', source='any', destination='any', interface='wan', action='pass')
        self.do_rule_creation_test(rule)
        self.check_rule_idx(rule, 4)

    def test_rule_create_before_invalid(self):
        """ test creation of a new rule before an invalid rule """
        rule = dict(name='one_rule', source='any', destination='any', interface='lan', before='admin_bypass')
        self.do_rule_creation_test(rule, failed=True)

    def test_rule_create_source_alias(self):
        """ test creation of a new rule with a valid source alias """
        rule = dict(name='one_rule', source='srv_admin', destination='any', interface='lan')
        self.do_rule_creation_test(rule)

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

    def test_rule_create_destination_alias(self):
        """ test creation of a new rule with a valid source alias """
        rule = dict(name='one_rule', source='any', destination='srv_admin', interface='lan')
        self.do_rule_creation_test(rule)

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

    def test_rule_create_net_interface_invalid(self):
        """ test creation of a new rule with invalid interface """
        rule = dict(name='one_rule', source='NET:invalid_lan', destination='any', interface='lan')
        self.do_rule_creation_test(rule, failed=True)

    def test_rule_create_ip_interface(self):
        """ test creation of a new rule with valid interface """
        rule = dict(name='one_rule', source='IP:vt1', destination='any', interface='lan')
        self.do_rule_creation_test(rule)

    def test_rule_create_ip_interface_invalid(self):
        """ test creation of a new rule with invalid interface """
        rule = dict(name='one_rule', source='IP:invalid_lan', destination='any', interface='lan')
        self.do_rule_creation_test(rule, failed=True)

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

    def test_rule_create_port_range(self):
        """ test creation of a new rule with range of ports """
        rule = dict(name='one_rule', source='10.10.1.1:30000-40000', destination='10.10.10.1', interface='lan')
        self.do_rule_creation_test(rule)

    def test_rule_create_port_alias_range(self):
        """ test creation of a new rule with range of alias ports """
        rule = dict(name='one_rule', source='10.10.1.1:port_ssh-port_http', destination='10.10.10.1', interface='lan')
        self.do_rule_creation_test(rule)

    def test_rule_create_port_alias_range_invalid_1(self):
        """ test creation of a new rule with range of invalid alias ports """
        rule = dict(name='one_rule', source='10.10.1.1:port_ssh-openvpn_port', destination='10.10.10.1', interface='lan')
        self.do_rule_creation_test(rule, failed=True)

    def test_rule_create_port_alias_range_invalid_2(self):
        """ test creation of a new rule with range of invalid alias ports """
        rule = dict(name='one_rule', source='10.10.1.1:-openvpn_port', destination='10.10.10.1', interface='lan')
        self.do_rule_creation_test(rule, failed=True)

    def test_rule_create_port_alias_range_invalid_3(self):
        """ test creation of a new rule with range of invalid alias ports """
        rule = dict(name='one_rule', source='10.10.1.1:port_ssh-65537', destination='10.10.10.1', interface='lan')
        self.do_rule_creation_test(rule, failed=True)

    def test_rule_create_port_number_invalid(self):
        """ test creation of a new rule with invalid port number """
        rule = dict(name='one_rule', source='10.10.1.1:65536', destination='10.10.10.1', interface='lan')
        self.do_rule_creation_test(rule, failed=True)

    def test_rule_create_port_alias_invalid(self):
        """ test creation of a new rule with invalid port alias """
        rule = dict(name='one_rule', source='10.10.1.1:openvpn_port', destination='10.10.10.1', interface='lan')
        self.do_rule_creation_test(rule, failed=True)

    def test_rule_create_negate_source(self):
        """ test creation of a new rule with a not source """
        rule = dict(name='one_rule', source='!srv_admin', destination='any', interface='lan')
        self.do_rule_creation_test(rule)

    def test_rule_create_negate_destination(self):
        """ test creation of a new rule with a not destination """
        rule = dict(name='one_rule', source='any', destination='!srv_admin', interface='lan')
        self.do_rule_creation_test(rule)

    def test_rule_create_separator_top(self):
        """ test creation of a new rule at top """
        rule = dict(name='one_rule', source='any', destination='any', interface='vt1', after='top')
        self.do_rule_creation_test(rule)
        self.check_rule_idx(rule, 0)
        self.check_separator_idx(rule['interface'], 'test_sep1', 1)
        self.check_separator_idx(rule['interface'], 'test_sep2', 4)

    def test_rule_create_separator_bottom(self):
        """ test creation of a new rule at bottom """
        rule = dict(name='one_rule', source='any', destination='any', interface='vt1', before='bottom')
        self.do_rule_creation_test(rule)
        self.check_rule_idx(rule, 3)
        self.check_separator_idx(rule['interface'], 'test_sep1', 0)
        self.check_separator_idx(rule['interface'], 'test_sep2', 3)

    def test_rule_create_separator_before_first(self):
        """ test creation of a new rule at bottom """
        rule = dict(name='one_rule', source='any', destination='any', interface='vt1', before='r1')
        self.do_rule_creation_test(rule)
        self.check_rule_idx(rule, 0)
        self.check_separator_idx(rule['interface'], 'test_sep1', 0)
        self.check_separator_idx(rule['interface'], 'test_sep2', 4)

    def test_rule_create_separator_after_third(self):
        """ test creation of a new rule at bottom """
        rule = dict(name='one_rule', source='any', destination='any', interface='vt1', after='r3')
        self.do_rule_creation_test(rule)
        self.check_rule_idx(rule, 3)
        self.check_separator_idx(rule['interface'], 'test_sep1', 0)
        self.check_separator_idx(rule['interface'], 'test_sep2', 4)
