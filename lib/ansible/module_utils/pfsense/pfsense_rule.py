# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Orion Poplawski <orion@nwra.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import time
import re

from ansible.module_utils.pfsense.pfsense import PFSenseModule

RULES_ARGUMENT_SPEC = dict(
    name=dict(required=True, type='str'),
    action=dict(default='pass', required=False, choices=['pass', "block", 'reject']),
    state=dict(required=True, choices=['present', 'absent']),
    disabled=dict(default=False, required=False, type='bool'),
    interface=dict(required=True, type='str'),
    floating=dict(required=False, choices=["yes", "no"]),
    direction=dict(required=False, choices=["any", "in", "out"]),
    ipprotocol=dict(required=False, default='inet', choices=['inet', 'inet46', 'inet6']),
    protocol=dict(default='any', required=False, choices=["any", "tcp", "udp", "tcp/udp", "icmp"]),
    source=dict(required=True, type='str'),
    destination=dict(required=True, type='str'),
    log=dict(required=False, choices=["no", "yes"]),
    after=dict(required=False, type='str'),
    before=dict(required=False, type='str'),
    statetype=dict(required=False, default='keep state', type='str')
)

RULES_REQUIRED_IF = [["floating", "yes", ["direction"]]]


class PFSenseRuleModule(object):
    """ module managing pfsense rules """

    def __init__(self, module, pfsense=None):
        if pfsense is None:
            pfsense = PFSenseModule(module)
        self.module = module
        self.pfsense = pfsense
        self.rules = self.pfsense.get_element('filter')

        self.changed = False
        self.change_descr = ''

        self.diff = {'after': {}, 'before': {}}

        self.results = {}
        self.results['added'] = []
        self.results['deleted'] = []
        self.results['modified'] = []

        # internals params
        self._rule = None
        self._descr = None
        self._interface = None
        self._floating = None
        self._after = None
        self._before = None

    def _interface_name(self):
        """ return formated interface name for logging """
        if self._floating:
            return 'floating(' + self._interface + ')'
        return self._interface

    def _match_interface(self, rule_elt):
        """ check if a rule elt match the targeted interface
            floating rules must match the floating mode instead of the interface name
        """
        interface_elt = rule_elt.find('interface')
        floating_elt = rule_elt.find('floating')
        if floating_elt is not None and floating_elt.text == 'yes':
            return self._floating
        elif self._floating:
            return False
        return interface_elt is not None and interface_elt.text == self._interface

    def _find_rule_by_descr(self, descr):
        """ return rule descr on interface/floating with rule index """
        found = None
        i = 0
        for rule in self.rules:
            descr_elt = rule.find('descr')
            if self._match_interface(rule) and descr_elt is not None and descr_elt.text == descr:
                found = rule
                break
            i += 1
        return (found, i)

    def _adjust_separators(self, start_idx, add=True, before=False):
        """ update separators position """
        separators_elt = self.rules.find('separator')
        if separators_elt is None:
            return

        separators_elt = separators_elt.find(self._interface)
        if separators_elt is None:
            return

        for separator_elt in separators_elt:
            row_elt = separator_elt.find('row')
            if row_elt is None or row_elt.text is None:
                continue

            if_elt = separator_elt.find('if')
            if if_elt is None or if_elt.text != self._interface:
                continue

            match = re.match(r'fr(\d+)', row_elt.text)
            if match:
                idx = int(match.group(1))
                if add:
                    if before:
                        if idx > start_idx:
                            row_elt.text = 'fr' + str(idx + 1)
                    else:
                        if idx >= start_idx:
                            row_elt.text = 'fr' + str(idx + 1)
                elif idx > start_idx:
                    row_elt.text = 'fr' + str(idx - 1)

    def _get_first_rule_xml_index(self):
        """ Find the first rule for the interface/floating and return its xml index """
        i = 0
        for rule_elt in self.rules:
            if self._match_interface(rule_elt):
                break
            i += 1
        return i

    def _get_last_rule_xml_index(self):
        """ Find the last rule for the interface/floating and return its xml index """
        last_found = -1
        i = 0
        for rule_elt in self.rules:
            if self._match_interface(rule_elt):
                last_found = i
            i += 1
        return last_found

    def _get_rule_position(self, descr=None, fail=True):
        """ get rule position in interface/floating """
        if descr is None:
            descr = self._descr

        i = 0
        for rule_elt in self.rules:
            if not self._match_interface(rule_elt):
                continue
            descr_elt = rule_elt.find('descr')
            if descr_elt is not None and descr_elt.text == descr:
                return i
            i += 1

        if fail:
            self.module.fail_json(msg='Failed to find rule=%s interface=%s' % (descr, self._interface_name()))
        return None

    def _get_interface_rule_count(self):
        """ get rule count in interface/floating """
        count = 0
        for rule_elt in self.rules:
            if not self._match_interface(rule_elt):
                continue
            count += 1

        return count

    def _get_expected_rule_xml_index(self):
        """ get expected rule index in xml """
        if self._before == 'bottom':
            return self._get_last_rule_xml_index() + 1
        elif self._after == 'top':
            return self._get_first_rule_xml_index()
        elif self._after is not None:
            found, i = self._find_rule_by_descr(self._after)
            if found is not None:
                return i + 1
            else:
                self.module.fail_json(msg='Failed to insert after rule=%s interface=%s' % (self._after, self._interface_name()))
        elif self._before is not None:
            found, i = self._find_rule_by_descr(self._before)
            if found:
                return i
            else:
                self.module.fail_json(msg='Failed to insert before rule=%s interface=%s' % (self._before, self._interface_name()))
        else:
            found, i = self._find_rule_by_descr(self._descr)
            if found is not None:
                return i
            return self._get_last_rule_xml_index() + 1
        return -1

    def _get_expected_rule_position(self):
        """ get expected rule position in interface/floating """
        if self._before == 'bottom':
            return self._get_interface_rule_count() - 1
        elif self._after == 'top':
            return 0
        elif self._after is not None:
            return self._get_rule_position(self._after) + 1
        elif self._before is not None:
            position = self._get_rule_position(self._before) - 1
            if position < 0:
                return 0
            return position
        else:
            position = self._get_rule_position(self._after, fail=False)
            if position is not None:
                return position
            return self._get_interface_rule_count()
        return -1

    def _insert(self, rule_elt):
        """ insert rule into xml """
        rule_xml_idx = self._get_expected_rule_xml_index()
        self.rules.insert(rule_xml_idx, rule_elt)

        rule_position = self._get_rule_position()
        self._adjust_separators(rule_position, before=(self._after is None and self._before is not None))

    def _update_rule_position(self, rule_elt):
        """ move rule in xml if required """
        current_position = self._get_rule_position()
        expected_position = self._get_expected_rule_position()
        if current_position == expected_position:
            return False

        self.diff['before']['position'] = current_position
        self.diff['after']['position'] = expected_position
        self._adjust_separators(current_position, add=False)
        self.rules.remove(rule_elt)
        self._insert(rule_elt)
        return True

    def _update(self):
        """ make the target pfsense reload rules """
        return self.pfsense.phpshell('''require_once("filter.inc");
if (filter_configure() == 0) { clear_subsystem_dirty('rules'); }''')

    def _parse_address(self, param):
        """ validate param address field and returns it as a dict """
        match = re.match('^([^:]+)(?::?([^:-]+)-?([^:-]+)?)?$', param)
        if match is None:
            self.module.fail_json(msg='Cannot parse address %s' % (param))
        address = match.group(1)
        port_start = match.group(2)
        port_end = match.group(3)

        ret = dict()
        # Check if the first character is "!"
        if address[0] == '!':
            # Invert the rule
            ret['not'] = None
            address = address[1:]
        if address == 'any':
            ret['any'] = None
        # rule with this firewall
        elif address == '(self)':
            ret['network'] = '(self)'
        elif address == 'NET':
            ret['network'] = port_start
            # TODO: check if '-' is allowed into interfaces name
            # TODO: check interface name validity
            if port_end:
                ret['network'] += '-' + port_end
            return ret
        # rule with interface name (LAN, WAN...)
        elif self.pfsense.is_interface_name(address):
            interface = self.pfsense.get_interface_pfsense_by_name(address)
            ret['network'] = interface
        else:
            if not self.pfsense.is_ip_or_alias(address):
                self.module.fail_json(msg='Cannot parse address %s, not IP or alias' % (address))
            ret['address'] = address

        if port_start is not None:
            if not self.pfsense.is_port_or_alias(port_start):
                self.module.fail_json(msg='Cannot parse port %s, not port number or alias' % (port_start))
            ret['port'] = port_start
        if port_end is not None:
            if not self.pfsense.is_port_or_alias(port_end):
                self.module.fail_json(msg='Cannot parse port %s, not port number or alias' % (port_end))
            ret['port'] += '-' + port_end

        return ret

    def _parse_interface(self, interface):
        """ validate param interface field """
        if self.pfsense.is_interface_name(interface):
            interface = self.pfsense.get_interface_pfsense_by_name(interface)
            return interface
        elif self.pfsense.is_interface_pfsense(interface):
            return interface

        self.module.fail_json(msg='%s is not a valid interface' % (interface))
        return None

    def _remove_deleted_rule_param(self, rule_elt, param):
        """ Remove from rule a deleted rule param """
        changed = False
        if param not in self._rule:
            param_elt = rule_elt.find(param)
            if param_elt is not None:
                changed = True
                rule_elt.remove(param_elt)
        return changed

    def _remove_deleted_rule_params(self, rule_elt):
        """ Remove from rule a few deleted rule params """
        changed = False
        if self._remove_deleted_rule_param(rule_elt, 'log'):
            changed = True
        if self._remove_deleted_rule_param(rule_elt, 'floating'):
            changed = True
        if self._remove_deleted_rule_param(rule_elt, 'direction'):
            changed = True
        if self._remove_deleted_rule_param(rule_elt, 'protocol'):
            changed = True
        if self._remove_deleted_rule_param(rule_elt, 'disabled'):
            changed = True

        return changed

    def _remove_rule_elt(self, rule_elt):
        """ delete rule_elt from xml """
        self.rules.remove(rule_elt)
        self.changed = True
        self.diff['before'] = self.rule_element_to_dict(rule_elt)
        self.results['deleted'].append(self.rule_element_to_dict(rule_elt))

    def _set_internals(self, rule, after=None, before=None):
        """ set members (avoid passing those by params everywhere) """
        self._rule = rule
        self._descr = rule['descr']
        self._interface = rule['interface']
        self._floating = 'floating' in rule and rule['floating'] == 'yes'
        self._after = after
        self._before = before

    ##################
    # public methods
    #
    def rule_element_to_dict(self, rule_elt):
        """ convert rule_elt to dictionary like module arguments """
        rule = self.pfsense.element_to_dict(rule_elt)

        # We use 'name' for 'descr'
        rule['name'] = rule.pop('descr', 'UNKNOWN')

        # Convert addresses to argument format
        for addr_item in ['source', 'destination']:
            elt = rule_elt.find(addr_item)
            if elt is not None:
                rule[addr_item] = self.pfsense.addr_normalize(self.pfsense.element_to_dict(elt))
        # Convert nested elements to dicts
        for other_item in ['created', 'updated']:
            elt = rule_elt.find(other_item)
            if elt is not None:
                rule[other_item] = self.pfsense.element_to_dict(elt)
        rule['action'] = rule.pop('type', 'UNKNOWN')

        return rule

    def add(self, rule, after=None, before=None):
        """ add or update rule """
        self._set_internals(rule, after, before)
        rule_elt, i = self._find_rule_by_descr(self._descr)
        changed = False
        timestamp = '%d' % int(time.time())
        if rule_elt is None:
            changed = True
            self.diff['before'] = ''
            rule['id'] = ''
            rule['tracker'] = timestamp
            rule['created'] = rule['updated'] = dict()
            rule['created']['time'] = rule['updated']['time'] = timestamp
            rule['created']['username'] = rule['updated']['username'] = self.pfsense.get_username()
            rule_elt = self.pfsense.new_element('rule')
            self.diff['after'] = self.rule_element_to_dict(rule_elt)
            self.pfsense.copy_dict_to_element(rule, rule_elt)
            self._insert(rule_elt)
            self.results['added'].append(rule)
            self.change_descr = 'ansible pfsense_rule added %s' % (rule['descr'])
        else:
            self.diff['before'] = self.rule_element_to_dict(rule_elt)
            changed = self.pfsense.copy_dict_to_element(rule, rule_elt)
            if self._remove_deleted_rule_params(rule_elt):
                changed = True

            if self._update_rule_position(rule_elt):
                changed = True

            if changed:
                rule_elt.find('updated').find('time').text = timestamp
                rule_elt.find('updated').find('username').text = self.pfsense.get_username()
                self.diff['after'].update(self.rule_element_to_dict(rule_elt))
                self.results['modified'].append(self.rule_element_to_dict(rule_elt))
                self.change_descr = 'ansible pfsense_rule updated "%s" interface %s action %s' % (rule['descr'], rule['interface'], rule['type'])

        if changed:
            self.changed = True

    def remove(self, rule):
        """ delete rule """
        self._set_internals(rule)
        rule_elt, i = self._find_rule_by_descr(self._descr)
        if rule_elt is not None:
            self.diff['before'] = self.rule_element_to_dict(rule_elt)
            self._adjust_separators(self._get_rule_position(), add=False)
            self._remove_rule_elt(rule_elt)
            self.change_descr = 'ansible pfsense_rule removed "%s" interface %s' % (rule['descr'], rule['interface'])

    def params_to_rule(self, params):
        """ return a rule dict from module params """
        rule = dict()
        rule['descr'] = params['name']
        rule['type'] = params['action']
        rule['interface'] = self._parse_interface(params['interface'])
        if params['floating'] == 'yes':
            rule['floating'] = params['floating']
        if params['direction'] is not None:
            rule['direction'] = params['direction']
        rule['ipprotocol'] = params['ipprotocol']
        if params['protocol'] != 'any':
            rule['protocol'] = params['protocol']
        rule['source'] = dict()
        rule['source'] = self._parse_address(params['source'])
        rule['destination'] = self._parse_address(params['destination'])
        if params['log'] == 'yes':
            rule['log'] = ''
        if params['disabled']:
            rule['disabled'] = ''
        rule['statetype'] = params['statetype']

        return rule

    def commit_changes(self):
        """ apply changes and exit module """
        stdout = ''
        stderr = ''
        if self.changed and not self.module.check_mode:
            self.pfsense.write_config(descr=self.change_descr)
            (rc, stdout, stderr) = self._update()

        self.module.exit_json(stdout=stdout, stderr=stderr, changed=self.changed, diff=self.diff)

    def run(self, params):
        """ process input params to add/update/delete a rule """
        rule = self.params_to_rule(params)

        state = params['state']
        if state == 'absent':
            self.remove(rule)
        elif state == 'present':
            if params['after'] and params['before']:
                self.module.fail_json(msg='Cannot specify both after and before')
            elif params['after']:
                if params['after'] == rule['descr']:
                    self.module.fail_json(msg='Cannot specify the current rule in after')
                self.add(rule, after=params['after'])
            elif params['before']:
                if params['before'] == rule['descr']:
                    self.module.fail_json(msg='Cannot specify the current rule in before')
                self.add(rule, before=params['before'])
            else:
                self.add(rule)
