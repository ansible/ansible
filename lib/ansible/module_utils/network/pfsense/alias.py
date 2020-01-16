# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Orion Poplawski <orion@nwra.com>
# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type
from ansible.module_utils.network.pfsense.module_base import PFSenseModuleBase

ALIAS_ARGUMENT_SPEC = dict(
    name=dict(required=True, type='str'),
    state=dict(default='present', choices=['present', 'absent']),
    type=dict(default=None, required=False, choices=['host', 'network', 'port', 'urltable', 'urltable_ports']),
    address=dict(default=None, required=False, type='str'),
    descr=dict(default=None, required=False, type='str'),
    detail=dict(default=None, required=False, type='str'),
    updatefreq=dict(default=None, required=False, type='int'),
)

ALIAS_REQUIRED_IF = [
    ["type", "urltable", ["updatefreq"]],
    ["type", "urltable_ports", ["updatefreq"]],
]


class PFSenseAliasModule(PFSenseModuleBase):
    """ module managing pfsense aliases """

    ##############################
    # init
    #
    def __init__(self, module, pfsense=None):
        super(PFSenseAliasModule, self).__init__(module, pfsense)
        self.name = "pfsense_alias"
        self.root_elt = self.pfsense.get_element('aliases')
        self.obj = dict()

        self.diff = {}
        self.result['diff'] = self.diff

    ##############################
    # params processing
    #
    def _params_to_obj(self):
        """ return dict from module params """
        obj = dict()
        obj['name'] = self.params['name']
        if self.params['state'] == 'present':
            obj['type'] = self.params['type']
            obj['address'] = self.params['address']
            obj['descr'] = self.params['descr']
            obj['detail'] = self.params['detail']
            if obj['type'] == 'urltable' or obj['type'] == 'urltable_ports':
                obj['url'] = self.params['address']
                obj['updatefreq'] = str(self.params['updatefreq'])

        return obj

    def _validate_params(self):
        """ do some extra checks on input parameters """
        params = self.params

        # check name
        self.pfsense.check_name(params['name'], 'alias')

        # when deleting, only name is allowed
        if params['state'] == 'absent':
            for param, value in sorted(params.items()):
                if param != 'state' and param != 'name' and value is not None:
                    self.module.fail_json(msg=param + " is invalid with state='absent'")
        else:
            # the GUI does not allow to create 2 aliases with same name and differents types
            alias_elt = self.pfsense.find_alias(params['name'])
            if alias_elt is not None:
                if params['type'] != alias_elt.find('type').text:
                    self.module.fail_json(msg='An alias with this name and a different type already exists')

            if self.pfsense.get_interface_pfsense_by_name(params['name']) is not None:
                self.module.fail_json(msg='An interface description with this name already exists')

            missings = ['type', 'address']
            for param, value in params.items():
                if param in missings and value is not None and value != '':
                    missings.remove(param)
            if missings:
                self.module.fail_json(msg='state is present but all of the following are missing: ' + ','.join(missings))

            # updatefreq is for urltable only
            if params['updatefreq'] is not None and params['type'] != 'urltable' and params['type'] != 'urltable_ports':
                self.module.fail_json(msg='updatefreq is only valid with type urltable or urltable_ports')

            # check details count
            details = params['detail'].split('||') if params['detail'] is not None else []
            addresses = params['address'].split(' ')
            if len(details) > len(addresses):
                self.module.fail_json(msg='Too many details in relation to addresses')

            # pfSense GUI rule
            for detail in details:
                if detail.startswith('|') or detail.endswith('|'):
                    self.module.fail_json(msg='Vertical bars (|) at start or end of descriptions not allowed')

    ##############################
    # XML processing
    #
    def _copy_and_update_target(self):
        """ update the XML target_elt """
        before = self.pfsense.element_to_dict(self.target_elt)
        changed = self.pfsense.copy_dict_to_element(self.obj, self.target_elt)
        if self._remove_deleted_params():
            changed = True

        self.diff['before'] = before
        if changed:
            self.diff['after'] = self.pfsense.element_to_dict(self.target_elt)
            self.result['changed'] = True
        else:
            self.diff['after'] = self.obj

        return (before, changed)

    def _create_target(self):
        """ create the XML target_elt """
        target_elt = self.pfsense.new_element('alias')
        self.diff['before'] = ''
        self.diff['after'] = self.obj
        self.result['changed'] = True
        return target_elt

    def _find_target(self):
        """ find the XML target_elt """
        return self.pfsense.find_alias(self.obj['name'])

    def _remove_target_elt(self):
        """ delete target_elt from xml """
        super(PFSenseAliasModule, self)._remove_target_elt()
        self.diff['before'] = self.pfsense.element_to_dict(self.target_elt)

    ##############################
    # run
    #
    def _remove(self):
        """ delete obj """
        self.diff['after'] = ''
        self.diff['before'] = ''
        super(PFSenseAliasModule, self)._remove()

    def _update(self):
        """ make the target pfsense reload """
        return self.pfsense.phpshell('''require_once("filter.inc");
if (filter_configure() == 0) { clear_subsystem_dirty('aliases'); }''')

    ##############################
    # Logging
    #
    def _get_obj_name(self):
        """ return obj's name """
        return "'" + self.obj['name'] + "'"

    def _log_fields(self, before=None):
        """ generate pseudo-CLI command fields parameters to create an obj """
        values = ''
        if before is None:
            values += self.format_cli_field(self.obj, 'type')
            values += self.format_cli_field(self.obj, 'address')
            values += self.format_cli_field(self.obj, 'updatefreq')
            values += self.format_cli_field(self.obj, 'descr')
            values += self.format_cli_field(self.obj, 'detail')
        else:
            values += self.format_updated_cli_field(self.obj, before, 'address', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'updatefreq', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'descr', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'detail', add_comma=(values))
        return values
