# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type
import re
from ansible.module_utils.network.pfsense.module_base import PFSenseModuleBase
from ansible.module_utils.network.pfsense.rule import PFSenseRuleModule
from ansible.module_utils.compat.ipaddress import ip_network

INTERFACE_ARGUMENT_SPEC = dict(
    state=dict(default='present', choices=['present', 'absent']),
    descr=dict(required=True, type='str'),
    interface=dict(required=False, type='str'),
    enable=dict(required=False, type='bool'),
    ipv4_type=dict(default='none', choices=['none', 'static']),
    mac=dict(required=False, type='str'),
    mtu=dict(required=False, type='int'),
    mss=dict(required=False, type='int'),
    speed_duplex=dict(default='autoselect', required=False, type='str'),
    ipv4_address=dict(required=False, type='str'),
    ipv4_prefixlen=dict(default=24, required=False, type='int'),
    ipv4_gateway=dict(required=False, type='str'),
    create_ipv4_gateway=dict(required=False, type='bool'),
    ipv4_gateway_address=dict(required=False, type='str'),
    blockpriv=dict(required=False, type='bool'),
    blockbogons=dict(required=False, type='bool'),
)

INTERFACE_REQUIRED_IF = [
    ["state", "present", ["interface", "ipv4_type"]],
    ["ipv4_type", "static", ["ipv4_address", "ipv4_prefixlen"]],
    ["create_ipv4_gateway", True, ["ipv4_gateway_address"]],
]


class PFSenseInterfaceModule(PFSenseModuleBase):
    """ module managing pfsense interfaces """

    ##############################
    # init
    #
    def __init__(self, module, pfsense=None):
        super(PFSenseInterfaceModule, self).__init__(module, pfsense)
        self.name = "pfsense_interface"
        self.obj = dict()

        self.root_elt = self.pfsense.interfaces
        self.target_elt = None

    ##############################
    # params processing
    #
    def _check_overlaps(self):
        """ check new address does not overlaps with one existing """

        if not self.obj.get('ipaddr'):
            return

        our_addr = ip_network(u'{0}/{1}'.format(self.obj['ipaddr'], self.obj['subnet']), strict=False)

        for iface in self.root_elt:
            if iface == self.target_elt:
                continue

            ipaddr_elt = iface.find('ipaddr')
            subnet_elt = iface.find('subnet')
            if ipaddr_elt is None or subnet_elt is None or ipaddr_elt.text == 'dhcp':
                continue

            other_addr = ip_network(u'{0}/{1}'.format(ipaddr_elt.text, subnet_elt.text), strict=False)
            if our_addr.overlaps(other_addr):
                descr_elt = iface.find('descr')
                if descr_elt is not None and descr_elt.text:
                    ifname = descr_elt.text
                else:
                    ifname = iface.tag
                msg = 'IPv4 address {0}/{1} is being used by or overlaps with: {2} ({3}/{4})'.format(
                    self.obj['ipaddr'],
                    self.obj['subnet'],
                    ifname,
                    ipaddr_elt.text,
                    subnet_elt.text
                )
                self.module.fail_json(msg=msg)

    def _params_to_obj(self):
        """ return an interface dict from module params """
        params = self.params

        obj = dict()
        self.obj = obj
        obj['descr'] = params['descr']
        if params['state'] == 'present':
            obj['if'] = params['interface']

            for param in ['enable', 'blockpriv', 'blockbogons']:
                self._get_ansible_param_bool(obj, param, value='')

            self._get_ansible_param(obj, 'mac', fname='spoofmac', force=True)
            self._get_ansible_param(obj, 'mtu')
            self._get_ansible_param(obj, 'mss')
            self._get_ansible_param(obj, 'speed_duplex', fname='media', exclude='autoselect')

            if params['ipv4_type'] == 'static':
                self._get_ansible_param(obj, 'ipv4_address', fname='ipaddr')
                self._get_ansible_param(obj, 'ipv4_prefixlen', fname='subnet')
                self._get_ansible_param(obj, 'ipv4_gateway', fname='gateway')

            # get target interface
            self.target_elt = self._find_matching_interface()
            self._check_overlaps()
        else:
            self.target_elt = self._find_interface_elt_by_name()

        return obj

    def _validate_params(self):
        """ do some extra checks on input parameters """

        params = self.params

        # check name
        if re.match('^[a-zA-Z0-9_]+$', params['descr']) is None:
            self.module.fail_json(msg='The name of the interface may only consist of the characters "a-z, A-Z, 0-9 and _"')

        if params['state'] == 'present':
            if params.get('mac') and re.match('^([0-9A-F]{2}[:-]){5}([0-9A-F]{2})$', params['mac']) is None:
                self.module.fail_json(msg='MAC address must be in the following format: xx:xx:xx:xx:xx:xx (or blank).')

            # todo can't change mac address on vlan interface

            if params.get('ipv4_prefixlen') is not None and params['ipv4_prefixlen'] < 1 or params['ipv4_prefixlen'] > 32:
                self.module.fail_json(msg='ipv4_prefixlen must be between 1 and 32.')

            if params.get('mtu') is not None and params['mtu'] < 1:
                self.module.fail_json(msg='mtu must be above 0')

            if params.get('mss') is not None and params['mtu'] < 1:
                self.module.fail_json(msg='mtu must be above 0')

            interfaces = self._get_interface_list()
            if params['interface'] not in interfaces:
                self.module.fail_json(msg='{0} can\'t be assigned. Interface may only be one the following: {1}'.format(params['interface'], interfaces))

            media_modes = set(self._get_media_mode(params['interface']))
            media_modes.add('autoselect')
            if params.get('speed_duplex') and params['speed_duplex'] not in media_modes:
                self.module.fail_json(msg='For this interface, media mode may only be one the following: {0}'.format(media_modes))

            if params['ipv4_type'] == 'static':
                if params.get('ipv4_address') and not self.pfsense.is_ip_address(params['ipv4_address']):
                    self.module.fail_json(msg='{0} is not a valid ip address'.format(params['ipv4_address']))

            if params.get('create_ipv4_gateway'):
                if params.get('ipv4_gateway_address') and not self.pfsense.is_ip_address(params['ipv4_gateway_address']):
                    self.module.fail_json(msg='{0} is not a valid ip address'.format(params['ipv4_gateway_address']))

    ##############################
    # XML processing
    #
    def _copy_and_add_target(self):
        """ create the XML target_elt """
        self.pfsense.copy_dict_to_element(self.obj, self.target_elt)
        self._create_gateway()

    def _copy_and_update_target(self):
        """ update the XML target_elt """
        before = self.pfsense.element_to_dict(self.target_elt)
        changed = self.pfsense.copy_dict_to_element(self.obj, self.target_elt)
        if self._remove_deleted_params():
            changed = True

        if self._create_gateway():
            changed = True

        return (before, changed)

    def _create_gateway(self):
        """ create gateway if required """

        # todo: maybe it would be better to create a module to manage gateways and to call it there
        if self.obj.get('gateway') and not self.pfsense.find_gateway_elt(self.obj['gateway'], self.target_elt.tag, 'inet'):
            if not self.params.get('create_ipv4_gateway'):
                self.module.fail_json(msg='Gateway {0} does not exist on {1}'.format(self.obj['gateway'], self.obj['descr']))

            gateway_elt = self.pfsense.new_element('gateway_item')
            gateway = {}
            gateway['interface'] = self.target_elt.tag
            gateway['gateway'] = self.params['ipv4_gateway_address']
            gateway['name'] = self.obj['gateway']
            gateway['weight'] = ''
            gateway['ipprotocol'] = 'inet'
            gateway['descr'] = ''
            self.pfsense.copy_dict_to_element(gateway, gateway_elt)
            self.pfsense.gateways.append(gateway_elt)

            cmd = 'create gateway \'{0}\', interface=\'{1}\', ip=\'{2}\''.format(self.obj['gateway'], self.target_elt.tag, self.params['ipv4_gateway_address'])
            self.result['commands'].append(cmd)
            return True
        return False

    def _create_target(self):
        """ create the XML target_elt """
        # wan can't be deleted, so the first interface we can create is lan
        if self._find_interface_elt_by_tag('lan') is None:
            interface_elt = self.pfsense.new_element('lan')
            self.root_elt.insert(1, interface_elt)
            return interface_elt

        # lan is used, so we must create an optX interface
        i = 1
        while True:
            interface = 'opt{0}'.format(i)
            if self._find_interface_elt_by_tag(interface) is None:
                interface_elt = self.pfsense.new_element(interface)
                # i + 1 = i + (lan and wan) - 1
                self.root_elt.insert(i + 1, interface_elt)
                return interface_elt
            i = i + 1

    def _find_interface_elt(self):
        """ return pfsense interface physical name """
        for iface in self.root_elt:
            descr_elt = iface.find('descr')
            if descr_elt is None:
                continue
            if iface.find('if').text.strip() == self.obj['if'] and descr_elt.text.strip().lower() == self.obj['descr'].lower():
                return iface
        return None

    def _find_interface_elt_by_name(self):
        """ return pfsense interface by name """
        for iface in self.root_elt:
            descr_elt = iface.find('descr')
            if descr_elt is None:
                continue
            if descr_elt.text.strip().lower() == self.obj['descr'].lower():
                return iface
        return None

    def _get_interface_name_by_physical_name(self):
        """ return pfsense interface physical name """
        for iface in self.root_elt:
            if iface.find('if').text.strip() == self.obj['if']:
                descr_elt = iface.find('descr')
                if descr_elt is not None:
                    return descr_elt.text.strip()
                return iface.tag

        return None

    def _find_interface_elt_by_port(self):
        """ find pfsense interface by port name """
        for iface in self.root_elt:
            if iface.find('if').text.strip() == self.obj['if']:
                return iface
        return None

    def _find_interface_elt_by_tag(self, interface):
        """ find pfsense interface by port name """
        for iface in self.root_elt:
            if iface.tag == interface:
                return iface
        return None

    def _find_matching_interface(self):
        """ return target interface """

        # we first try to find an interface having same name and physical
        interface_elt = self._find_interface_elt()
        if interface_elt is not None:
            return interface_elt

        # we then try to find an existing interface with the name
        interface_elt = self._find_interface_elt_by_name()
        if interface_elt is not None:
            # we check the targeted physical interface can be used
            used_by = self._get_interface_name_by_physical_name()
            if used_by is not None:
                self.module.fail_json(msg='Port {0} is already in use on interface {1}'.format(self.obj['if'], used_by))
            return interface_elt

        # last, we  try to find an existing interface with the port (interface will be renamed)
        return self._find_interface_elt_by_port()

    def _find_target(self):
        """ find the XML target_elt """
        return self.target_elt

    @staticmethod
    def _get_params_to_remove():
        """ returns the list of params to remove if they are not set """
        params = ['mtu', 'mss', 'gateway', 'enable', 'mac', 'media', 'ipaddr', 'subnet', 'blockpriv', 'blockbogons']
        return params

    def _pre_remove_target_elt(self):
        """ processing before removing elt """
        self.obj['if'] = self.target_elt.find('if').text
        self._remove_all_separators(self.target_elt.tag)
        self._remove_all_rules(self.target_elt.tag)

    def _remove_all_rules(self, interface):
        """ delete all interface rules """

        # we use the pfsense_rule module to delete the rules since, at least for floating rules,
        # it implies to recalculate separators positions
        # if we have to just remove the deleted interface of a floating rule we do it ourselves
        todel = []
        for rule_elt in self.pfsense.rules:
            if rule_elt.find('floating') is not None:
                interfaces = rule_elt.find('interface').text.split(',')
                old_ifs = ','.join([self.pfsense.get_interface_display_name(interface) for interface in interfaces])
                if interface in interfaces:
                    if len(interfaces) > 1:
                        interfaces.remove(interface)
                        new_ifs = ','.join([self.pfsense.get_interface_display_name(new_interface) for new_interface in interfaces])
                        rule_elt.find('interface').text = ','.join(interfaces)
                        cmd = 'update rule \'{0}\' on \'floating({1})\' set interface=\'{2}\''.format(rule_elt.find('descr').text, old_ifs, new_ifs)
                        self.result['commands'].append(cmd)
                        continue
                    todel.append(rule_elt)
                else:
                    continue
            else:
                iface = rule_elt.find('interface')
                if iface is not None and iface.text == interface:
                    todel.append(rule_elt)

        if todel:
            pfsense_rules = PFSenseRuleModule(self.module, self.pfsense)
            for rule_elt in todel:
                params = {}
                params['state'] = 'absent'
                params['name'] = rule_elt.find('descr').text
                params['interface'] = rule_elt.find('interface').text
                if rule_elt.find('floating') is not None:
                    params['floating'] = True
                pfsense_rules.run(params)
            if pfsense_rules.result['commands']:
                self.result['commands'].extend(pfsense_rules.result['commands'])

    def _remove_all_separators(self, interface):
        """ delete all interface separators """
        todel = []
        separators = self.pfsense.rules.find('separator')
        for interface_elt in separators:
            if interface_elt.tag != interface:
                continue
            for separator_elt in interface_elt:
                todel.append(separator_elt)
            for separator_elt in todel:
                cmd = 'delete rule_separator \'{0}\', interface=\'{1}\''.format(separator_elt.find('text').text, interface)
                self.result['commands'].append(cmd)
                interface_elt.remove(separator_elt)
            separators.remove(interface_elt)
            break

    ##############################
    # run
    #
    def _get_interface_list(self):
        return self.pfsense.php(
            "require_once('/etc/inc/interfaces.inc');"
            "$portlist = get_interface_list();"
            ""
            "/* add wireless clone interfaces */"
            "if (is_array($config['wireless']['clone']) && count($config['wireless']['clone']))"
            "    foreach ($config['wireless']['clone'] as $clone)  $portlist[$clone['cloneif']] = $clone;"
            ""
            "/* add VLAN interfaces */"
            "if (is_array($config['vlans']['vlan']) && count($config['vlans']['vlan']))"
            "    foreach ($config['vlans']['vlan'] as $vlan)  $portlist[$vlan['vlanif']] = $vlan;"
            ""
            "/* add Bridge interfaces */"
            "if (is_array($config['bridges']['bridged']) && count($config['bridges']['bridged']))"
            "    foreach ($config['bridges']['bridged'] as $bridge) $portlist[$bridge['bridgeif']] = $bridge;"
            ""
            "/* add GIF interfaces */"
            "if (is_array($config['gifs']['gif']) && count($config['gifs']['gif']))"
            "    foreach ($config['gifs']['gif'] as $gif) $portlist[$gif['gifif']] = $gif;"
            ""
            "/* add GRE interfaces */"
            "if (is_array($config['gres']['gre']) && count($config['gres']['gre']))"
            "    foreach ($config['gres']['gre'] as $gre) $portlist[$gre['greif']] = $gre;"
            ""
            "/* add LAGG interfaces */"
            "if (is_array($config['laggs']['lagg']) && count($config['laggs']['lagg']))"
            "    foreach ($config['laggs']['lagg'] as $lagg) {"
            "        $portlist[$lagg['laggif']] = $lagg;"
            "        /* LAGG members cannot be assigned */"
            "        $lagifs = explode(',', $lagg['members']);"
            "        foreach ($lagifs as $lagif)"
            "            if (isset($portlist[$lagif])) unset($portlist[$lagif]);"
            "    }"
            ""
            "/* add QinQ interfaces */"
            "if (is_array($config['qinqs']['qinqentry']) && count($config['qinqs']['qinqentry']))"
            "    foreach ($config['qinqs']['qinqentry'] as $qinq) {"
            "        $portlist[\"{$qinq['vlanif']}\"] = $qinq;"
            "        /* QinQ members */"
            "        $qinqifs = explode(' ', $qinq['members']);"
            "        foreach ($qinqifs as $qinqif) $portlist[\"{$qinq['vlanif']}.{$qinqif}\"] = $qinqif;"
            "    }"
            ""
            "/* add PPP interfaces */"
            "if (is_array($config['ppps']['ppp']) && count($config['ppps']['ppp']))"
            "    foreach ($config['ppps']['ppp'] as $pppid => $ppp) $portlist[$ppp['if']] = $ppp;"
            ""
            "if (is_array($config['openvpn'])) {"
            "    if (is_array($config['openvpn']['openvpn-server']))"
            "        foreach ($config['openvpn']['openvpn-server'] as $s) $portlist[\"ovpns{$s['vpnid']}\"] = $s;"
            "    if (is_array($config['openvpn']['openvpn-client']))"
            "        foreach ($config['openvpn']['openvpn-client'] as $c)  $portlist[\"ovpns{$c['vpnid']}\"] = $c;"
            "}"
            ""
            "$ipsec_descrs = interface_ipsec_vti_list_all();"
            "foreach ($ipsec_descrs as $ifname => $ifdescr) $portlist[$ifname] = array('descr' => $ifdescr);"
            ""
            "echo json_encode(array_keys($portlist), JSON_PRETTY_PRINT);")

    def _get_media_mode(self, interface):
        """ Find all possible media options for the interface """
        return self.pfsense.php(
            '$mediaopts_list = array();\n'
            'exec("/sbin/ifconfig -m ' + interface + ' | grep \'media \'", $mediaopts);\n'
            'foreach ($mediaopts as $mediaopt) {\n'
            '        preg_match("/media (.*)/", $mediaopt, $matches);\n'
            '        if (preg_match("/(.*) mediaopt (.*)/", $matches[1], $matches1)) {\n'
            '                // there is media + mediaopt like "media 1000baseT mediaopt full-duplex"\n'
            '                array_push($mediaopts_list, $matches1[1] . " " . $matches1[2]);\n'
            '        } else {\n'
            '                // there is only media like "media 1000baseT"\n'
            '                array_push($mediaopts_list, $matches[1]);\n'
            '        }\n'
            '}\n'
            'echo json_encode($mediaopts_list);')

    def _update(self):
        """ make the target pfsense reload aliases """
        return self.pfsense.phpshell('''require_once("filter.inc");
if (filter_configure() == 0) { clear_subsystem_dirty('interfaces'); }''')

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
            values += self.format_cli_field(self.obj, 'if', fname='port')
            values += self.format_cli_field(self.obj, 'enable', fvalue=self.fvalue_bool)
            values += self.format_cli_field(self.params, 'ipv4_type')
            values += self.format_cli_field(self.params, 'mac')
            values += self.format_cli_field(self.obj, 'mtu')
            values += self.format_cli_field(self.obj, 'mss')
            values += self.format_cli_field(self.obj, 'ipaddr', fname='ipv4_address')
            values += self.format_cli_field(self.obj, 'subnet', fname='ipv4_prefixlen')
            values += self.format_cli_field(self.obj, 'gateway', fname='ipv4_gateway')
            values += self.format_cli_field(self.obj, 'blockpriv', fvalue=self.fvalue_bool)
            values += self.format_cli_field(self.obj, 'blockbogons', fvalue=self.fvalue_bool)
            values += self.format_cli_field(self.params, 'speed_duplex', fname='speed_duplex')
        else:
            values += self.format_updated_cli_field(self.obj, before, 'descr', add_comma=(values), fname='interface')
            values += self.format_updated_cli_field(self.obj, before, 'if', add_comma=(values), fname='port')
            values += self.format_updated_cli_field(self.obj, before, 'enable', add_comma=(values), fvalue=self.fvalue_bool)
            values += self.format_updated_cli_field(self.obj, before, 'ipv4_type', add_comma=(values), log_none='True')
            values += self.format_updated_cli_field(self.obj, before, 'spoofmac', add_comma=(values), fname='mac')
            values += self.format_updated_cli_field(self.obj, before, 'mtu', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'mss', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'media', add_comma=(values), fname='speed_duplex')
            values += self.format_updated_cli_field(self.obj, before, 'ipaddr', add_comma=(values), fname='ipv4_address')
            values += self.format_updated_cli_field(self.obj, before, 'subnet', add_comma=(values), fname='ipv4_prefixlen')
            values += self.format_updated_cli_field(self.obj, before, 'gateway', add_comma=(values), fname='ipv4_gateway')
            values += self.format_updated_cli_field(self.obj, before, 'blockpriv', add_comma=(values), fvalue=self.fvalue_bool)
            values += self.format_updated_cli_field(self.obj, before, 'blockbogons', add_comma=(values), fvalue=self.fvalue_bool)
        return values

    def _log_update(self, before):
        """ generate pseudo-CLI command to update an interface """
        log = "update {0} '{1}'".format(self._get_module_name(True), before['descr'])
        values = self._log_fields(before)
        self.result['commands'].append(log + ' set ' + values)
