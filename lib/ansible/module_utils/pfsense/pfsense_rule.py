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
    disabled=dict(default=False, required=False,),
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

        self.results = {}
        self.results['added'] = []
        self.results['deleted'] = []
        self.results['modified'] = []

    def _find_rule_by_descr(self, descr, interface):
        """ return rule descr on interface with rule index """
        found = None
        i = 0
        for rule in self.rules:
            descr_elt = rule.find('descr')
            interface_elt = rule.find('interface')
            if (descr_elt is not None and descr_elt.text == descr
                    and interface_elt is not None and interface_elt.text == interface):
                found = rule
                break
            i += 1
        return (found, i)

    def _insert(self, rule_elt, after=None, before='bottom'):
        """ insert rule into xml """
        interface = rule_elt.find('interface').text
        if after is None and before == 'bottom':
            self.rules.append(rule_elt)
        elif after == 'top':
            i = 0
            # Find the first rule for this interface
            for rule in self.rules:
                rule_interface_elt = rule.find('interface')
                if rule_interface_elt is not None and rule_interface_elt.text == interface:
                    break
                i += 1
            self.rules.insert(i, rule_elt)
        elif after is not None:
            found, i = self._find_rule_by_descr(after, interface)
            if found is not None:
                self.rules.insert(i + 1, rule_elt)
            else:
                self.module.fail_json(msg='Failed to insert after rule=%s interface=%s' % (after, interface))
        elif before is not None:
            found, i = self._find_rule_by_descr(before, interface)
            if found:
                self.rules.insert(i, rule_elt)
            else:
                self.module.fail_json(msg='Failed to insert before rule=%s interface=%s' % (before, interface))
        else:
            self.module.fail_json(msg='Failed to add rule')

    def _update(self):
        """ make the target pfsense reload rules """
        return self.pfsense.phpshell('''require_once("filter.inc");
if (filter_configure() == 0) { clear_subsystem_dirty('rules'); }''')

    def commit_changes(self):
        """ apply changes and exit module """
        stdout = ''
        stderr = ''
        if self.changed and not self.module.check_mode:
            self.pfsense.write_config(descr=self.change_descr)
            (rc, stdout, stderr) = self._update()
        self.module.exit_json(stdout=stdout, stderr=stderr, changed=self.changed)

    def parse_address(self, param):
        """ validate param address field and returns it as a dict """
        match = re.match('([^:]+):?([^:]+)?', param)
        address = match.group(1)
        port = match.group(2)

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
            ret['network'] = port
            return ret
        # rule with interface name (LAN, WAN...)
        elif self.pfsense.is_interface_name(address):
            interface = self.pfsense.get_interface_pfsense_by_name(address)
            ret['network'] = interface
        else:
            if not self.pfsense.is_ip_or_alias(address):
                self.module.fail_json(msg='Cannot parse address %s, not IP or alias' % (address))
            ret['address'] = address
        if port is not None:
            if not self.pfsense.is_port_or_alias(port):
                self.module.fail_json(msg='Cannot parse port %s, not port number or alias' % (port))
            ret['port'] = port
        return ret

    def parse_interface(self, interface):
        """ validate param interface field """
        if self.pfsense.is_interface_name(interface):
            interface = self.pfsense.get_interface_pfsense_by_name(interface)
            return interface
        elif self.pfsense.is_interface_pfsense(interface):
            return interface

        self.module.fail_json(msg='%s is not a valid interface' % (interface))
        return None

    @staticmethod
    def remove_deleted_rule_param(rule, rule_elt, param):
        """ Remove from rule a deleted rule param """
        changed = False
        if param not in rule:
            param_elt = rule_elt.find(param)
            if param_elt is not None:
                changed = True
                rule_elt.remove(param_elt)
        return changed

    def remove_deleted_rule_params(self, rule, rule_elt):
        """ Remove from rule a few deleted rule params """
        changed = False
        if self.remove_deleted_rule_param(rule, rule_elt, 'log'):
            changed = True
        if self.remove_deleted_rule_param(rule, rule_elt, 'floating'):
            changed = True
        if self.remove_deleted_rule_param(rule, rule_elt, 'direction'):
            changed = True
        if self.remove_deleted_rule_param(rule, rule_elt, 'protocol'):
            changed = True

        return changed

    def add(self, rule, after=None, before='bottom'):
        """ add or update rule """
        rule_elt, i = self._find_rule_by_descr(rule['descr'], rule['interface'])
        changed = False
        timestamp = '%d' % int(time.time())
        if rule_elt is None:
            changed = True
            rule['id'] = ''
            rule['tracker'] = timestamp
            rule['created'] = rule['updated'] = dict()
            rule['created']['time'] = rule['updated']['time'] = timestamp
            rule['created']['username'] = rule['updated']['username'] = self.pfsense.get_username()
            rule_elt = self.pfsense.new_element('rule')
            self.pfsense.copy_dict_to_element(rule, rule_elt)
            self._insert(rule_elt, after, before)
            self.results['added'].append(rule)
            self.change_descr = 'ansible pfsense_rule added %s' % (rule['descr'])
        else:
            changed = self.pfsense.copy_dict_to_element(rule, rule_elt)
            if self.remove_deleted_rule_params(rule, rule_elt):
                changed = True

            # changing the rule order if required
            if after is not None:
                found, k = self._find_rule_by_descr(after, rule['interface'])
                if found:
                    if k + 1 != i:
                        self.rules.remove(rule_elt)
                        found, k = self._find_rule_by_descr(after, rule['interface'])
                        self.rules.insert(k + 1, rule_elt)
                        changed = True
                else:
                    self.module.fail_json(msg='Failed to insert after rule=%s interface=%s' % (after, rule['interface']))

            if changed:
                rule_elt.find('updated').find('time').text = timestamp
                rule_elt.find('updated').find('username').text = self.pfsense.get_username()
                self.results['modified'].append(self.pfsense.element_to_dict(rule_elt))
                self.change_descr = 'ansible pfsense_rule updated "%s" interface %s action %s' % (rule['descr'], rule['interface'], rule['type'])

        if changed:
            self.changed = True

    def remove_rule_elt(self, rule_elt):
        """ delete rule_elt from xml """
        self.rules.remove(rule_elt)
        self.changed = True
        self.results['deleted'].append(self.pfsense.element_to_dict(rule_elt))

    def remove(self, rule):
        """ delete rule """
        rule_elt, i = self._find_rule_by_descr(rule['descr'], rule['interface'])
        if rule_elt is not None:
            self.remove_rule_elt(rule_elt)
            self.change_descr = 'ansible pfsense_rule removed "%s" interface %s' % (rule['descr'], rule['interface'])

    def params_to_rule(self, params):
        """ return a rule dict from module params """
        rule = dict()
        rule['descr'] = params['name']
        rule['type'] = params['action']
        rule['interface'] = self.parse_interface(params['interface'])
        if params['floating'] == 'yes':
            rule['floating'] = params['floating']
        if params['direction'] is not None:
            rule['direction'] = params['direction']
        rule['ipprotocol'] = params['ipprotocol']
        if params['protocol'] != 'any':
            rule['protocol'] = params['protocol']
        rule['source'] = dict()
        rule['source'] = self.parse_address(params['source'])
        rule['destination'] = self.parse_address(params['destination'])
        if params['log'] == 'yes':
            rule['log'] = ''
        rule['statetype'] = params['statetype']

        return rule

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
                self.add(rule, after=params['after'])
            elif params['before']:
                self.add(rule, before=params['before'])
            else:
                self.add(rule)
