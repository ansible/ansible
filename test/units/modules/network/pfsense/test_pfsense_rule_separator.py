# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import pytest
from ansible.modules.network.pfsense import pfsense_rule_separator
from .pfsense_module import TestPFSenseModule

if sys.version_info < (2, 7):
    pytestmark = pytest.mark.skip("pfSense Ansible modules require Python >= 2.7")


class TestPFSenseRuleSeparatorModule(TestPFSenseModule):

    module = pfsense_rule_separator

    def __init__(self, *args, **kwargs):
        super(TestPFSenseRuleSeparatorModule, self).__init__(*args, **kwargs)
        self.config_file = 'pfsense_rule_separator_config.xml'

    @staticmethod
    def get_args_fields():
        """ return params fields """
        fields = ['interface', 'floating', 'color', 'after', 'before', 'state', 'name']
        return fields

    def get_target_elt(self, separator, absent=False):
        """ get separator from XML """
        if separator.get('floating'):
            interface = 'floatingrules'
        else:
            interface = self.unalias_interface(separator['interface'])

        filter_elt = self.assert_find_xml_elt(self.xml_result, 'filter')
        separator_elt = self.assert_find_xml_elt(filter_elt, 'separator')
        iface_elt = self.assert_find_xml_elt(separator_elt, interface)
        for separator_elt in iface_elt:
            text_elt = separator_elt.find('text')
            if text_elt is not None and text_elt.text == separator['name']:
                if absent:
                    self.fail('Separator ' + separator['name'] + ' found on interface ' + interface)
                return separator_elt

        if not absent:
            self.fail('Separator ' + separator['name'] + ' not found on interface ' + interface)
        return None

    def check_target_elt(self, separator, separator_elt):
        """ check XML separator definition """
        if separator.get('floating'):
            interface = 'floatingrules'
        else:
            interface = self.unalias_interface(separator['interface'])

        self.assert_xml_elt_equal(separator_elt, 'if', interface)

        if 'color' not in separator:
            self.assert_xml_elt_equal(separator_elt, 'color', 'bg-info')
        else:
            self.assert_xml_elt_equal(separator_elt, 'color', 'bg-' + separator['color'])

    def check_separator_idx(self, separator, expected_idx):
        """ test the logical position of separator """
        separator_elt = self.get_target_elt(separator)
        row_elt = self.assert_find_xml_elt(separator_elt, 'row')
        idx = int(row_elt.text.replace('fr', ''))
        if idx != expected_idx:
            self.fail('Idx of separator ' + separator['name'] + ' if wrong: ' + str(idx) + ', expected: ' + str(expected_idx))

    ##############
    # hosts
    #
    def test_separator_create(self):
        """ test creation of a new separator """
        separator = dict(name='voip', interface='lan_100')
        command = "create rule_separator 'voip' on 'lan_100', color='info'"
        self.do_module_test(separator, command=command)
        self.check_separator_idx(separator, 6)

    def test_separator_create_floating(self):
        """ test creation of a new separator """
        separator = dict(name='voip', floating=True)
        command = "create rule_separator 'voip' on 'floating', color='info'"
        self.do_module_test(separator, command=command)
        self.check_separator_idx(separator, 0)

    def test_separator_create_top(self):
        """ test creation of a new separator at top """
        separator = dict(name='voip', interface='lan_100', after='top')
        command = "create rule_separator 'voip' on 'lan_100', color='info', after='top'"
        self.do_module_test(separator, command=command)
        self.check_separator_idx(separator, 0)

    def test_separator_create_bottom(self):
        """ test creation of a new separator at bottom """
        separator = dict(name='voip', interface='lan', before='bottom')
        command = "create rule_separator 'voip' on 'lan', color='info', before='bottom'"
        self.do_module_test(separator, command=command)
        self.check_separator_idx(separator, 14)

    def test_separator_create_after(self):
        """ test creation of a new separator at bottom """
        separator = dict(name='voip', interface='lan', after='antilock_out_1')
        command = "create rule_separator 'voip' on 'lan', color='info', after='antilock_out_1'"
        self.do_module_test(separator, command=command)
        self.check_separator_idx(separator, 1)

    def test_separator_create_before(self):
        """ test creation of a new separator at bottom """
        separator = dict(name='voip', interface='lan', before='antilock_out_2')
        command = "create rule_separator 'voip' on 'lan', color='info', before='antilock_out_2'"
        self.do_module_test(separator, command=command)
        self.check_separator_idx(separator, 1)

    def test_separator_delete(self):
        """ test deletion of a separator """
        separator = dict(name='test_separator', interface='lan')
        command = "delete rule_separator 'test_separator' on 'lan'"
        self.do_module_test(separator, command=command, delete=True)

    def test_separator_delete_inexistent(self):
        """ test deletion of an inexistent separator """
        separator = dict(name='test_separator', interface='wan')
        self.do_module_test(separator, command='', changed=False, delete=True)

    def test_separator_update_noop(self):
        """ test changing nothing to a separator """
        separator = dict(name='test_separator', interface='lan', color='info')
        self.do_module_test(separator, changed=False)

    def test_separator_update_color(self):
        """ test updating color of a separator """
        separator = dict(name='test_separator', interface='lan', color='warning')
        command = "update rule_separator 'test_separator' on 'lan' set color='warning'"
        self.do_module_test(separator, command=command)
        self.check_separator_idx(separator, 1)

    def test_separator_update_position(self):
        """ test updating position of a separator """
        separator = dict(name='test_separator', interface='lan', after='top')
        command = "update rule_separator 'test_separator' on 'lan' set color='info', after='top'"
        self.do_module_test(separator, command=command)
        self.check_separator_idx(separator, 0)
