# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type
from ansible.module_utils.network.pfsense.module_base import PFSenseModuleBase
from ansible.module_utils.compat.ipaddress import ip_address, ip_network

GATEWAY_ARGUMENT_SPEC = dict(
    state=dict(default='present', choices=['present', 'absent']),
    name=dict(required=True, type='str'),
    interface=dict(required=False, type='str'),
    ipprotocol=dict(default='inet', choices=['inet', 'inet6']),
    gateway=dict(required=False, type='str'),
    descr=dict(default='', type='str'),
    disabled=dict(default=False, type='bool'),
    monitor=dict(required=False, type='str'),
    monitor_disable=dict(default=False, type='bool'),
    action_disable=dict(default=False, type='bool'),
    force_down=dict(default=False, type='bool'),
    weight=dict(default=1, required=False, type='int'),
)

GATEWAY_REQUIRED_IF = [
    ["state", "present", ["interface", "gateway", "weight"]],
]


class PFSenseGatewayModule(PFSenseModuleBase):
    """ module managing pfsense gateways """

    ##############################
    # init
    #
    def __init__(self, module, pfsense=None):
        super(PFSenseGatewayModule, self).__init__(module, pfsense)
        self.name = "pfsense_gateway"
        self.root_elt = self.pfsense.get_element('gateways')
        self.obj = dict()
        self.interface_elt = None
        self.dynamic = False
        self.target_elt = None

        if self.root_elt is None:
            self.root_elt = self.pfsense.new_element('gateways')
            self.pfsense.root.append(self.root_elt)

    ##############################
    # params processing
    #
    def _check_gateway_groups(self):
        """ check if gateway is in use in gateway groups """
        for elt in self.root_elt:
            if (elt.tag == 'defaultgw4' or elt.tag == 'defaultgw6') and (elt.text is not None and elt.text == self.params['name']):
                return False

            if elt.tag != 'gateway_group':
                continue

            items = elt.findall('.//item')
            for item in items:
                fields = item.text.split('|')
                if fields and fields[0] == self.params['name']:
                    return False

        return True

    def _check_routes(self):
        """ check if gateway is in use in static routes """
        routes = self.pfsense.get_element('staticroutes')
        if routes is None:
            return True

        for elt in routes:
            if elt.find('gateway').text == self.params['name']:
                return False

        return True

    def _check_subnet(self):
        """ check if addr lies into interface subnets """
        def _check_vips():
            virtualips = self.pfsense.get_element('virtualip')
            if virtualips is None:
                return False

            for vip_elt in virtualips:
                if vip_elt.find('interface').text != self.interface_elt.tag or vip_elt.find('mode').text != 'other' or vip_elt.find('type').text != 'network':
                    continue

                subnet = ip_network(u'{0}/{1}'.format(vip_elt.find('subnet').text, vip_elt.find('subnet_bits').text), strict=False)
                if addr in subnet:
                    return True
            return False

        if self.params['ipprotocol'] == 'inet':
            inet_type = 'IPv4'
            f1_elt = self.interface_elt.find('ipaddr')
            f2_elt = self.interface_elt.find('subnet')
        else:
            inet_type = 'IPv6'
            f1_elt = self.interface_elt.find('ipaddrv6')
            f2_elt = self.interface_elt.find('subnetv6')
        if f1_elt is None or f1_elt.text is None or f2_elt is None or f2_elt.text is None:
            self.module.fail_json(msg='Cannot add {0} Gateway Address because no {0} address could be found on the interface.'.format(inet_type))

        try:
            addr = ip_address(u'{0}'.format(self.params['gateway']))
            subnet = ip_network(u'{0}/{1}'.format(f1_elt.text, f2_elt.text), strict=False)
            if addr in subnet or _check_vips():
                return

            self.module.fail_json(msg="The gateway address {0} does not lie within one of the chosen interface's subnets.".format(self.params['gateway']))
        except ValueError:
            self.module.fail_json(msg='Cannot add {0} Gateway Address because no {0} address could be found on the interface.'.format(inet_type))

    def _params_to_obj(self):
        """ return a dict from module params """
        params = self.params

        obj = dict()

        obj['name'] = params['name']
        if params['state'] == 'present':
            self._get_interface(params['interface'], obj)
            self._get_ansible_param(obj, 'ipprotocol')
            self._get_ansible_param(obj, 'gateway')
            self._get_ansible_param(obj, 'descr')
            self._get_ansible_param(obj, 'monitor')
            self._get_ansible_param(obj, 'weight')

            self._get_ansible_param_bool(obj, 'disabled')
            self._get_ansible_param_bool(obj, 'monitor_disable')
            self._get_ansible_param_bool(obj, 'action_disable')
            self._get_ansible_param_bool(obj, 'force_down')

            if not self.dynamic:
                self._check_subnet()
            elif self.target_elt.find('interface').text != obj['interface']:
                self.module.fail_json(msg="The gateway use 'dynamic' as a target. You can not change the interface")
            elif self.target_elt.find('ipprotocol').text != params['ipprotocol']:
                self.module.fail_json(msg="The gateway use 'dynamic' as a target. You can not change ipprotocol")

        return obj

    def _validate_params(self):
        """ do some extra checks on input parameters """
        params = self.params

        self.target_elt = self.pfsense.find_gateway_elt(params['name'])
        if self.target_elt is not None and self.target_elt.find('gateway').text == 'dynamic':
            self.dynamic = True

        if params['state'] == 'present':
            # check weight
            if params.get('weight') is not None and (params['weight'] < 1 or params['weight'] > 30):
                self.module.fail_json(msg='weight must be between 1 and 30')

            if self.dynamic:
                if params['gateway'] != 'dynamic':
                    self.module.fail_json(msg="The gateway use 'dynamic' as a target. This is read-only, so you must set gateway as dynamic too")
            else:
                if params['ipprotocol'] == 'inet':
                    if not self.pfsense.is_ipv4_address(params['gateway']):
                        self.module.fail_json(msg='gateway must use an IPv4 address')
                    if params.get('monitor') is not None and params['monitor'] != '' and not self.pfsense.is_ipv4_address(params['monitor']):
                        self.module.fail_json(msg='monitor must use an IPv4 address')

                else:
                    if not self.pfsense.is_ipv6_address(params['gateway']):
                        self.module.fail_json(msg='gateway must use an IPv6 address')
                    if params.get('monitor') is not None and params['monitor'] != '' and not self.pfsense.is_ipv6_address(params['monitor']):
                        self.module.fail_json(msg='monitor must use an IPv6 address')

            self.pfsense.check_name(params['name'], 'gateway')

        else:
            if self.dynamic:
                self.module.fail_json(msg="The gateway use 'dynamic' as a target. You can not delete it")
            if not self._check_gateway_groups() or not self._check_routes():
                self.module.fail_json(msg="The gateway is still in use. You can not delete it")

    ##############################
    # XML processing
    #
    def _create_target(self):
        """ create the XML target_elt """
        return self.pfsense.new_element('gateway_item')

    def _find_target(self):
        """ find the XML target_elt """
        return self.pfsense.find_gateway_elt(self.obj['name'])

    def _get_interface(self, name, obj):
        """ return pfsense interface by name """
        for interface in self.pfsense.interfaces:
            descr_elt = interface.find('descr')
            if descr_elt is not None and descr_elt.text.strip() == name:
                obj['interface'] = interface.tag
                self.interface_elt = interface
                return
        self.module.fail_json(msg='Interface {0} not found'.format(name))

    @staticmethod
    def _get_params_to_remove():
        """ returns the list of params to remove if they are not set """
        return ['disabled', 'monitor', 'monitor_disable', 'action_disable', 'force_down']

    ##############################
    # run
    #
    def _update(self):
        """ make the target pfsense reload """
        return self.pfsense.phpshell('''
require_once("filter.inc");
$retval = 0;

$retval |= system_routing_configure();
$retval |= system_resolvconf_generate();
$retval |= filter_configure();
/* reconfigure our gateway monitor */
setup_gateways_monitor();
/* Dynamic DNS on gw groups may have changed */
send_event("service reload dyndnsall");

if ($retval == 0) clear_subsystem_dirty('staticroutes');
''')

    ##############################
    # Logging
    #
    def _get_obj_name(self):
        """ return obj's name """
        return "'{0}'".format(self.obj['name'])

    def _log_fields(self, before=None):
        """ generate pseudo-CLI command fields parameters to create an obj """
        values = ''
        if before is None:
            values += self.format_cli_field(self.params, 'interface')
            values += self.format_cli_field(self.obj, 'ipprotocol', default='inet')
            values += self.format_cli_field(self.obj, 'gateway')
            values += self.format_cli_field(self.obj, 'descr', default='')
            values += self.format_cli_field(self.params, 'disabled', fvalue=self.fvalue_bool, default=False)
            values += self.format_cli_field(self.obj, 'monitor')
            values += self.format_cli_field(self.params, 'monitor_disable', fvalue=self.fvalue_bool, default=False)
            values += self.format_cli_field(self.params, 'action_disable', fvalue=self.fvalue_bool, default=False)
            values += self.format_cli_field(self.params, 'force_down', fvalue=self.fvalue_bool, default=False)
            values += self.format_cli_field(self.obj, 'weight', default='1')
        else:
            fbefore = dict()
            fbefore['interface'] = self.pfsense.get_interface_display_name(before['interface'])

            values += self.format_updated_cli_field(self.params, fbefore, 'interface', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'ipprotocol', default='inet', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'gateway', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'descr', default='', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'disabled', fvalue=self.fvalue_bool, default=False, add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'monitor', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'monitor_disable', fvalue=self.fvalue_bool, default=False, add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'action_disable', fvalue=self.fvalue_bool, default=False, add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'force_down', fvalue=self.fvalue_bool, default=False, add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'weight', default='1', add_comma=(values))

        return values
