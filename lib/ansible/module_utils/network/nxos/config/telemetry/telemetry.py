#
# -*- coding: utf-8 -*-
# Copyright 2019 Cisco and/or its affiliates.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The nxos_telemetry class
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
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.nxos.facts.facts import Facts
from ansible.module_utils.network.nxos.cmdref.telemetry.telemetry import TMS_GLOBAL, TMS_DESTGROUP, TMS_SENSORGROUP, TMS_SUBSCRIPTION
from ansible.module_utils.network.nxos.utils.telemetry.telemetry import normalize_data, remove_duplicate_context
from ansible.module_utils.network.nxos.utils.telemetry.telemetry import valiate_input, get_setval_path
from ansible.module_utils.network.nxos.utils.telemetry.telemetry import get_module_params_subsection
from ansible.module_utils.network.nxos.utils.utils import normalize_interface
from ansible.module_utils.network.nxos.nxos import NxosCmdRef


class Telemetry(ConfigBase):
    """
    The nxos_telemetry class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'telemetry',
    ]

    def __init__(self, module):
        super(Telemetry, self).__init__(module)

    def get_telemetry_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        telemetry_facts = facts['ansible_network_resources'].get('telemetry')
        if not telemetry_facts:
            return {}
        return telemetry_facts

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

        state = self._module.params['state']
        if 'overridden' in state:
            self._module.fail_json(msg='State <overridden> is invalid for this module.')

        # When state is 'deleted', the module_params should not contain data
        # under the 'config' key
        if 'deleted' in state and self._module.params.get('config'):
            self._module.fail_json(msg='Remove config key from playbook when state is <deleted>')

        if self._module.params['config'] is None:
            self._module.params['config'] = {}
        # Normalize interface name.
        int = self._module.params['config'].get('source_interface')
        if int:
            self._module.params['config']['source_interface'] = normalize_interface(int)

        existing_telemetry_facts = self.get_telemetry_facts()
        commands.extend(self.set_config(existing_telemetry_facts))
        if commands:
            if not self._module.check_mode:
                self.edit_config(commands)
                # TODO: edit_config is only available for network_cli. Once we
                # add support for httpapi, we will need to switch to load_config
                # or add support to httpapi for edit_config
                #
                # self._connection.load_config(commands)
            result['changed'] = True
        result['commands'] = commands

        changed_telemetry_facts = self.get_telemetry_facts()

        result['before'] = existing_telemetry_facts
        if result['changed']:
            result['after'] = changed_telemetry_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_tms_global_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        config = self._module.params['config']
        want = dict((k, v) for k, v in config.items() if v is not None)
        have = existing_tms_global_facts
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

        # The deleted case is very simple since we purge all telemetry config
        # and does not require any processing using NxosCmdRef objects.
        if state == 'deleted':
            return self._state_deleted(want, have)

        # Save off module params
        ALL_MP = self._module.params['config']

        cmd_ref = {}
        cmd_ref['TMS_GLOBAL'] = {}
        cmd_ref['TMS_DESTGROUP'] = {}
        cmd_ref['TMS_SENSORGROUP'] = {}
        cmd_ref['TMS_SUBSCRIPTION'] = {}

        # Build Telemetry Global NxosCmdRef Object
        cmd_ref['TMS_GLOBAL']['ref'] = []
        self._module.params['config'] = get_module_params_subsection(ALL_MP, 'TMS_GLOBAL')
        cmd_ref['TMS_GLOBAL']['ref'].append(NxosCmdRef(self._module, TMS_GLOBAL))
        ref = cmd_ref['TMS_GLOBAL']['ref'][0]
        ref.set_context()
        ref.get_existing()
        ref.get_playvals()
        device_cache = ref.cache_existing

        if device_cache is None:
            device_cache_lines = []
        else:
            device_cache_lines = device_cache.split("\n")

        def build_cmdref_objects(td):
            cmd_ref[td['type']]['ref'] = []
            saved_ids = []
            if want.get(td['name']):
                for playvals in want[td['name']]:
                    valiate_input(playvals, td['name'], self._module)
                    if playvals['id'] in saved_ids:
                        continue
                    saved_ids.append(playvals['id'])
                    resource_key = td['cmd'].format(playvals['id'])
                    # Only build the NxosCmdRef object for the td['name'] module parameters.
                    self._module.params['config'] = get_module_params_subsection(ALL_MP, td['type'], playvals['id'])
                    cmd_ref[td['type']]['ref'].append(NxosCmdRef(self._module, td['obj']))
                    ref = cmd_ref[td['type']]['ref'][-1]
                    ref.set_context([resource_key])
                    if td['type'] == 'TMS_SENSORGROUP' and get_setval_path(self._module):
                        # Sensor group path setting can contain optional values.
                        # Call get_setval_path helper function to process any
                        # optional setval keys.
                        ref._ref['path']['setval'] = get_setval_path(self._module)
                    ref.get_existing(device_cache)
                    ref.get_playvals()
                    if td['type'] == 'TMS_DESTGROUP':
                        normalize_data(ref)

            if state == 'replaced':
                # For state replaced we need to build NxosCmdRef objects for state on
                # the device that is not specified in the playbook so that it can be
                # removed.
                re_pattern = r'{0}'.format(td['cmd'].split(' ')[0])
                for line in device_cache_lines:
                    if re.search(re_pattern, line):
                        resource_key = line.strip()
                        skip_resource_key = False
                        # Skip id if it is being managed by the playbook.
                        for id in saved_ids:
                            re_pattern = r'{0}$'.format(id)
                            if re.search(re_pattern, resource_key):
                                skip_resource_key = True
                                break
                        if skip_resource_key:
                            continue
                        cmd_ref[td['type']]['ref'].append(NxosCmdRef(self._module, td['obj']))
                        ref = cmd_ref[td['type']]['ref'][-1]
                        ref.set_context([resource_key])
                        ref.get_existing(device_cache)
                        if td['type'] == 'TMS_DESTGROUP':
                            normalize_data(ref)

        # Build Telemetry Destination Group NxosCmdRef Objects
        td = {'name': 'destination_groups', 'type': 'TMS_DESTGROUP',
              'obj': TMS_DESTGROUP, 'cmd': 'destination-group {0}'}
        build_cmdref_objects(td)

        # Build Telemetry Sensor Group NxosCmdRef Objects
        td = {'name': 'sensor_groups', 'type': 'TMS_SENSORGROUP',
              'obj': TMS_SENSORGROUP, 'cmd': 'sensor-group {0}'}
        build_cmdref_objects(td)

        # Build Telemetry Subscription NxosCmdRef Objects
        td = {'name': 'subscriptions', 'type': 'TMS_SUBSCRIPTION',
              'obj': TMS_SUBSCRIPTION, 'cmd': 'subscription {0}'}
        build_cmdref_objects(td)

        if state == 'merged':
            if want == have:
                return []
            commands = self._state_merged(cmd_ref)
        elif state == 'replaced':
            if want == have:
                return []
            commands = self._state_replaced(cmd_ref)
        return commands

    @staticmethod
    def _state_replaced(cmd_ref):
        """ The command generator when state is replaced
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        save_context = ['telemetry']
        commands = cmd_ref['TMS_GLOBAL']['ref'][0].get_proposed(save_context)

        # Order matters for state replaced.
        # First remove all subscriptions, followed by sensor-groups and destination-groups.
        # Second add all destination-groups, followed by sensor-groups and subscriptions
        add = {'TMS_DESTGROUP': [], 'TMS_SENSORGROUP': [], 'TMS_SUBSCRIPTION': []}
        delete = {'TMS_DESTGROUP': [], 'TMS_SENSORGROUP': [], 'TMS_SUBSCRIPTION': []}

        def remove_command(cmd_list):
            remove = False
            for cmd in cmd_list:
                if re.search(r'^no', cmd):
                    remove = True
                    break
            return remove

        if cmd_ref['TMS_DESTGROUP'].get('ref'):
            for cr in cmd_ref['TMS_DESTGROUP']['ref']:
                ref_cmd_list = cr.get_proposed(save_context)
                if remove_command(ref_cmd_list):
                    delete['TMS_DESTGROUP'].extend(ref_cmd_list)
                else:
                    add['TMS_DESTGROUP'].extend(ref_cmd_list)

        if cmd_ref['TMS_SENSORGROUP'].get('ref'):
            for cr in cmd_ref['TMS_SENSORGROUP']['ref']:
                ref_cmd_list = cr.get_proposed(save_context)
                if remove_command(ref_cmd_list):
                    delete['TMS_SENSORGROUP'].extend(ref_cmd_list)
                else:
                    add['TMS_SENSORGROUP'].extend(ref_cmd_list)

        if cmd_ref['TMS_SUBSCRIPTION'].get('ref'):
            for cr in cmd_ref['TMS_SUBSCRIPTION']['ref']:
                ref_cmd_list = cr.get_proposed(save_context)
                if remove_command(ref_cmd_list):
                    delete['TMS_SUBSCRIPTION'].extend(ref_cmd_list)
                else:
                    add['TMS_SUBSCRIPTION'].extend(ref_cmd_list)

        commands.extend(delete['TMS_SUBSCRIPTION'])
        commands.extend(delete['TMS_SENSORGROUP'])
        commands.extend(delete['TMS_DESTGROUP'])
        commands.extend(add['TMS_DESTGROUP'])
        commands.extend(add['TMS_SENSORGROUP'])
        commands.extend(add['TMS_SUBSCRIPTION'])
        return remove_duplicate_context(commands)

    @staticmethod
    def _state_merged(cmd_ref):
        """ The command generator when state is merged
        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = cmd_ref['TMS_GLOBAL']['ref'][0].get_proposed()

        if cmd_ref['TMS_DESTGROUP'].get('ref'):
            for cr in cmd_ref['TMS_DESTGROUP']['ref']:
                commands.extend(cr.get_proposed())

        if cmd_ref['TMS_SENSORGROUP'].get('ref'):
            for cr in cmd_ref['TMS_SENSORGROUP']['ref']:
                commands.extend(cr.get_proposed())

        if cmd_ref['TMS_SUBSCRIPTION'].get('ref'):
            for cr in cmd_ref['TMS_SUBSCRIPTION']['ref']:
                commands.extend(cr.get_proposed())

        return remove_duplicate_context(commands)

    @staticmethod
    def _state_deleted(want, have):
        """ The command generator when state is deleted
        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        if want != have:
            commands = ['no telemetry']
        return commands
