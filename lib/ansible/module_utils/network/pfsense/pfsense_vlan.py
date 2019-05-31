# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type
import re
from ansible.module_utils.network.pfsense.pfsense import PFSenseModule, PFSenseModuleBase

VLANS_ARGUMENT_SPEC = dict(
    state=dict(default='present', choices=['present', 'absent']),
    interface=dict(required=True, type='str'),
    vlan_id=dict(required=True, type='int'),
    priority=dict(default=None, required=False, type='int'),
    descr=dict(default='', type='str'),
)


class PFSenseVlanModule(PFSenseModuleBase):
    """ module managing pfsense vlans """

    def __init__(self, module, pfsense=None):
        if pfsense is None:
            pfsense = PFSenseModule(module)
        self.module = module
        self.pfsense = pfsense
        self.vlans = self.pfsense.get_element('vlans')

        self.change_descr = ''

        self.result = {}
        self.result['changed'] = False
        self.result['commands'] = []

        # get physical interfaces on which vlans can be set
        self.interfaces = self.pfsense.php(
            'require_once("/etc/inc/interfaces.inc");'
            '$portlist = get_interface_list();'
            '$lagglist = get_lagg_interface_list();'
            '$portlist = array_merge($portlist, $lagglist);'
            'foreach ($lagglist as $laggif => $lagg) {'
            "    $laggmembers = explode(',', $lagg['members']);"
            '    foreach ($laggmembers as $lagm)'
            '        if (isset($portlist[$lagm]))'
            '            unset($portlist[$lagm]);'
            '}'
            '$list = array();'
            'foreach ($portlist as $ifn => $ifinfo)'
            '   if (is_jumbo_capable($ifn))'
            '       array_push($list, $ifn);'
            'echo json_encode($list);')

    def _log_create(self, vlan):
        """ generate pseudo-CLI command to create an vlan """
        log = "create vlan '{0}.{1}'".format(vlan['if'], vlan['tag'])
        log += self.format_cli_field(vlan, 'descr')
        log += self.format_cli_field(vlan, 'pcp', fname='priority')
        self.result['commands'].append(log)

    def _log_delete(self, vlan):
        """ generate pseudo-CLI command to delete an vlan """
        log = "delete vlan '{0}.{1}'".format(vlan['if'], vlan['tag'])
        self.result['commands'].append(log)

    def _log_update(self, vlan, before):
        """ generate pseudo-CLI command to update an vlan """
        log = "update vlan '{0}.{1}'".format(vlan['if'], vlan['tag'])
        values = ''
        values += self.format_updated_cli_field(vlan, before, 'pcp', add_comma=(values), fname='priority')
        values += self.format_updated_cli_field(vlan, before, 'descr', add_comma=(values))
        self.result['commands'].append(log + ' set ' + values)

    def _add(self, vlan):
        """ add or update vlan """
        vlan_elt = self.pfsense.find_vlan(vlan['if'], vlan['tag'])
        if vlan_elt is None:
            vlan_elt = self.pfsense.new_element('vlan')
            self.pfsense.copy_dict_to_element(vlan, vlan_elt)
            self.vlans.append(vlan_elt)

            changed = True
            self.change_descr = 'ansible pfsense_vlan added {0} on {1}'.format(vlan['tag'], vlan['if'])
            self._log_create(vlan)
        else:
            before = self.pfsense.element_to_dict(vlan_elt)
            changed = self.pfsense.copy_dict_to_element(vlan, vlan_elt)

            if changed:
                self.change_descr = 'ansible pfsense_vlan updated {0} on {1}'.format(vlan['tag'], vlan['if'])
                self._log_update(vlan, before)

        if changed:
            self.result['changed'] = changed

    def _remove_vlan_elt(self, vlan_elt):
        """ delete vlan_elt from xml """
        self.vlans.remove(vlan_elt)
        self.result['changed'] = True

    def _remove(self, vlan):
        """ delete vlan """
        vlan_elt = self.pfsense.find_vlan(vlan['if'], vlan['tag'])
        if vlan_elt is not None:
            if self.pfsense.get_interface_by_physical_name('{0}.{1}'.format(vlan['if'], vlan['tag'])) is not None:
                self.module.fail_json(msg='vlan {0} on {1} cannot be deleted because it is still being used as an interface'.format(vlan['tag'], vlan['if']))

            self._log_delete(vlan)
            self._remove_vlan_elt(vlan_elt)
            self.change_descr = 'ansible pfsense_vlan removed {0} on {1}'.format(vlan['tag'], vlan['if'])

    def _validate_params(self, params):
        """ do some extra checks on input parameters """
        # check interface
        if params['interface'] not in self.interfaces:
            # check with assign or friendly name
            interface = self.pfsense.get_interface_physical_name_by_name(params['interface'])
            if interface is None:
                interface = self.pfsense.get_interface_physical_name(params['interface'])

            if interface is None or interface not in self.interfaces:
                self.module.fail_json(msg='Vlans can\'t be set on interface {0}'.format(params['interface']))

        # check vlan
        if params['vlan_id'] < 1 or params['vlan_id'] > 4094:
            self.module.fail_json(msg='vlan_id must be between 1 and 4094 on interface {0}'.format(params['interface']))

        # check priority
        if params.get('priority') is not None and (params['priority'] < 0 or params['priority'] > 7):
            self.module.fail_json(msg='priority must be between 0 and 7 on interface {0}'.format(params['interface']))

    def _params_to_vlan(self, params):
        """ return an vlan dict from module params """
        self._validate_params(params)

        vlan = dict()

        vlan['tag'] = str(params['vlan_id'])
        if params['interface'] not in self.interfaces:
            vlan['if'] = self.pfsense.get_interface_physical_name_by_name(params['interface'])
            if vlan['if'] is None:
                vlan['if'] = self.pfsense.get_interface_physical_name(params['interface'])
        else:
            vlan['if'] = params['interface']

        if params['state'] == 'present':
            if params['priority'] is not None:
                vlan['pcp'] = str(params['priority'])
            else:
                vlan['pcp'] = ''

            vlan['descr'] = params['descr']
            vlan['vlanif'] = '{0}.{1}'.format(vlan['if'], vlan['tag'])

        return vlan

    def commit_changes(self):
        """ apply changes and exit module """
        self.result['stdout'] = ''
        self.result['stderr'] = ''
        if self.result['changed'] and not self.module.check_mode:
            self.pfsense.write_config(descr=self.change_descr)

        self.module.exit_json(**self.result)

    def run(self, params):
        """ process input params to add/update/delete an vlan """
        vlan = self._params_to_vlan(params)

        if params['state'] == 'absent':
            self._remove(vlan)
        else:
            self._add(vlan)
