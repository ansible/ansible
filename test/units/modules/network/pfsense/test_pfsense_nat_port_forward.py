# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import sys

if sys.version_info < (2, 7):
    pytestmark = pytest.mark.skip("pfSense Ansible modules require Python >= 2.7")

from ansible.modules.network.pfsense import pfsense_nat_port_forward
from .pfsense_module import TestPFSenseModule
from .test_pfsense_rule import TestPFSenseRuleModule


class TestPFSenseNatPortForwardModule(TestPFSenseModule):

    module = pfsense_nat_port_forward

    def __init__(self, *args, **kwargs):
        super(TestPFSenseNatPortForwardModule, self).__init__(*args, **kwargs)
        self.config_file = 'pfsense_nat_port_forward_config.xml'

    @staticmethod
    def get_args_fields():
        """ return params fields """
        fields = ['descr', 'interface', 'disabled', 'nordr', 'interface', 'protocol', 'source']
        fields += ['destination', 'target', 'natreflection', 'associated_rule', 'nosync']
        fields += ['after', 'before']
        return fields

    def check_target_addr(self, params, target_elt):
        """ test the addresses definition """
        if params['target'] == '2.3.4.5:443':
            self.assert_xml_elt_equal(target_elt, 'target', '2.3.4.5')
            self.assert_xml_elt_equal(target_elt, 'local-port', '443')

    def get_associated_rule_elt(self, params, ruleid):
        """ check the associated rule """
        filters = dict()
        filters['interface'] = self.unalias_interface(params['interface'])
        filters['associated-rule-id'] = ruleid
        return self.assert_has_xml_tag('filter', filters)

    def check_target_elt(self, params, target_elt, target_idx=-1):
        """ test the xml definition """
        rules_tester = TestPFSenseRuleModule()
        rules_tester.check_rule_elt_addr(params, target_elt, 'source')

        # checking destination address and ports
        rules_tester.check_rule_elt_addr(params, target_elt, 'destination')
        self.check_target_addr(params, target_elt)
        self.check_param_equal_or_not_find(params, target_elt, 'disabled')
        self.check_param_equal_or_not_find(params, target_elt, 'nordr')
        self.check_param_equal_or_not_find(params, target_elt, 'nosync')
        self.check_param_equal_or_not_find(params, target_elt, 'natreflection', not_find_val='system-default')

        self.check_value_equal(target_elt, 'interface', self.unalias_interface(params['interface']))
        self.check_param_equal(params, target_elt, 'protocol', 'tcp')

        self.check_rule_idx(params, target_idx)
        if 'associated_rule' not in params:
            params['associated_rule'] = 'associated'

        if params['associated_rule'] == 'none' or params['associated_rule'] == 'unassociated':
            self.assert_xml_elt_is_none_or_empty(target_elt, 'associated-rule-id')
        elif params['associated_rule'] == 'pass':
            self.check_value_equal(target_elt, 'associated-rule-id', 'pass')
        else:
            ruleid_elt = self.assert_find_xml_elt(target_elt, 'associated-rule-id')
            self.assertTrue(ruleid_elt.text.startswith('nat_'))

            rule_elt = self.get_associated_rule_elt(params, ruleid_elt.text)
            self.assertEqual(rule_elt.find('descr').text, 'NAT ' + params['descr'])

    def check_rule_idx(self, params, target_idx):
        """ test the xml position """
        rules_elt = self.assert_find_xml_elt(self.xml_result, 'nat')

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
        rules_elt = self.assert_find_xml_elt(self.xml_result, 'nat')

        for item in rules_elt:
            descr_elt = item.find('descr')
            if descr_elt is not None and descr_elt.text == obj['descr']:
                return item

        return None

    ##############
    # tests
    #
    def test_nat_port_forward_create(self):
        """ test """
        obj = dict(descr='test_pf', interface='lan', source='any:443', destination='1.2.3.4:443', target='2.3.4.5:443', associated_rule='pass')
        command = (
            "create nat_port_forward 'test_pf', interface='lan', source='any:443', destination='1.2.3.4:443', target='2.3.4.5:443', associated_rule='pass'"
        )
        self.do_module_test(obj, command=command, target_idx=3)

    def test_nat_port_forward_create_range(self):
        """ test """
        obj = dict(descr='test_pf', interface='lan', source='any:9000-10000', destination='1.2.3.4:9000-10000', target='2.3.4.5:9000', associated_rule='none')
        command = (
            "create nat_port_forward 'test_pf', interface='lan', source='any:9000-10000', destination='1.2.3.4:9000-10000', "
            "target='2.3.4.5:9000', associated_rule='none'"
        )
        self.do_module_test(obj, command=command, target_idx=3)

    def test_nat_port_forward_create_associated(self):
        """ test """
        obj = dict(descr='test_pf', interface='lan', source='any:443', destination='1.2.3.4:443', target='2.3.4.5:443', associated_rule='associated')
        cmd1 = "create rule 'NAT test_pf', source='any:443', destination='1.2.3.4:443', protocol='tcp', interface='lan'"
        cmd2 = "create nat_port_forward 'test_pf', interface='lan', source='any:443', destination='1.2.3.4:443', target='2.3.4.5:443'"
        self.do_module_test(obj, command=[cmd1, cmd2], target_idx=3)

    def test_nat_port_forward_create_unassociated(self):
        """ test """
        obj = dict(descr='test_pf', interface='lan', source='any:443', destination='1.2.3.4:443', target='2.3.4.5:443', associated_rule='unassociated')
        cmd1 = "create rule 'NAT test_pf', source='any:443', destination='1.2.3.4:443', protocol='tcp', interface='lan'"
        cmd2 = (
            "create nat_port_forward 'test_pf', interface='lan', source='any:443', destination='1.2.3.4:443', target='2.3.4.5:443', "
            "associated_rule='unassociated'"
        )
        self.do_module_test(obj, command=[cmd1, cmd2], target_idx=3)

    def test_nat_port_forward_create_top(self):
        """ test """
        obj = dict(descr='test_pf', interface='lan', source='any:443', destination='1.2.3.4:443', target='2.3.4.5:443', associated_rule='pass', after='top')
        command = (
            "create nat_port_forward 'test_pf', interface='lan', source='any:443', destination='1.2.3.4:443', target='2.3.4.5:443', "
            "associated_rule='pass', after='top'"
        )
        self.do_module_test(obj, command=command, target_idx=0)

    def test_nat_port_forward_create_after(self):
        """ test """
        obj = dict(descr='test_pf', interface='lan', source='any:443', destination='1.2.3.4:443', target='2.3.4.5:443', associated_rule='pass', after='one')
        command = (
            "create nat_port_forward 'test_pf', interface='lan', source='any:443', destination='1.2.3.4:443', target='2.3.4.5:443', "
            "associated_rule='pass', after='one'"
        )
        self.do_module_test(obj, command=command, target_idx=1)

    def test_nat_port_forward_create_before(self):
        """ test """
        obj = dict(descr='test_pf', interface='lan', source='any:443', destination='1.2.3.4:443', target='2.3.4.5:443', associated_rule='pass', before='two')
        command = (
            "create nat_port_forward 'test_pf', interface='lan', source='any:443', destination='1.2.3.4:443', target='2.3.4.5:443', "
            "associated_rule='pass', before='two'"
        )
        self.do_module_test(obj, command=command, target_idx=1)

    def test_nat_port_forward_update_noop(self):
        """ test """
        obj = dict(descr='one', interface='wan', source='any', destination='IP:wan:22022', target='10.255.1.20:22', associated_rule='none')
        self.do_module_test(obj, target_idx=0, changed=False)

    def test_nat_port_forward_update_bottom(self):
        """ test """
        obj = dict(descr='one', interface='wan', source='any', destination='IP:wan:22022', target='10.255.1.20:22', associated_rule='none', before='bottom')
        command = "update nat_port_forward 'one' set before='bottom'"
        self.do_module_test(obj, command=command, target_idx=2)

    def test_nat_port_forward_update_top(self):
        """ test """
        obj = dict(descr='last', interface='wan', source='any', destination='IP:wan:22022', target='10.255.1.20:22', associated_rule='associated', after='top')
        command = "update nat_port_forward 'last' set after='top'"
        self.do_module_test(obj, command=command, target_idx=0)

    def test_nat_port_forward_update_source(self):
        """ test """
        obj = dict(descr='one', interface='wan', source='1.2.3.4', destination='IP:wan:22022', target='10.255.1.20:22', associated_rule='none')
        command = "update nat_port_forward 'one' set source='1.2.3.4'"
        self.do_module_test(obj, command=command, target_idx=0)

    def test_nat_port_forward_update_destination(self):
        """ test """
        obj = dict(descr='one', interface='wan', source='any', destination='1.2.3.4:22022', target='10.255.1.20:22', associated_rule='none')
        command = "update nat_port_forward 'one' set destination='1.2.3.4:22022'"
        self.do_module_test(obj, command=command, target_idx=0)

    def test_nat_port_forward_update_interface(self):
        """ test """
        obj = dict(descr='one', interface='vpn', source='any', destination='IP:wan:22022', target='10.255.1.20:22', associated_rule='none')
        command = "update nat_port_forward 'one' set interface='vpn'"
        self.do_module_test(obj, command=command, target_idx=0)

    def test_nat_port_forward_update_interface_associated(self):
        """ test """
        obj = dict(descr='last', interface='lan_100', source='any', destination='IP:wan:22022', target='10.255.1.20:22', associated_rule='associated')
        cmd1 = "delete rule 'NAT last', interface='wan'"
        cmd2 = "create rule 'NAT last', source='any', destination='IP:wan:22022', protocol='tcp', interface='lan_100'"
        cmd3 = "update nat_port_forward 'last' set interface='lan_100'"
        self.do_module_test(obj, command=[cmd1, cmd2, cmd3], target_idx=2)

    def test_nat_port_forward_delete(self):
        """ test """
        obj = dict(descr='one')
        command = "delete nat_port_forward 'one'"
        self.do_module_test(obj, command=command, delete=True)
