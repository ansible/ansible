# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.network.pfsense.module_base import PFSenseModuleBase
from string import hexdigits
from hashlib import md5
import sys

NAT_OUTBOUND_ARGUMENT_SPEC = dict(
    descr=dict(required=True, type='str'),
    state=dict(default='present', choices=['present', 'absent']),
    disabled=dict(default=False, required=False, type='bool'),
    nonat=dict(default=False, required=False, type='bool'),
    interface=dict(required=False, type='str'),
    ipprotocol=dict(required=False, default='inet46', choices=['inet', 'inet46', 'inet6']),
    protocol=dict(default='any', required=False, choices=["any", "tcp", "udp", "tcp/udp", "icmp", "esp", "ah", "gre", "ipv6", "igmp", "carp", "pfsync"]),
    source=dict(required=False, type='str'),
    destination=dict(required=False, type='str'),
    invert=dict(default=False, required=False, type='bool'),
    address=dict(required=False, type='str'),
    poolopts=dict(
        default='', required=False, choices=["", "round-robin", "round-robin sticky-address", "random", "random sticky-address", "source-hash", "bitmask"]
    ),
    source_hash_key=dict(default='', type='str'),
    staticnatport=dict(default=False, required=False, type='bool'),
    nosync=dict(default=False, required=False, type='bool'),
    after=dict(required=False, type='str'),
    before=dict(required=False, type='str'),
)

NAT_OUTBOUD_REQUIRED_IF = [
    ["state", "present", ["interface", "source", "destination"]]
]


class PFSenseNatOutboundModule(PFSenseModuleBase):
    """ module managing pfsense NAT rules """

    ##############################
    # init
    #
    def __init__(self, module, pfsense=None):
        super(PFSenseNatOutboundModule, self).__init__(module, pfsense)
        self.name = "pfsense_nat_outbound"
        self.obj = dict()

        self.after = None
        self.before = None
        self.position_changed = False

        nat_elt = self.pfsense.get_element('nat')
        if nat_elt is None:
            nat_elt = self.pfsense.new_element('nat')
            self.pfsense.root.append(nat_elt)

        self.root_elt = nat_elt.find('outbound')
        if self.root_elt is None:
            self.root_elt = self.pfsense.new_element('outbound')
            nat_elt.append(self.root_elt)

    ##############################
    # params processing
    #
    def _params_to_obj(self):
        """ return a dict from module params """

        obj = dict()
        obj['descr'] = self.params['descr']
        if self.params['state'] == 'present':
            obj['sourceport'] = ''
            obj['interface'] = self.pfsense.parse_interface(self.params['interface'])
            self._get_ansible_param(obj, 'ipprotocol')
            if obj['ipprotocol'] == 'inet46':
                del obj['ipprotocol']
            self._get_ansible_param(obj, 'protocol')
            if obj['protocol'] == 'any':
                del obj['protocol']
            self._get_ansible_param(obj, 'poolopts')
            self._get_ansible_param(obj, 'source_hash_key')
            self._get_ansible_param(obj, 'natport')
            self._get_ansible_param_bool(obj, 'disabled')
            self._get_ansible_param_bool(obj, 'nonat')
            self._get_ansible_param_bool(obj, 'invert')
            self._get_ansible_param_bool(obj, 'staticnatport')
            self._get_ansible_param_bool(obj, 'nosync')

            if 'after' in self.params and self.params['after'] is not None:
                self.after = self.params['after']

            if 'before' in self.params and self.params['before'] is not None:
                self.before = self.params['before']

            self._parse_address(obj, 'source', 'sourceport', True, 'network')
            self._parse_address(obj, 'destination', 'dstport', False, 'address')
            self._parse_translated_address(obj)

            if obj['source_hash_key'] != '' and not obj['source_hash_key'].startswith('0x'):
                if sys.version_info[0] >= 3:
                    obj['source_hash_key'] = '0x' + md5(obj['source_hash_key'].encode('utf-8')).hexdigest()
                else:
                    obj['source_hash_key'] = '0x' + md5(obj['source_hash_key']).hexdigest()

        return obj

    def _parse_address(self, obj, field, field_port, allow_self, target):
        """ validate param address field and returns it as a dict """
        if self.params.get(field) is None or self.params[field] == '':
            return

        param = self.params[field]
        addr = param.split(':')
        if len(addr) > 2:
            self.module.fail_json(msg='Cannot parse address %s' % (param))

        address = addr[0]

        ret = dict()
        ports = addr[1] if len(addr) > 1 else None
        if address == 'any':
            if field == 'source':
                ret[target] = 'any'
            else:
                ret['any'] = ''
        # rule with this firewall
        elif allow_self and address == '(self)':
            ret[target] = '(self)'
        elif self.pfsense.is_ip_address(address):
            ret[target] = address + '/32'
        elif self.pfsense.is_ip_network(address, False):
            (addr, bits) = self.pfsense.parse_ip_network(address, False, False)
            ret[target] = addr + '/' + str(bits)
        elif self.pfsense.find_alias(address, 'host') is not None or self.pfsense.find_alias(address, 'network') is not None:
            ret[target] = address
        else:
            self.module.fail_json(msg='Cannot parse address %s, not IP or alias' % (address))

        self._parse_ports(obj, ports, field_port, param)

        obj[field] = ret

    def _parse_ports(self, obj, ports, field_port, param):
        """ validate param address field and returns it as a dict """
        if ports is not None:
            ports = ports.split('-')
            if len(ports) > 2 or ports[0] is None or ports[0] == '' or len(ports) == 2 and (ports[1] is None or ports[1] == ''):
                self.module.fail_json(msg='Cannot parse address %s' % (param))

            if not self.pfsense.is_port_or_alias(ports[0]):
                self.module.fail_json(msg='Cannot parse port %s, not port number or alias' % (ports[0]))
            obj[field_port] = ports[0]

            if len(ports) > 1:
                if not self.pfsense.is_port_or_alias(ports[1]):
                    self.module.fail_json(msg='Cannot parse port %s, not port number or alias' % (ports[1]))
                obj[field_port] += ':' + ports[1]

    def _parse_translated_address(self, obj):
        """ validate param address field and returns it as a dict """
        obj['target'] = ''
        obj['targetip'] = ''
        obj['targetip_subnet'] = ''

        if self.params.get('address') is None or self.params['address'] == '':
            return

        param = self.params['address']
        addr = param.split(':')
        if len(addr) > 2:
            self.module.fail_json(msg='Cannot parse address %s' % (param))

        address = addr[0]

        ports = addr[1] if len(addr) > 1 else None
        if address is not None and address != '':
            if self.pfsense.is_virtual_ip(address):
                obj['target'] = address
            elif self.pfsense.find_alias(address, 'host') is not None or self.pfsense.find_alias(address, 'network') is not None:
                obj['target'] = address
                if obj['poolopts'] != '' and not obj['poolopts'].startswith('round-robin'):
                    self.module.fail_json(msg='Only Round Robin pool options may be chosen when selecting an alias.')
            elif self.pfsense.is_ip_address(address):
                obj['target'] = 'other-subnet'
                obj['targetip'] = address
                obj['targetip_subnet'] = '32'
            else:
                (addr, part) = self.pfsense.parse_ip_network(address, False, False)
                if addr is None:
                    self.module.fail_json(msg='Cannot parse address %s, not IP or alias' % (address))
                obj['target'] = 'other-subnet'
                obj['targetip'] = addr
                obj['targetip_subnet'] = str(part)

        self._parse_ports(obj, ports, 'natport', param)

    def _validate_params(self):
        """ do some extra checks on input parameters """

        if self.params.get('after') and self.params.get('before'):
            self.module.fail_json(msg='Cannot specify both after and before')
        elif self.params.get('after'):
            if self.params['after'] == self.params['descr']:
                self.module.fail_json(msg='Cannot specify the current rule in after')
        elif self.params.get('before'):
            if self.params['before'] == self.params['descr']:
                self.module.fail_json(msg='Cannot specify the current rule in before')

        if self.params['source_hash_key'].startswith('0x'):
            hash = self.params['source_hash_key'][2:]
            if len(hash) != 32 or not all(c in hexdigits for c in hash):
                self.module.fail_json(msg='Incorrect format for source-hash key, \"0x\" must be followed by exactly 32 hexadecimal characters.')

    ##############################
    # XML processing
    #
    def _copy_and_add_target(self):
        """ create the XML target_elt """
        self.pfsense.copy_dict_to_element(self.obj, self.target_elt)
        self._insert(self.target_elt)

    def _copy_and_update_target(self):
        """ update the XML target_elt """
        before = self.pfsense.element_to_dict(self.target_elt)
        changed = self.pfsense.copy_dict_to_element(self.obj, self.target_elt)
        if self._remove_deleted_params():
            changed = True

        if self._update_rule_position(self.target_elt):
            changed = True

        return (before, changed)

    def _create_target(self):
        """ create the XML target_elt """
        target_elt = self.pfsense.new_element('rule')
        return target_elt

    def _find_rule_by_descr(self, descr):
        """ find the XML target_elt """
        for idx, rule_elt in enumerate(self.root_elt):
            if rule_elt.tag != 'rule':
                continue

            if rule_elt.find('descr').text == descr:
                return (rule_elt, idx)
        return (None, None)

    def _find_target(self):
        """ find the XML target_elt """
        for rule_elt in self.root_elt:
            if rule_elt.tag != 'rule':
                continue

            if rule_elt.find('descr').text == self.obj['descr']:
                return rule_elt
        return None

    def _get_expected_rule_position(self):
        """ get expected rule position in interface/floating """
        if self.before == 'bottom':
            return len(self.root_elt)
        elif self.after == 'top':
            return 0
        elif self.after is not None:
            return self._get_rule_position(self.after) + 1
        elif self.before is not None:
            position = self._get_rule_position(self.before) - 1
            if position < 0:
                return 0
            return position
        else:
            position = self._get_rule_position(self.after, fail=False)
            if position is not None:
                return position
            return len(self.root_elt)
        return -1

    def _get_expected_rule_xml_index(self):
        """ get expected rule index in xml """
        if self.before == 'bottom':
            return len(self.root_elt)
        elif self.after == 'top':
            return 0
        elif self.after is not None:
            found, i = self._find_rule_by_descr(self.after)
            if found is not None:
                return i + 1
            else:
                self.module.fail_json(msg='Failed to insert after rule=%s' % (self.after))
        elif self.before is not None:
            found, i = self._find_rule_by_descr(self.before)
            if found is not None:
                return i
            else:
                self.module.fail_json(msg='Failed to insert before rule=%s' % (self.before))
        else:
            found, i = self._find_rule_by_descr(self.obj['descr'])
            if found is not None:
                return i
            return len(self.root_elt)
        return -1

    @staticmethod
    def _get_params_to_remove():
        """ returns the list of params to remove if they are not set """
        return ['disabled', 'nonat', 'invert', 'staticnatport', 'nosync', 'dstport', 'natport', 'ipprotocol', 'protocol']

    def _get_rule_position(self, descr=None, fail=True):
        """ get rule position in interface/floating """
        if descr is None:
            descr = self.obj['descr']

        (res, idx) = self._find_rule_by_descr(descr)
        if fail and res is None:
            self.module.fail_json(msg='Failed to find rule=%s' % (descr))
        return idx

    def _insert(self, rule_elt):
        """ insert rule into xml """
        rule_xml_idx = self._get_expected_rule_xml_index()
        self.root_elt.insert(rule_xml_idx, rule_elt)

    def _update_rule_position(self, rule_elt):
        """ move rule in xml if required """
        current_position = self._get_rule_position()
        expected_position = self._get_expected_rule_position()
        if current_position == expected_position:
            self.position_changed = False
            return False

        self.root_elt.remove(rule_elt)
        self._insert(rule_elt)
        self.position_changed = True
        return True

    ##############################
    # run
    #
    def _update(self):
        """ make the target pfsense reload """
        return self.pfsense.phpshell('''require_once("filter.inc");
if (filter_configure() == 0) { clear_subsystem_dirty('natconf'); clear_subsystem_dirty('filter'); }''')

    ##############################
    # Logging
    #
    def _get_obj_name(self):
        """ return obj's name """
        return "'" + self.obj['descr'] + "'"

    @staticmethod
    def fvalue_protocol(value):
        """ boolean value formatting function """
        if value is None or value == 'none':
            return 'any'

        return value

    @staticmethod
    def fvalue_ipprotocol(value):
        """ boolean value formatting function """
        if value is None or value == 'none':
            return 'inet46'

        return value

    def _log_fields(self, before=None):
        """ generate pseudo-CLI command fields parameters to create an obj """
        values = ''
        fafter = self._obj_to_log_fields(self.obj)
        if before is None:
            values += self.format_cli_field(self.params, 'disabled', fvalue=self.fvalue_bool, default=False)
            values += self.format_cli_field(self.params, 'nonat', fvalue=self.fvalue_bool, default=False)
            values += self.format_cli_field(self.params, 'interface')
            values += self.format_cli_field(self.params, 'ipprotocol', fvalue=self.fvalue_ipprotocol, default='inet46')
            values += self.format_cli_field(self.params, 'protocol', fvalue=self.fvalue_protocol, default='any')
            values += self.format_cli_field(self.params, 'source')
            values += self.format_cli_field(self.params, 'destination')
            values += self.format_cli_field(self.params, 'invert', fvalue=self.fvalue_bool, default=False)
            values += self.format_cli_field(fafter, 'address', default='')
            values += self.format_cli_field(self.params, 'poolopts', default='')
            values += self.format_cli_field(self.obj, 'source_hash_key', default='')
            values += self.format_cli_field(self.params, 'staticnatport', fvalue=self.fvalue_bool, default=False)
            values += self.format_cli_field(self.params, 'nosync', fvalue=self.fvalue_bool, default=False)
            values += self.format_cli_field(self.params, 'after')
            values += self.format_cli_field(self.params, 'before')
        else:
            fbefore = self._obj_to_log_fields(before)
            fafter['before'] = self.before
            fafter['after'] = self.after

            values += self.format_updated_cli_field(self.obj, before, 'disabled', fvalue=self.fvalue_bool, default=False, add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'nonat', fvalue=self.fvalue_bool, default=False, add_comma=(values))
            values += self.format_updated_cli_field(fafter, fbefore, 'interface', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'ipprotocol', fvalue=self.fvalue_ipprotocol, add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'protocol', fvalue=self.fvalue_protocol, add_comma=(values))
            values += self.format_updated_cli_field(fafter, fbefore, 'source', add_comma=(values))
            values += self.format_updated_cli_field(fafter, fbefore, 'destination', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'invert', fvalue=self.fvalue_bool, default=False, add_comma=(values))
            values += self.format_updated_cli_field(fafter, before, 'address', default='', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'poolopts', default='', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'source_hash_key', default='', add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'staticnatport', fvalue=self.fvalue_bool, default=False, add_comma=(values))
            values += self.format_updated_cli_field(self.obj, before, 'nosync', fvalue=self.fvalue_bool, default=False, add_comma=(values))
            if self.position_changed:
                values += self.format_updated_cli_field(fafter, {}, 'after', log_none=False, add_comma=(values))
                values += self.format_updated_cli_field(fafter, {}, 'before', log_none=False, add_comma=(values))

        return values

    @staticmethod
    def _obj_address_to_log_field(rule, addr, target, port):
        """ return formated address from dict """
        field = ''
        if addr in rule:
            if target in rule[addr]:
                field = rule[addr][target]
            elif addr == 'destination' and 'any' in rule[addr]:
                field = 'any'

        if port in rule and rule[port] is not None and rule[port] != '':
            field += ':'
            field += rule[port].replace(':', '-')

        return field

    def _obj_to_log_fields(self, rule):
        """ return formated source and destination from dict """
        res = {}
        res['source'] = self._obj_address_to_log_field(rule, 'source', 'network', 'sourceport')
        res['destination'] = self._obj_address_to_log_field(rule, 'destination', 'address', 'dstport')
        res['interface'] = self.pfsense.get_interface_display_name(rule['interface'])

        if rule['target'] == 'other-subnet':
            res['address'] = rule['targetip'] + '/' + rule['targetip_subnet']
        else:
            res['address'] = rule['target']
        if 'natport' in rule and rule['natport'] != '':
            res['address'] += ':'
            res['address'] += rule['natport'].replace(':', '-')
        return res
