# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type
from ansible.module_utils.network.pfsense.module_base import PFSenseModuleBase
from ansible.module_utils.compat.ipaddress import ip_address, ip_network

ROUTE_ARGUMENT_SPEC = dict(
    state=dict(default='present', choices=['present', 'absent']),
    descr=dict(required=True, type='str'),
    gateway=dict(required=False, type='str'),
    network=dict(required=False, type='str'),
    disabled=dict(default=False, type='bool'),
)

ROUTE_REQUIRED_IF = [
    ["state", "present", ["gateway", "network"]],
]


class PFSenseRouteModule(PFSenseModuleBase):
    """ module managing pfsense routes """

    ##############################
    # init
    #
    def __init__(self, module, pfsense=None):
        super(PFSenseRouteModule, self).__init__(module, pfsense)
        self.name = "pfsense_route"
        self.root_elt = self.pfsense.get_element('staticroutes')
        self.obj = dict()
        self.route_cmd = list()

        if self.root_elt is None:
            self.root_elt = self.pfsense.new_element('staticroutes')
            self.pfsense.root.append(self.root_elt)

    ##############################
    # params processing
    #
    def _expand_alias(self, networks):
        """ return real addresses of alias """
        ret = list()

        while len(networks) > 0:
            alias = networks.pop()
            if self.pfsense.is_ip_network(alias, strict=False):
                ret.append(alias)
            else:
                alias_elt = self.pfsense.find_alias(alias, aliastype='host')
                if alias_elt is None:
                    alias_elt = self.pfsense.find_alias(alias, aliastype='network')
                networks += alias_elt.find('address').text.split(' ')

        return ret

    def _params_to_obj(self):
        """ return a dict from module params """
        params = self.params

        obj = dict()
        self.obj = obj

        obj['descr'] = params['descr']
        target_elt = self._find_target()
        if params['state'] == 'present':
            self._get_ansible_param(obj, 'gateway')
            self._get_ansible_param(obj, 'descr')
            self._get_ansible_param(obj, 'network')

            self._get_ansible_param_bool(obj, 'disabled')

        if target_elt is not None:
            old_network = target_elt.find('network').text
            if params['state'] == 'absent' or old_network != params['network']:
                networks = self._expand_alias([old_network])
                for network in networks:
                    if self.pfsense.is_ipv4_address(network):
                        network = network + '/32'
                    elif self.pfsense.is_ipv6_address(old_network):
                        network = network + '/128'

                    if self.pfsense.is_ipv4_network(network, False):
                        family = '-inet'
                    else:
                        family = '-inet6'

                    self.route_cmd.append('/sbin/route delete {0} {1}'.format(family, network))

        return obj

    def _validate_params(self):
        """ do some extra checks on input parameters """
        params = self.params

        if params['state'] == 'present':
            gw_elt = self.pfsense.find_gateway_elt(params['gateway'])
            if gw_elt is None:
                self.module.fail_json(msg='The gateway {0} does not exist'.format(params['gateway']))

            if (self.pfsense.is_ipv4_address(params['network']) and gw_elt.find('ipprotocol').text == 'inet6' or
                    self.pfsense.is_ipv6_address(params['network']) and gw_elt.find('ipprotocol').text == 'inet'):
                msg = 'The gateway "{0}" is a different Address Family than network "{1}".'.format(gw_elt.find('gateway').text, params['network'])
                self.module.fail_json(msg=msg)

            if (not self.pfsense.is_ipv4_network(params['network'], False) and self.pfsense.find_alias(params['network'], aliastype='host') is None and
                    self.pfsense.find_alias(params['network'], aliastype='network') is None):
                self.module.fail_json(msg='A valid IPv4 or IPv6 destination network or alias must be specified.')

    ##############################
    # XML processing
    #
    def _create_target(self):
        """ create the XML target_elt """
        return self.pfsense.new_element('route')

    def _find_target(self):
        """ find the XML target_elt """
        for route_elt in self.root_elt:
            if route_elt.find('descr').text == self.obj['descr']:
                return route_elt
        return None

    @staticmethod
    def _get_params_to_remove():
        """ returns the list of params to remove if they are not set """
        return ['disabled']

    ##############################
    # run
    #
    def _update(self):
        """ make the target pfsense reload """
        for cmd in self.route_cmd:
            self.module.run_command(cmd)

        return self.pfsense.phpshell('''
require_once("filter.inc");
$retval = 0;
if (file_exists("{$g['tmp_path']}/.system_routes.apply")) {
        $toapplylist = unserialize(file_get_contents("{$g['tmp_path']}/.system_routes.apply"));
        foreach ($toapplylist as $toapply)
                mwexec("{$toapply}");
        @unlink("{$g['tmp_path']}/.system_routes.apply");
}

$retval |= system_routing_configure();
$retval |= filter_configure();
/* reconfigure our gateway monitor */
setup_gateways_monitor();

if ($retval == 0) clear_subsystem_dirty('staticroutes');
''')

    ##############################
    # Logging
    #
    def _get_obj_name(self):
        """ return obj's name """
        return "'{0}'".format(self.obj['descr'])

    def _log_fields(self, before=None):
        """ generate pseudo-CLI command fields parameters to create an obj """
        values = ''
        if before is None:
            values += self.format_cli_field(self.obj, 'network')
            values += self.format_cli_field(self.obj, 'gateway')
            values += self.format_cli_field(self.params, 'disabled', fvalue=self.fvalue_bool, default=False)
        else:
            values += self.format_updated_cli_field(self.obj, before, 'network', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'gateway', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'disabled', fvalue=self.fvalue_bool, default=False, add_comma=(values))

        return values
