# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from copy import copy
import pytest
import sys

if sys.version_info < (2, 7):
    pytestmark = pytest.mark.skip("pfSense Ansible modules require Python >= 2.7")

from units.modules.utils import set_module_args
from .test_pfsense_rule import TestPFSenseRuleModule, args_from_var


class TestPFSenseRuleUpdateModule(TestPFSenseRuleModule):

    def do_rule_update_test(self, rule, failed=False, msg='', **kwargs):
        """ test updating field of an host alias """
        target = copy(rule)
        target.update(kwargs)
        set_module_args(args_from_var(target))
        self.execute_module(changed=True, failed=failed, msg=msg)
        if failed:
            self.assertFalse(self.load_xml_result())
        else:
            rule_elt = self.get_target_elt(rule)
            self.check_target_elt(rule, rule_elt)

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

    def test_rule_update_enabled(self):
        """ test updating disabled of a rule to False """
        rule = dict(name='test_lan_100_1', source='any', destination='any', interface='lan_100', disabled='False', protocol='tcp')
        self.do_rule_update_test(rule)

    def test_rule_update_enabled_default(self):
        """ test updating disabled of a rule to default """
        rule = dict(name='test_lan_100_1', source='any', destination='any', interface='lan_100', protocol='tcp')
        self.do_rule_update_test(rule)

    def test_rule_update_floating_interface(self):
        """ test updating interface of a floating rule """
        rule = dict(name='test_rule_floating', source='any', destination='any', interface='lan', floating='yes', direction='any', protocol='tcp')
        self.do_rule_update_test(rule)

    def test_rule_update_floating_direction(self):
        """ test updating direction of a rule to out """
        rule = dict(name='test_rule_floating', source='any', destination='any', interface='wan', floating='yes', direction='out', protocol='tcp')
        self.do_rule_update_test(rule)

    def test_rule_update_floating_yes(self):
        """ test updating floating of a rule to yes
            Since you can't change the floating mode of a rule, it should create a new rule
        """
        rule = dict(name='test_rule', source='any', destination='any', interface='wan', floating='yes', direction='any', protocol='tcp')
        self.do_rule_update_test(rule)
        other_rule = dict(name='test_rule', source='any', destination='any', interface='wan', floating='no', protocol='tcp')
        other_rule_elt = self.get_target_elt(other_rule)
        self.check_target_elt(other_rule, other_rule_elt)

    def test_rule_update_floating_no(self):
        """ test updating floating of a rule to no
            Since you can't change the floating mode of a rule, it should create a new rule
        """
        rule = dict(name='test_rule_floating', source='any', destination='any', interface='wan', floating='no', direction='any', protocol='tcp')
        self.do_rule_update_test(rule)
        other_rule = dict(name='test_rule_floating', source='any', destination='any', interface='wan', floating='yes', direction='any', protocol='tcp')
        other_rule_elt = self.get_target_elt(other_rule)
        self.check_target_elt(other_rule, other_rule_elt)

    def test_rule_update_floating_default(self):
        """ test updating floating of a rule to default (no)
            Since you can't change the floating mode of a rule, it should create a new rule
        """
        rule = dict(name='test_rule_floating', source='any', destination='any', interface='wan', protocol='tcp')
        self.do_rule_update_test(rule)
        other_rule = dict(name='test_rule_floating', source='any', destination='any', interface='wan', floating='yes', direction='any', protocol='tcp')
        other_rule_elt = self.get_target_elt(other_rule)
        self.check_target_elt(other_rule, other_rule_elt)

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

    def test_rule_update_log_yes(self):
        """ test updating log of a rule to yes """
        rule = dict(name='test_rule', source='any', destination='any', interface='wan', log='yes', protocol='tcp')
        self.do_rule_update_test(rule)

    def test_rule_update_log_no(self):
        """ test updating log of a rule to no """
        rule = dict(name='test_rule_2', source='any', destination='any', interface='wan', log='no', protocol='tcp')
        self.do_rule_update_test(rule)

    def test_rule_update_log_default(self):
        """ test updating log of a rule to default """
        rule = dict(name='test_rule_2', source='any', destination='any', interface='wan', protocol='tcp')
        self.do_rule_update_test(rule)

    def test_rule_update_negate_add_source(self):
        """ test updating source of a rule with a not """
        rule = dict(name='test_rule_2', source='!srv_admin', destination='any', interface='wan', protocol='tcp')
        self.do_rule_update_test(rule)

    def test_rule_update_negate_add_destination(self):
        """ test updating destination of a rule with a not """
        rule = dict(name='test_rule_2', source='any', destination='!srv_admin', interface='wan', protocol='tcp')
        self.do_rule_update_test(rule)

    def test_rule_update_negate_remove_source(self):
        """ test updating source of a rule remove the not """
        rule = dict(name='not_rule_src', source='srv_admin', destination='any:port_ssh', interface='lan', protocol='tcp')
        self.do_rule_update_test(rule)

    def test_rule_update_negate_remove_destination(self):
        """ test updating destination of a rule remove the not """
        rule = dict(name='not_rule_dst', source='any', destination='srv_admin:port_ssh', interface='lan', protocol='tcp')
        self.do_rule_update_test(rule)

    def test_rule_update_before(self):
        """ test updating position of a rule to before another """
        rule = dict(name='test_rule_3', source='any', destination='any', interface='wan', protocol='tcp', before='test_rule')
        self.do_rule_update_test(rule)
        self.check_rule_idx(rule, 0)

    def test_rule_update_before_bottom(self):
        """ test updating position of a rule to bottom """
        rule = dict(name='test_rule_3', source='any', destination='any', interface='wan', protocol='tcp', before='bottom')
        self.do_rule_update_test(rule)
        self.check_rule_idx(rule, 3)

    def test_rule_update_after(self):
        """ test updating position of a rule to after another rule """
        rule = dict(name='test_rule_3', source='any', destination='any', interface='wan', protocol='tcp', after='antilock_out_3')
        self.do_rule_update_test(rule)
        self.check_rule_idx(rule, 3)

    def test_rule_update_after_self(self):
        """ test updating position of a rule to after same rule """
        rule = dict(name='test_rule_3', source='any', destination='any', interface='wan', protocol='tcp', after='test_rule_3')
        self.do_rule_update_test(rule, failed=True, msg='Cannot specify the current rule in after')

    def test_rule_update_before_self(self):
        """ test updating position of a rule to before same rule """
        rule = dict(name='test_rule_3', source='any', destination='any', interface='wan', protocol='tcp', before='test_rule_3')
        self.do_rule_update_test(rule, failed=True, msg='Cannot specify the current rule in before')

    def test_rule_update_after_top(self):
        """ test updating position of a rule to top """
        rule = dict(name='test_rule_3', source='any', destination='any', interface='wan', protocol='tcp', after='top')
        self.do_rule_update_test(rule)
        self.check_rule_idx(rule, 0)

    def test_rule_update_separator_top(self):
        """ test updating position of a rule to top """
        rule = dict(name='r2', source='any', destination='any', interface='vt1', after='top')
        self.do_rule_update_test(rule)
        self.check_rule_idx(rule, 0)
        self.check_separator_idx(rule['interface'], 'test_sep1', 1)
        self.check_separator_idx(rule['interface'], 'test_sep2', 3)

    def test_rule_update_separator_bottom(self):
        """ test updating position of a rule to bottom """
        rule = dict(name='r1', source='any', destination='any', interface='vt1', before='bottom')
        self.do_rule_update_test(rule)
        self.check_rule_idx(rule, 2)
        self.check_separator_idx(rule['interface'], 'test_sep1', 0)
        self.check_separator_idx(rule['interface'], 'test_sep2', 2)

    def test_rule_update_separator_before_first(self):
        """ test creation of a new rule at bottom """
        rule = dict(name='r3', source='any', destination='any', interface='vt1', before='r1')
        self.do_rule_update_test(rule)
        self.check_rule_idx(rule, 0)
        self.check_separator_idx(rule['interface'], 'test_sep1', 0)
        self.check_separator_idx(rule['interface'], 'test_sep2', 3)

    def test_rule_update_separator_after_third(self):
        """ test creation of a new rule at bottom """
        rule = dict(name='r1', source='any', destination='any', interface='vt1', after='r3')
        self.do_rule_update_test(rule)
        self.check_rule_idx(rule, 2)
        self.check_separator_idx(rule['interface'], 'test_sep1', 0)
        self.check_separator_idx(rule['interface'], 'test_sep2', 3)

    def test_rule_update_queue_set(self):
        """ test updating queue of a rule """
        rule = dict(name='test_rule', source='any', destination='any', interface='wan', queue='one_queue', protocol='tcp')
        self.do_rule_update_test(rule)

    def test_rule_update_queue_set_ack(self):
        """ test updating queue and ackqueue of a rule """
        rule = dict(name='test_rule', source='any', destination='any', interface='wan', queue='one_queue', ackqueue='another_queue', protocol='tcp')
        self.do_rule_update_test(rule)

    def test_rule_update_queue_unset_ack(self):
        """ test updating ackqueue of a rule """
        rule = dict(name='test_lan_100_2', source='any', destination='any', interface='lan_100', queue='one_queue', protocol='tcp')
        self.do_rule_update_test(rule)

    def test_rule_update_queue_unset(self):
        """ test updating queue of a rule """
        rule = dict(name='test_lan_100_3', source='any', destination='any', interface='lan_100', protocol='tcp')
        self.do_rule_update_test(rule)

    def test_rule_update_limiter_set(self):
        """ test updating limiter of a rule """
        rule = dict(name='test_rule', source='any', destination='any', interface='wan', in_queue='one_limiter', protocol='tcp')
        self.do_rule_update_test(rule)

    def test_rule_update_limiter_set_out(self):
        """ test updating limiter in and out of a rule """
        rule = dict(name='test_rule', source='any', destination='any', interface='wan', in_queue='one_limiter', out_queue='another_limiter', protocol='tcp')
        self.do_rule_update_test(rule)

    def test_rule_update_limiter_unset_out(self):
        """ test updating limiter out of a rule """
        rule = dict(name='test_lan_100_4', source='any', destination='any', interface='lan_100', in_queue='one_limiter', protocol='tcp')
        self.do_rule_update_test(rule)

    def test_rule_update_limiter_unset(self):
        """ test updating limiter of a rule """
        rule = dict(name='test_lan_100_5', source='any', destination='any', interface='lan_100', protocol='tcp')
        self.do_rule_update_test(rule)

    def test_rule_update_gateway_set(self):
        """ test updating gateway of a rule """
        rule = dict(name='test_rule_3', source='any', destination='any:port_http', interface='wan', protocol='tcp', gateway='GW_WAN')
        self.do_rule_update_test(rule)

    def test_rule_update_gateway_unset(self):
        """ test updating gateway of a rule """
        rule = dict(name='antilock_out_1', source='any', destination='any:port_ssh', interface='lan', protocol='tcp')
        self.do_rule_update_test(rule)
