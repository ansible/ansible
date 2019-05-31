# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Orion Poplawski <orion@nwra.com>
# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type
from ansible.module_utils.network.pfsense.pfsense import PFSenseModule, PFSenseModuleBase

RULE_SEPARATORS_ARGUMENT_SPEC = dict(
    name=dict(required=True, type='str'),
    state=dict(default='present', choices=['present', 'absent']),
    interface=dict(required=False, type='str'),
    floating=dict(required=False, type='bool'),
    color=dict(default='info', required=False, choices=['info', 'warning', 'danger', 'success']),
    after=dict(default=None, required=False, type='str'),
    before=dict(default=None, required=False, type='str'),
)

RULE_SEPARATORS_REQUIRED_ONE_OF = [['interface', 'floating']]
RULE_SEPARATORS_MUTUALLY_EXCLUSIVE = [['interface', 'floating']]


class PFSenseRuleSeparatorModule(PFSenseModuleBase):
    """ module managing pfsense rule separators """

    def __init__(self, module, pfsense=None):
        if pfsense is None:
            pfsense = PFSenseModule(module)
        self.module = module
        self.pfsense = pfsense
        self.separators = self.pfsense.rules.find('separator')

        self.change_descr = None
        self.result = {}
        self.result['changed'] = False
        self.result['commands'] = []

        self._params = None
        self._separator = None
        self._name = None
        self._interface_name = None
        self._interface = None
        self._floating = None
        self._after = None
        self._before = None

    def _log_create(self):
        """ generate pseudo-CLI command to create a separator """
        log = "create rule_separator '{0}'".format(self._name)
        log += self.format_cli_field(self._params, 'interface')
        log += self.format_cli_field(self._params, 'floating')
        log += self.format_cli_field(self._params, 'color')
        log += self.format_cli_field(self._params, 'after')
        log += self.format_cli_field(self._params, 'before')
        self.result['commands'].append(log)

    def _log_delete(self):
        """ generate pseudo-CLI command to delete a separator """
        log = "delete rule_separator '{0}'".format(self._name)
        log += self.format_cli_field(self._params, 'interface')
        log += self.format_cli_field(self._params, 'floating')
        self.result['commands'].append(log)

    def _log_update(self):
        """ generate pseudo-CLI command to update an alias """
        log = "update rule_separator '{0}'".format(self._name)
        values = ''
        values += self.format_cli_field(self._params, 'interface', add_comma=(values))
        values += self.format_cli_field(self._params, 'floating', add_comma=(values))
        values += self.format_cli_field(self._params, 'color', add_comma=(values))
        values += self.format_cli_field(self._params, 'after', add_comma=(values))
        values += self.format_cli_field(self._params, 'before', add_comma=(values))
        self.result['commands'].append(log + ' set ' + values)

    def _find_separator(self):
        """ find separator in XML """
        if_elt = self.separators.find(self._interface)
        if if_elt is not None:
            for separator_elt in if_elt:
                if separator_elt.find('text').text == self._name:
                    return separator_elt
        return None

    def _recompute_separators_tag(self):
        """ recompute separators tag name """
        if_elt = self.separators.find(self._interface)
        if if_elt is not None:
            i = 0
            for separator_elt in if_elt:
                name = 'sep' + str(i)
                if separator_elt.tag != name:
                    separator_elt.tag = name
                i += 1

    def _get_rule_position(self, descr):
        """ get rule position in interface/floating """
        res = self.pfsense.get_rule_position(descr, self._interface, self._floating)
        if res is None:
            self.module.fail_json(msg='Failed to find rule=%s interface=%s' % (descr, self._interface_name))
        return res

    def _get_separator_position(self):
        """ get separator position in interface/floating """
        separator_elt = self._find_separator()
        if separator_elt is not None:
            return int(separator_elt.find('row').text.replace('fr', ''))
        return None

    def _get_expected_separator_position(self):
        """ get expected separator position in interface/floating """
        if self._before == 'bottom':
            return self.pfsense.get_interface_rules_count(self._interface, self._floating)
        elif self._after == 'top':
            return 0
        elif self._after is not None:
            return self._get_rule_position(self._after) + 1
        elif self._before is not None:
            return self._get_rule_position(self._before)
        else:
            position = self._get_separator_position()
            if position is not None:
                return position
            return self.pfsense.get_interface_rules_count(self._interface, self._floating)
        return -1

    def _update(self):
        """ make the target pfsense reload separators """
        return self.pfsense.phpshell('''require_once("filter.inc");
if (filter_configure() == 0) { clear_subsystem_dirty('filter'); }''')

    def commit_changes(self):
        """ apply changes and exit module """
        self.result['stdout'] = ''
        self.result['stderr'] = ''
        if self.result['changed'] and not self.module.check_mode:
            self.pfsense.write_config(descr=self.change_descr)
            (dummy, self.result['stdout'], self.result['stderr']) = self._update()

        self.module.exit_json(**self.result)

    def _add(self):
        """ add or update separator """
        self._separator['row'] = 'fr' + str(self._get_expected_separator_position())
        separator_elt = self._find_separator()
        if separator_elt is None:
            if_elt = self.separators.find(self._interface)
            if if_elt is None:
                if_elt = self.pfsense.new_element(self._interface)
                self.separators.append(if_elt)

            separator_elt = self.pfsense.new_element('sep')
            self.pfsense.copy_dict_to_element(self._separator, separator_elt)
            if_elt.append(separator_elt)
            self._recompute_separators_tag()
            self.change_descr = 'ansible pfsense_rule_separator added %s interface %s' % (self._name, self._interface_name)
            self._log_create()
            changed = True
        else:
            changed = self.pfsense.copy_dict_to_element(self._separator, separator_elt)
            if changed:
                self.change_descr = 'ansible pfsense_rule_separator updated "%s interface %s"' % (self._name, self._interface_name)
                self._log_update()

        if changed:
            self.result['changed'] = changed

    def _remove_separator_elt(self, separator_elt):
        """ delete separator_elt from xml """
        if_elt = self.separators.find(self._interface)
        if_elt.remove(separator_elt)
        self.result['changed'] = True
        self._recompute_separators_tag()

    def _remove(self):
        """ delete separator """
        separator_elt = self._find_separator()
        if separator_elt is not None:
            self._remove_separator_elt(separator_elt)
            self.change_descr = 'ansible pfsense_rule_separator removed "%s interface %s' % (self._name, self._interface_name)
            self._log_delete()

    def _params_to_separator(self, params):
        """ return an separator dict from module params """
        separator = dict()
        separator['text'] = params['name']
        if params.get('floating'):
            self._interface_name = 'floating'
            separator['if'] = 'floatingrules'
        else:
            self._interface_name = params['interface']
            separator['if'] = self.pfsense.parse_interface(params['interface'])

        if params['state'] == 'present':
            separator['color'] = 'bg-' + params['color']

        return separator

    def run(self, params):
        """ process input params to add/update/delete a separator """
        self._separator = self._params_to_separator(params)
        self._params = params
        self._name = self._separator['text']
        self._interface = self._separator['if']
        self._floating = (params.get('floating'))
        self._after = params.get('after')
        self._before = params.get('before')

        if params['state'] == 'absent':
            self._remove()
        else:
            self._add()
