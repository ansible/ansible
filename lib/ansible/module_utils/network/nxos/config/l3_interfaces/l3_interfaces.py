#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The nxos_l3_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re

from copy import deepcopy
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list, remove_empties
from ansible.module_utils.network.nxos.facts.facts import Facts
from ansible.module_utils.network.nxos.utils.utils import normalize_interface, search_obj_in_list
from ansible.module_utils.network.nxos.utils.utils import remove_rsvd_interfaces, get_interface_type


class L3_interfaces(ConfigBase):
    """
    The nxos_l3_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'l3_interfaces',
    ]

    exclude_params = [
    ]

    def __init__(self, module):
        super(L3_interfaces, self).__init__(module)

    def get_l3_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        l3_interfaces_facts = facts['ansible_network_resources'].get('l3_interfaces')
        if not l3_interfaces_facts:
            return []

        self.platform = self.get_platform_type()
        return remove_rsvd_interfaces(l3_interfaces_facts)

    def get_platform_type(self):
        default, _warnings = Facts(self._module).get_facts(legacy_facts_type=['default'])
        return default.get('ansible_net_platform', '')

    def edit_config(self, commands):
        return self._connection.edit_config(commands)

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()

        existing_l3_interfaces_facts = self.get_l3_interfaces_facts()
        commands.extend(self.set_config(existing_l3_interfaces_facts))
        if commands:
            if not self._module.check_mode:
                self.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        changed_l3_interfaces_facts = self.get_l3_interfaces_facts()

        result['before'] = existing_l3_interfaces_facts
        if result['changed']:
            result['after'] = changed_l3_interfaces_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_l3_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        config = self._module.params.get('config')
        want = []
        if config:
            for w in config:
                w.update({'name': normalize_interface(w['name'])})
                if get_interface_type(w['name']) == 'management':
                    self._module.fail_json(msg="The 'management' interface is not allowed to be managed by this module")
                want.append(remove_empties(w))
        have = deepcopy(existing_l3_interfaces_facts)
        self.init_check_existing(have)
        resp = self.set_state(want, have)
        return to_list(resp)

    def set_state(self, want, have):
        """ Select the appropriate function based on the state provided

        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        state = self._module.params['state']
        if state in ('overridden', 'merged', 'replaced') and not want:
            self._module.fail_json(msg='config is required for state {0}'.format(state))

        commands = list()
        if state == 'overridden':
            commands.extend(self._state_overridden(want, have))
        elif state == 'deleted':
            commands.extend(self._state_deleted(want, have))
        else:
            for w in want:
                if state == 'merged':
                    commands.extend(self._state_merged(w, have))
                elif state == 'replaced':
                    commands.extend(self._state_replaced(w, have))
        return commands

    def _state_replaced(self, want, have):
        """ The command generator when state is replaced
        Scope is limited to interface objects defined in the playbook.

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        cmds = []
        name = want['name']
        obj_in_have = search_obj_in_list(want['name'], have, 'name')

        have_v4 = obj_in_have.pop('ipv4', []) if obj_in_have else []
        have_v6 = obj_in_have.pop('ipv6', []) if obj_in_have else []

        # Process lists of dicts separately
        v4_cmds = self._v4_cmds(want.pop('ipv4', []), have_v4, state='replaced')
        v6_cmds = self._v6_cmds(want.pop('ipv6', []), have_v6, state='replaced')

        # Process remaining attrs
        if obj_in_have:
            # Find 'want' changes first
            diff = self.diff_of_dicts(want, obj_in_have)
            rmv = {'name': name}
            haves_not_in_want = set(obj_in_have.keys()) - set(want.keys()) - set(diff.keys())
            for i in haves_not_in_want:
                rmv[i] = obj_in_have[i]
            cmds.extend(self.generate_delete_commands(rmv))
        else:
            diff = want

        cmds.extend(self.add_commands(diff, name=name))
        cmds.extend(v4_cmds)
        cmds.extend(v6_cmds)
        self.cmd_order_fixup(cmds, name)
        return cmds

    def _state_overridden(self, want, have):
        """ The command generator when state is overridden
        Scope includes all interface objects on the device.

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        # overridden behavior is the same as replaced except for scope.
        cmds = []
        existing_vlans = []
        for i in have:
            obj_in_want = search_obj_in_list(i['name'], want, 'name')
            if obj_in_want:
                if i != obj_in_want:
                    v4_cmds = self._v4_cmds(obj_in_want.pop('ipv4', []), i.pop('ipv4', []), state='overridden')
                    replaced_cmds = self._state_replaced(obj_in_want, [i])
                    replaced_cmds.extend(v4_cmds)
                    self.cmd_order_fixup(replaced_cmds, obj_in_want['name'])
                    cmds.extend(replaced_cmds)
            else:
                deleted_cmds = self.generate_delete_commands(i)
                self.cmd_order_fixup(deleted_cmds, i['name'])
                cmds.extend(deleted_cmds)

        for i in want:
            if [item for item in have if i['name'] == item['name']]:
                continue
            cmds.extend(self.add_commands(i, name=i['name']))

        return cmds

    def _state_merged(self, w, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        return self.set_commands(w, have)

    def _v4_cmds(self, want, have, state=None):
        """Helper method for processing ipv4 changes.
        This is needed to handle primary/secondary address changes, which require a specific sequence when changing.
        """
        # The ip address cli does not allow removing primary addresses while
        # secondaries are present, but it does allow changing a primary to a
        # new address as long as the address is not a current secondary.
        # Be aware of scenarios where a secondary is taking over
        # the role of the primary, which must be changed in sequence.
        # In general, primaries/secondaries should change in this order:
        # Step 1. Remove secondaries that are being changed or removed
        # Step 2. Change the primary if needed
        # Step 3. Merge secondaries

        # Normalize inputs (add tag key if not present)
        for i in want:
            i['tag'] = i.get('tag')
        for i in have:
            i['tag'] = i.get('tag')

        merged = True if state == 'merged' else False
        replaced = True if state == 'replaced' else False
        overridden = True if state == 'overridden' else False

        # Create secondary and primary wants/haves
        sec_w = [i for i in want if i.get('secondary')]
        sec_h = [i for i in have if i.get('secondary')]
        pri_w = [i for i in want if not i.get('secondary')]
        pri_h = [i for i in have if not i.get('secondary')]
        pri_w = pri_w[0] if pri_w else {}
        pri_h = pri_h[0] if pri_h else {}
        cmds = []

        # Remove all addrs when no primary is specified in want (pri_w)
        if pri_h and not pri_w and (replaced or overridden):
            cmds.append('no ip address')
            return cmds

        # 1. Determine which secondaries are changing and remove them. Need a have/want
        # diff instead of want/have because a have sec addr may be changing to a pri.
        sec_to_rmv = []
        sec_diff = self.diff_list_of_dicts(sec_h, sec_w)
        for i in sec_diff:
            if overridden or [w for w in sec_w if w['address'] == i['address']]:
                sec_to_rmv.append(i['address'])

        # Check if new primary is currently a secondary
        if pri_w and [h for h in sec_h if h['address'] == pri_w['address']]:
            if not overridden:
                sec_to_rmv.append(pri_w['address'])

        # Remove the changing secondaries
        cmds.extend(['no ip address %s secondary' % i for i in sec_to_rmv])

        # 2. change primary
        if pri_w:
            diff = dict(set(pri_w.items()) - set(pri_h.items()))
            if diff:
                cmd = 'ip address %s' % diff['address']
                tag = diff.get('tag')
                cmd += ' tag %s' % tag if tag else ''
                cmds.append(cmd)

        # 3. process remaining secondaries last
        sec_w_to_chg = self.diff_list_of_dicts(sec_w, sec_h)
        for i in sec_w_to_chg:
            cmd = 'ip address %s secondary' % i['address']
            cmd += ' tag %s' % i['tag'] if i['tag'] else ''
            cmds.append(cmd)

        return cmds

    def _v6_cmds(self, want, have, state=''):
        """Helper method for processing ipv6 changes.
        This is needed to avoid unnecessary churn on the device when removing or changing multiple addresses.
        """
        # Normalize inputs (add tag key if not present)
        for i in want:
            i['tag'] = i.get('tag')
        for i in have:
            i['tag'] = i.get('tag')

        cmds = []
        # items to remove (items in 'have' only)
        if state == 'replaced':
            for i in self.diff_list_of_dicts(have, want):
                want_addr = [w for w in want if w['address'] == i['address']]
                if not want_addr:
                    cmds.append('no ipv6 address %s' % i['address'])
                elif i['tag'] and not want_addr[0]['tag']:
                    # Must remove entire cli when removing tag
                    cmds.append('no ipv6 address %s' % i['address'])

        # items to merge/add
        for i in self.diff_list_of_dicts(want, have):
            addr = i['address']
            tag = i['tag']
            if not tag and state == 'merged':
                # When want is IP-no-tag and have is IP+tag it will show up in diff,
                # but for merged nothing has changed, so ignore it for idempotence.
                have_addr = [h for h in have if h['address'] == addr]
                if have_addr and have_addr[0].get('tag'):
                    continue
            cmd = 'ipv6 address %s' % i['address']
            cmd += ' tag %s' % tag if tag else ''
            cmds.append(cmd)

        return cmds

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        if want:
            for w in want:
                obj_in_have = search_obj_in_list(w['name'], have, 'name')
                commands.extend(self.del_all_attribs(obj_in_have))
        else:
            if not have:
                return commands
            for h in have:
                commands.extend(self.del_all_attribs(h))
        return commands

    def del_all_attribs(self, obj):
        commands = []
        if not obj or len(obj.keys()) == 1:
            return commands
        commands = self.generate_delete_commands(obj)
        self.cmd_order_fixup(commands, obj['name'])
        return commands

    def generate_delete_commands(self, obj):
        """Generate CLI commands to remove non-default settings.
        obj: dict of attrs to remove
        """
        commands = []
        name = obj.get('name')
        if 'dot1q' in obj:
            commands.append('no encapsulation dot1q')
        if 'redirects' in obj:
            if not self.check_existing(name, 'has_secondary') or re.match('N[3567]', self.platform):
                # device auto-enables redirects when secondaries are removed;
                # auto-enable may fail on legacy platforms so always do explicit enable
                commands.append('ip redirects')
        if 'unreachables' in obj:
            commands.append('no ip unreachables')
        if 'ipv4' in obj:
            commands.append('no ip address')
        if 'ipv6' in obj:
            commands.append('no ipv6 address')
        return commands

    def init_check_existing(self, have):
        """Creates a class var dict for easier access to existing states
        """
        self.existing_facts = dict()
        have_copy = deepcopy(have)
        for intf in have_copy:
            name = intf['name']
            self.existing_facts[name] = intf
            # Check for presence of secondaries; used for ip redirects logic
            if [i for i in intf.get('ipv4', []) if i.get('secondary')]:
                self.existing_facts[name]['has_secondary'] = True

    def check_existing(self, name, query):
        """Helper method to lookup existing states on an interface.
        This is needed for attribute changes that have additional dependencies;
        e.g. 'ip redirects' may auto-enable when all secondary ip addrs are removed.
        """
        if name:
            have = self.existing_facts.get(name, {})
            if 'has_secondary' in query:
                return have.get('has_secondary', False)
            if 'redirects' in query:
                return have.get('redirects', True)
            if 'unreachables' in query:
                return have.get('unreachables', False)
        return None

    def diff_of_dicts(self, w, obj):
        diff = set(w.items()) - set(obj.items())
        diff = dict(diff)
        if diff and w['name'] == obj['name']:
            diff.update({'name': w['name']})
        return diff

    def diff_list_of_dicts(self, w, h):
        diff = []
        set_w = set(tuple(sorted(d.items())) for d in w) if w else set()
        set_h = set(tuple(sorted(d.items())) for d in h) if h else set()
        difference = set_w.difference(set_h)
        for element in difference:
            diff.append(dict((x, y) for x, y in element))
        return diff

    def add_commands(self, diff, name=''):
        commands = []
        if not diff:
            return commands
        if 'dot1q' in diff:
            commands.append('encapsulation dot1q ' + str(diff['dot1q']))
        if 'redirects' in diff:
            # Note: device will auto-disable redirects when secondaries are present
            if diff['redirects'] != self.check_existing(name, 'redirects'):
                no_cmd = 'no ' if diff['redirects'] is False else ''
                commands.append(no_cmd + 'ip redirects')
                self.cmd_order_fixup(commands, name)
        if 'unreachables' in diff:
            if diff['unreachables'] != self.check_existing(name, 'unreachables'):
                no_cmd = 'no ' if diff['unreachables'] is False else ''
                commands.append(no_cmd + 'ip unreachables')
        if 'ipv4' in diff:
            commands.extend(self.generate_afi_commands(diff['ipv4']))
        if 'ipv6' in diff:
            commands.extend(self.generate_afi_commands(diff['ipv6']))
        self.cmd_order_fixup(commands, name)

        return commands

    def generate_afi_commands(self, diff):
        cmds = []
        for i in diff:
            cmd = 'ipv6 address ' if re.search('::', i['address']) else 'ip address '
            cmd += i['address']
            if i.get('secondary'):
                cmd += ' secondary'
            if i.get('tag'):
                cmd += ' tag ' + str(i['tag'])
            cmds.append(cmd)
        return cmds

    def set_commands(self, w, have):
        commands = []
        name = w['name']
        obj_in_have = search_obj_in_list(name, have, 'name')
        if not obj_in_have:
            commands = self.add_commands(w, name=name)
        else:
            # lists of dicts must be processed separately from non-list attrs
            v4_cmds = self._v4_cmds(w.pop('ipv4', []), obj_in_have.pop('ipv4', []), state='merged')
            v6_cmds = self._v6_cmds(w.pop('ipv6', []), obj_in_have.pop('ipv6', []), state='merged')

            # diff remaining attrs
            diff = self.diff_of_dicts(w, obj_in_have)
            commands = self.add_commands(diff, name=name)
            commands.extend(v4_cmds)
            commands.extend(v6_cmds)

        self.cmd_order_fixup(commands, name)
        return commands

    def cmd_order_fixup(self, cmds, name):
        """Inserts 'interface <name>' config at the beginning of populated command list; reorders dependent commands that must process after others.
        """
        if cmds:
            if name and not [item for item in cmds if item.startswith('interface')]:
                cmds.insert(0, 'interface ' + name)

            redirects = [item for item in cmds if re.match('(no )*ip redirects', item)]
            if redirects:
                # redirects should occur after ipv4 commands, just move to end of list
                redirects = redirects.pop()
                cmds.remove(redirects)
                cmds.append(redirects)
