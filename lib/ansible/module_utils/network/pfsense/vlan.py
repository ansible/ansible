# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type
from ansible.module_utils.network.pfsense.module_base import PFSenseModuleBase

VLAN_ARGUMENT_SPEC = dict(
    state=dict(default='present', choices=['present', 'absent']),
    interface=dict(required=True, type='str'),
    vlan_id=dict(required=True, type='int'),
    priority=dict(default=None, required=False, type='int'),
    descr=dict(default='', type='str'),
)


class PFSenseVlanModule(PFSenseModuleBase):
    """ module managing pfsense vlans """

    ##############################
    # init
    #
    def __init__(self, module, pfsense=None):
        super(PFSenseVlanModule, self).__init__(module, pfsense)
        self.name = "pfsense_vlan"
        self.root_elt = self.pfsense.get_element('vlans')
        self.obj = dict()

        if self.root_elt is None:
            self.root_elt = self.pfsense.new_element('vlans')
            self.pfsense.root.append(self.root_elt)

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

    ##############################
    # params processing
    #
    def _params_to_obj(self):
        """ return a dict from module params """
        params = self.params

        obj = dict()

        obj['tag'] = str(params['vlan_id'])
        if params['interface'] not in self.interfaces:
            obj['if'] = self.pfsense.get_interface_physical_name_by_name(params['interface'])
            if obj['if'] is None:
                obj['if'] = self.pfsense.get_interface_physical_name(params['interface'])
        else:
            obj['if'] = params['interface']

        if params['state'] == 'present':
            if params['priority'] is not None:
                obj['pcp'] = str(params['priority'])
            else:
                obj['pcp'] = ''

            obj['descr'] = params['descr']
            obj['vlanif'] = '{0}.{1}'.format(obj['if'], obj['tag'])

        return obj

    def _validate_params(self):
        """ do some extra checks on input parameters """
        params = self.params

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

    ##############################
    # XML processing
    #
    def _create_target(self):
        """ create the XML target_elt """
        return self.pfsense.new_element('vlan')

    def _find_target(self):
        """ find the XML target_elt """
        return self.pfsense.find_vlan(self.obj['if'], self.obj['tag'])

    def _pre_remove_target_elt(self):
        """ processing before removing elt """
        if self.pfsense.get_interface_by_physical_name('{0}.{1}'.format(self.obj['if'], self.obj['tag'])) is not None:
            self.module.fail_json(
                msg='vlan {0} on {1} cannot be deleted because it is still being used as an interface'.format(self.obj['tag'], self.obj['if'])
            )

    ##############################
    # run
    #
    def _update(self):
        """ make the target pfsense reload """
        return self.pfsense.phpshell('''require_once("filter.inc");
if (filter_configure() == 0) { clear_subsystem_dirty('filter'); }''')

    ##############################
    # Logging
    #
    def _get_obj_name(self):
        """ return obj's name """
        return "'{0}.{1}'".format(self.obj['if'], self.obj['tag'])

    def _log_fields(self, before=None):
        """ generate pseudo-CLI command fields parameters to create an obj """
        values = ''
        if before is None:
            values += self.format_cli_field(self.obj, 'descr')
            values += self.format_cli_field(self.obj, 'pcp', fname='priority')
        else:
            values += self.format_updated_cli_field(self.obj, before, 'pcp', add_comma=(values), fname='priority')
            values += self.format_updated_cli_field(self.obj, before, 'descr', add_comma=(values))
        return values
