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


class TestPFSenseRuleNoopModule(TestPFSenseRuleModule):

    def do_rule_noop_test(self, alias):
        """ test not updating an rule """
        set_module_args(args_from_var(alias))
        self.execute_module(changed=False)
        self.assertFalse(self.load_xml_result())

    ############################
    # rule noop tests
    #
    def test_rule_noop_action(self):
        """ test not updating action of a rule to block """
        rule = dict(name='test_rule', source='any', destination='any', interface='wan', action='pass', protocol='tcp')
        self.do_rule_noop_test(rule)

    def test_rule_noop_disabled(self):
        """ test not updating disabled of a rule """
        rule = dict(name='test_rule', source='any', destination='any', interface='wan', disabled='False', protocol='tcp')
        self.do_rule_noop_test(rule)

    def test_rule_noop_enabled(self):
        """ test not updating disabled of a rule """
        rule = dict(name='test_lan_100_1', source='any', destination='any', interface='lan_100', disabled='True', protocol='tcp')
        self.do_rule_noop_test(rule)

    def test_rule_noop_disabled_default(self):
        """ test not updating disabled of a rule """
        rule = dict(name='test_rule', source='any', destination='any', interface='wan', protocol='tcp')
        self.do_rule_noop_test(rule)

    def test_rule_noop_floating_interface(self):
        """ test not updating interface of a floating rule """
        rule = dict(name='test_rule_floating', source='any', destination='any', interface='wan', floating='yes', direction='any', protocol='tcp')
        self.do_rule_noop_test(rule)

    def test_rule_noop_floating_direction(self):
        """ test not updating direction of a rule to out """
        rule = dict(name='test_rule_floating', source='any', destination='any', interface='wan', floating='yes', direction='any', protocol='tcp')
        self.do_rule_noop_test(rule)

    def test_rule_noop_inet(self):
        """ test not updating ippprotocol of a rule """
        rule = dict(name='test_rule', source='any', destination='any', interface='wan', ipprotocol='inet', protocol='tcp')
        self.do_rule_noop_test(rule)

    def test_rule_noop_protocol(self):
        """ test not updating protocol of a rule """
        rule = dict(name='test_rule', source='any', destination='any', interface='wan', protocol='tcp')
        self.do_rule_noop_test(rule)

    def test_rule_noop_log_no(self):
        """ test not updating log of a rule to no """
        rule = dict(name='test_rule', source='any', destination='any', interface='wan', log='no', protocol='tcp')
        self.do_rule_noop_test(rule)

    def test_rule_noop_log_yes(self):
        """ test not updating log of a rule to no """
        rule = dict(name='test_rule_2', source='any', destination='any', interface='wan', log='yes', protocol='tcp')
        self.do_rule_noop_test(rule)

    def test_rule_noop_log_default(self):
        """ test not updating log of a rule to default """
        rule = dict(name='test_rule', source='any', destination='any', interface='wan', log='no', protocol='tcp')
        self.do_rule_noop_test(rule)

    def test_rule_noop_source_and_destination(self):
        """ test not updating source and destination of a rule """
        rule = dict(name='ads_to_ads_tcp_2_3', source='ad_poc3:port_ldap_ssl', destination='ad_poc1:port_ldap_ssl', interface='lan', protocol='tcp')
        self.do_rule_noop_test(rule)

    def test_rule_noop_negate_source(self):
        """ test creation of a new rule with a not source """
        rule = dict(name='not_rule_src', source='!srv_admin', destination='any:port_ssh', interface='lan', protocol='tcp')
        self.do_rule_noop_test(rule)

    def test_rule_noop_negate_destination(self):
        """ test creation of a new rule with a not destination """
        rule = dict(name='not_rule_dst', source='any', destination='!srv_admin:port_ssh', interface='lan', protocol='tcp')
        self.do_rule_noop_test(rule)

    def test_rule_noop_before(self):
        """ test not updating position of a rule to before another """
        rule = dict(name='test_rule_2', source='any', destination='any', interface='wan', log='yes', protocol='tcp', before='test_rule_3')
        self.do_rule_noop_test(rule)

    def test_rule_noop_before_bottom(self):
        """ test not updating position of a rule to bottom """
        rule = dict(name='antilock_out_3', source='any', destination='any:443', interface='wan', protocol='tcp', before='bottom')
        self.do_rule_noop_test(rule)

    def test_rule_noop_position_bottom(self):
        """ test not updating position of a rule to bottom """
        rule = dict(name='antilock_out_3', source='any', destination='any:443', interface='wan', protocol='tcp')
        self.do_rule_noop_test(rule)

    def test_rule_noop_position_middle(self):
        """ test not updating position of a rule to before another """
        rule = dict(name='test_rule_2', source='any', destination='any', interface='wan', log='yes', protocol='tcp')
        self.do_rule_noop_test(rule)

    def test_rule_noop_after(self):
        """ test not updating position of a rule to after another rule """
        rule = dict(name='test_rule_2', source='any', destination='any', interface='wan', log='yes', protocol='tcp', after='test_rule')
        self.do_rule_noop_test(rule)

    def test_rule_noop_after_top(self):
        """ test not updating position of a rule to top """
        rule = dict(name='test_rule', source='any', destination='any', interface='wan', log='no', protocol='tcp', after='top')
        self.do_rule_noop_test(rule)

    def test_rule_noop_separator_top(self):
        """ test not updating position of a rule to top """
        rule = dict(name='r1', source='any', destination='any', interface='vt1', protocol='tcp')
        self.do_rule_noop_test(rule)

    def test_rule_noop_separator_bottom(self):
        """ test not updating position of a rule to bottom """
        rule = dict(name='r3', source='any', destination='any', interface='vt1', protocol='tcp')
        self.do_rule_noop_test(rule)

    def test_rule_noop_queue_ack(self):
        """ test updating queue of a rule """
        rule = dict(name='test_lan_100_2', source='any', destination='any', interface='lan_100', queue='one_queue', ackqueue='another_queue', protocol='tcp')
        self.do_rule_noop_test(rule)

    def test_rule_noop_queue(self):
        """ test updating queue and ackqueue of a rule """
        rule = dict(name='test_lan_100_3', source='any', destination='any', interface='lan_100', queue='one_queue', protocol='tcp')
        self.do_rule_noop_test(rule)

    def test_rule_noop_limiter_out(self):
        """ test updating queue of a rule """
        rule = dict(
            name='test_lan_100_4', source='any', destination='any', interface='lan_100', in_queue='one_limiter', out_queue='another_limiter', protocol='tcp')
        self.do_rule_noop_test(rule)

    def test_rule_noop_limiter_in(self):
        """ test updating queue and ackqueue of a rule """
        rule = dict(name='test_lan_100_5', source='any', destination='any', interface='lan_100', in_queue='one_limiter', protocol='tcp')
        self.do_rule_noop_test(rule)
