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


class TestPFSenseRuleMiscModule(TestPFSenseRuleModule):

    def do_rule_deletion_test(self, rule):
        """ test deletion of a rule """
        set_module_args(args_from_var(rule, 'absent'))
        self.execute_module(changed=True)
        self.assert_has_xml_tag('filter', dict(name=rule['name'], interface=rule['interface']), absent=True)

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
