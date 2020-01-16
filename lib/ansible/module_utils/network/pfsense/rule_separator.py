# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Orion Poplawski <orion@nwra.com>
# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type
from ansible.module_utils.network.pfsense.module_base import PFSenseModuleBase

RULE_SEPARATOR_ARGUMENT_SPEC = dict(
    name=dict(required=True, type='str'),
    state=dict(default='present', choices=['present', 'absent']),
    interface=dict(required=False, type='str'),
    floating=dict(required=False, type='bool'),
    color=dict(default='info', required=False, choices=['info', 'warning', 'danger', 'success']),
    after=dict(default=None, required=False, type='str'),
    before=dict(default=None, required=False, type='str'),
)

RULE_SEPARATOR_REQUIRED_ONE_OF = [['interface', 'floating']]
RULE_SEPARATOR_MUTUALLY_EXCLUSIVE = [['interface', 'floating']]


class PFSenseRuleSeparatorModule(PFSenseModuleBase):
    """ module managing pfsense rule separators """

    ##############################
    # init
    #
    def __init__(self, module, pfsense=None):
        super(PFSenseRuleSeparatorModule, self).__init__(module, pfsense)
        self.name = "pfsense_rule_separator"
        self.root_elt = None
        self.obj = dict()

        self.separators = self.pfsense.rules.find('separator')
        if self.separators is None:
            self.separators = self.pfsense.new_element('separator')
            self.pfsense.rules.append(self.separators)

        self._interface_name = None
        self._floating = None
        self._after = None
        self._before = None

    ##############################
    # params processing
    #
    def _params_to_obj(self):
        """ return an separator dict from module params """
        params = self.params

        self._floating = (params.get('floating'))
        self._after = params.get('after')
        self._before = params.get('before')

        obj = dict()
        self.obj = obj
        obj['text'] = params['name']
        if params.get('floating'):
            self._interface_name = 'floating'
            obj['if'] = 'floatingrules'
        else:
            self._interface_name = params['interface']
            obj['if'] = self.pfsense.parse_interface(params['interface'])

        if params['state'] == 'present':
            obj['color'] = 'bg-' + params['color']
            obj['row'] = 'fr' + str(self._get_expected_separator_position())

        self.root_elt = self.separators.find(obj['if'])
        if self.root_elt is None:
            self.root_elt = self.pfsense.new_element(obj['if'])
            self.separators.append(self.root_elt)

        return obj

    ##############################
    # XML processing
    #
    def _create_target(self):
        """ create the XML target_elt """
        return self.pfsense.new_element('sep')

    def _copy_and_add_target(self):
        """ create the XML target_elt """
        self.pfsense.copy_dict_to_element(self.obj, self.target_elt)
        self.root_elt.append(self.target_elt)
        self._recompute_separators_tag()

    def _find_target(self):
        """ find the XML target_elt """
        if_elt = self.separators.find(self.obj['if'])
        if if_elt is not None:
            for separator_elt in if_elt:
                if separator_elt.find('text').text == self.obj['text']:
                    return separator_elt
        return None

    def _get_expected_separator_position(self):
        """ get expected separator position in interface/floating """
        if self._before == 'bottom':
            return self.pfsense.get_interface_rules_count(self.obj['if'], self._floating)
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
            return self.pfsense.get_interface_rules_count(self.obj['if'], self._floating)
        return -1

    def _get_rule_position(self, descr):
        """ get rule position in interface/floating """
        res = self.pfsense.get_rule_position(descr, self.obj['if'], self._floating)
        if res is None:
            self.module.fail_json(msg='Failed to find rule=%s interface=%s' % (descr, self._interface_name))
        return res

    def _get_separator_position(self):
        """ get separator position in interface/floating """
        separator_elt = self._find_target()
        if separator_elt is not None:
            return int(separator_elt.find('row').text.replace('fr', ''))
        return None

    def _post_remove_target_elt(self):
        """ processing after removing elt """
        self._recompute_separators_tag()

    def _recompute_separators_tag(self):
        """ recompute separators tag name """
        if_elt = self.separators.find(self.obj['if'])
        if if_elt is not None:
            i = 0
            for separator_elt in if_elt:
                name = 'sep' + str(i)
                if separator_elt.tag != name:
                    separator_elt.tag = name
                i += 1

    ##############################
    # run
    #
    def _update(self):
        """ make the target pfsense reload separators """
        return self.pfsense.phpshell('''require_once("filter.inc");
if (filter_configure() == 0) { clear_subsystem_dirty('filter'); }''')

    ##############################
    # Logging
    #
    def _get_obj_name(self):
        """ return obj's name """
        return "'{0}' on '{1}'".format(self.obj['text'], self._interface_name)

    def _log_fields(self, before=None):
        """ generate pseudo-CLI command fields parameters to create an obj """
        values = ''
        if before is None:
            values += self.format_cli_field(self.params, 'color')
            values += self.format_cli_field(self.params, 'after')
            values += self.format_cli_field(self.params, 'before')
        else:
            values += self.format_cli_field(self.params, 'color', add_comma=(values))
            values += self.format_cli_field(self.params, 'after', add_comma=(values))
            values += self.format_cli_field(self.params, 'before', add_comma=(values))
        return values
