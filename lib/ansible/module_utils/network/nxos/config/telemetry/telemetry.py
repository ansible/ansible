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
from ansible.module_utils.network.nxos.utils.telemetry.telemetry import valiate_input, get_setval_path, massage_data
from ansible.module_utils.network.nxos.utils.telemetry.telemetry import get_module_params_subsection, remove_duplicate_commands
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
        elif state == 'replaced':
            if want == have:
                return []
            return self._state_replaced(want, have)

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
        return commands

    @staticmethod
    def _state_replaced(want, have):
        """ The command generator when state is replaced
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        massaged_have = massage_data(have)
        massaged_want = massage_data(want)

        ref = {}
        ref['tms_global'] = NxosCmdRef([], TMS_GLOBAL, ref_only=True)
        ref['tms_destgroup'] = NxosCmdRef([], TMS_DESTGROUP, ref_only=True)
        ref['tms_sensorgroup'] = NxosCmdRef([], TMS_SENSORGROUP, ref_only=True)
        ref['tms_subscription'] = NxosCmdRef([], TMS_SUBSCRIPTION, ref_only=True)

        # Order matters for state replaced.
        # First remove all subscriptions, followed by sensor-groups and destination-groups.
        # Second add all destination-groups, followed by sensor-groups and subscriptions
        add = {'TMS_GLOBAL': [], 'TMS_DESTGROUP': [], 'TMS_SENSORGROUP': [], 'TMS_SUBSCRIPTION': []}
        delete = {'TMS_DESTGROUP': [], 'TMS_SENSORGROUP': [], 'TMS_SUBSCRIPTION': []}

        # Process Telemetry Global Want and Have Values
        # Possible states:
        # - want and have are (set) (equal: no action, not equal: replace with want)
        # - want (set) have (not set) (add want)
        # - want (not set) have (set) (delete have)
        # - want (not set) have (not set) (no action)
        # global_ctx = ref['tms_global']._ref['_template']['context']
        # property_ctx = ref['tms_global']._ref['certificate'].get('context')
        # setval = ref['tms_global']._ref['certificate']['setval']
        #
        all_global_properties = ['certificate', 'compression', 'source_interface', 'vrf']
        dest_profile_properties = ['compression', 'source_interface', 'vrf']
        dest_profile_remote_commands = []
        for property in all_global_properties:
            cmd = None
            global_ctx = ref['tms_global']._ref['_template']['context']
            property_ctx = ref['tms_global']._ref[property].get('context')
            setval = ref['tms_global']._ref[property]['setval']
            kind = ref['tms_global']._ref[property]['kind']
            if want.get(property) is not None:
                if have.get(property) is not None:
                    if want.get(property) != have.get(property):
                        if kind == 'dict':
                            cmd = [setval.format(**want.get(property))]
                        else:
                            cmd = [setval.format(want.get(property))]
                elif have.get(property) is None:
                    if kind == 'dict':
                        cmd = [setval.format(**want.get(property))]
                    else:
                        cmd = [setval.format(want.get(property))]
            elif want.get(property) is None:
                if have.get(property) is not None:
                    if kind == 'dict':
                        cmd = ['no ' + setval.format(**have.get(property))]
                    else:
                        cmd = ['no ' + setval.format(have.get(property))]
                    if property in dest_profile_properties:
                        dest_profile_remote_commands.extend(cmd)

            if cmd is not None:
                ctx = global_ctx
                if property_ctx is not None:
                    ctx.extend(property_ctx)
                add['TMS_GLOBAL'].extend(ctx)
                add['TMS_GLOBAL'].extend(cmd)

        add['TMS_GLOBAL'] = remove_duplicate_commands(add['TMS_GLOBAL'])
        # If all destination profile commands are being removed then just
        # remove the config context instead.
        if len(dest_profile_remote_commands) == 3:
            for item in dest_profile_remote_commands:
                add['TMS_GLOBAL'].remove(item)
            add['TMS_GLOBAL'].remove('destination-profile')
            add['TMS_GLOBAL'].extend(['no destination-profile'])

        # Process Telemetry destination_group, sensor_group and subscription Want and Have Values
        # Possible states:
        # - want (not set) have (set) (delete have)
        # - want and have are (set) (equal: no action, not equal: replace with want)
        # - want (set) have (not set) (add want)
        # - want (not set) have (not set) (no action)
        tms_resources = ['TMS_DESTGROUP', 'TMS_SENSORGROUP', 'TMS_SUBSCRIPTION']
        for resource in tms_resources:
            if resource == 'TMS_DESTGROUP':
                name = 'destination-group'
                cmd_property = 'destination'
                global_ctx = ref['tms_destgroup']._ref['_template']['context']
                setval = ref['tms_destgroup']._ref['destination']['setval']
                want_resources = massaged_want.get('destination_groups')
                have_resources = massaged_have.get('destination_groups')
            if resource == 'TMS_SENSORGROUP':
                name = 'sensor-group'
                global_ctx = ref['tms_sensorgroup']._ref['_template']['context']
                setval = {}
                setval['data_source'] = ref['tms_sensorgroup']._ref['data_source']['setval']
                setval['path'] = ref['tms_sensorgroup']._ref['path']['setval']
                want_resources = massaged_want.get('sensor_groups')
                have_resources = massaged_have.get('sensor_groups')
            if resource == 'TMS_SUBSCRIPTION':
                name = 'subscription'
                global_ctx = ref['tms_subscription']._ref['_template']['context']
                setval = {}
                setval['destination_group'] = ref['tms_subscription']._ref['destination_group']['setval']
                setval['sensor_group'] = ref['tms_subscription']._ref['sensor_group']['setval']
                want_resources = massaged_want.get('subscriptions')
                have_resources = massaged_have.get('subscriptions')

            if not want_resources and have_resources:
                # want not and have not set so delete have
                for key in have_resources.keys():
                    remove_context = ['{0} {1} {2}'.format('no', name, key)]
                    delete[resource].extend(global_ctx)
                    if remove_context[0] not in delete[resource]:
                        delete[resource].extend(remove_context)
            else:
                # want and have are set.
                # process wants:
                for want_key in want_resources.keys():
                    if want_key not in have_resources.keys():
                        # Want resource key not in have resource key so add it
                        property_ctx = ['{0} {1}'.format(name, want_key)]
                        for item in want_resources[want_key]:
                            if resource == 'TMS_DESTGROUP':
                                cmd = [setval.format(**item[cmd_property])]
                                add[resource].extend(global_ctx)
                                if property_ctx[0] not in add[resource]:
                                    add[resource].extend(property_ctx)
                                add[resource].extend(cmd)
                            if resource == 'TMS_SENSORGROUP':
                                cmd = {}
                                if item.get('data_source'):
                                    cmd['data_source'] = [setval['data_source'].format(item['data_source'])]
                                if item.get('path'):
                                    setval['path'] = get_setval_path(item.get('path'))
                                    cmd['path'] = [setval['path'].format(**item['path'])]
                                add[resource].extend(global_ctx)
                                if property_ctx[0] not in add[resource]:
                                    add[resource].extend(property_ctx)
                                if cmd.get('data_source'):
                                    add[resource].extend(cmd['data_source'])
                                if cmd.get('path'):
                                    add[resource].extend(cmd['path'])
                            if resource == 'TMS_SUBSCRIPTION':
                                cmd = {}
                                if item.get('destination_group'):
                                    cmd['destination_group'] = [setval['destination_group'].format(item['destination_group'])]
                                if item.get('sensor_group'):
                                    cmd['sensor_group'] = [setval['sensor_group'].format(**item['sensor_group'])]
                                add[resource].extend(global_ctx)
                                if property_ctx[0] not in add[resource]:
                                    add[resource].extend(property_ctx)
                                if cmd.get('destination_group'):
                                    add[resource].extend(cmd['destination_group'])
                                if cmd.get('sensor_group'):
                                    add[resource].extend(cmd['sensor_group'])

                    elif want_key in have_resources.keys():
                        # Want resource key exists in have resource keys but we need to
                        # inspect the individual items under the resource key
                        # for differences
                        for item in want_resources[want_key]:
                            if item not in have_resources[want_key]:
                                if item is None:
                                    continue
                                # item wanted but does not exist so add it
                                property_ctx = ['{0} {1}'.format(name, want_key)]
                                if resource == 'TMS_DESTGROUP':
                                    cmd = [setval.format(**item[cmd_property])]
                                    add[resource].extend(global_ctx)
                                    if property_ctx[0] not in add[resource]:
                                        add[resource].extend(property_ctx)
                                    add[resource].extend(cmd)
                                if resource == 'TMS_SENSORGROUP':
                                    cmd = {}
                                    if item.get('data_source'):
                                        cmd['data_source'] = [setval['data_source'].format(item['data_source'])]
                                    if item.get('path'):
                                        setval['path'] = get_setval_path(item.get('path'))
                                        cmd['path'] = [setval['path'].format(**item['path'])]
                                    add[resource].extend(global_ctx)
                                    if property_ctx[0] not in add[resource]:
                                        add[resource].extend(property_ctx)
                                    if cmd.get('data_source'):
                                        add[resource].extend(cmd['data_source'])
                                    if cmd.get('path'):
                                        add[resource].extend(cmd['path'])
                                if resource == 'TMS_SUBSCRIPTION':
                                    cmd = {}
                                    if item.get('destination_group'):
                                        cmd['destination_group'] = [setval['destination_group'].format(item['destination_group'])]
                                    if item.get('sensor_group'):
                                        cmd['sensor_group'] = [setval['sensor_group'].format(**item['sensor_group'])]
                                    add[resource].extend(global_ctx)
                                    if property_ctx[0] not in add[resource]:
                                        add[resource].extend(property_ctx)
                                    if cmd.get('destination_group'):
                                        add[resource].extend(cmd['destination_group'])
                                    if cmd.get('sensor_group'):
                                        add[resource].extend(cmd['sensor_group'])

                # process haves:
                for have_key in have_resources.keys():
                    if have_key not in want_resources.keys():
                        # Want resource key is not in have resource keys so remove it
                        cmd = ['no ' + '{0} {1}'.format(name, have_key)]
                        delete[resource].extend(global_ctx)
                        delete[resource].extend(cmd)
                    elif have_key in want_resources.keys():
                        # Have resource key exists in want resource keys but we need to
                        # inspect the individual items under the resource key
                        # for differences
                        for item in have_resources[have_key]:
                            if item not in want_resources[have_key]:
                                if item is None:
                                    continue
                                # have item not wanted so remove it
                                property_ctx = ['{0} {1}'.format(name, have_key)]
                                if resource == 'TMS_DESTGROUP':
                                    cmd = ['no ' + setval.format(**item[cmd_property])]
                                    delete[resource].extend(global_ctx)
                                    if property_ctx[0] not in delete[resource]:
                                        delete[resource].extend(property_ctx)
                                    delete[resource].extend(cmd)
                                if resource == 'TMS_SENSORGROUP':
                                    cmd = {}
                                    if item.get('data_source'):
                                        cmd['data_source'] = ['no ' + setval['data_source'].format(item['data_source'])]
                                    if item.get('path'):
                                        setval['path'] = get_setval_path(item.get('path'))
                                        cmd['path'] = ['no ' + setval['path'].format(**item['path'])]
                                    delete[resource].extend(global_ctx)
                                    if property_ctx[0] not in delete[resource]:
                                        delete[resource].extend(property_ctx)
                                    if cmd.get('data_source'):
                                        delete[resource].extend(cmd['data_source'])
                                    if cmd.get('path'):
                                        delete[resource].extend(cmd['path'])
                                if resource == 'TMS_SUBSCRIPTION':
                                    cmd = {}
                                    if item.get('destination_group'):
                                        cmd['destination_group'] = ['no ' + setval['destination_group'].format(item['destination_group'])]
                                    if item.get('sensor_group'):
                                        cmd['sensor_group'] = ['no ' + setval['sensor_group'].format(**item['sensor_group'])]
                                    delete[resource].extend(global_ctx)
                                    if property_ctx[0] not in delete[resource]:
                                        delete[resource].extend(property_ctx)
                                    if cmd.get('destination_group'):
                                        delete[resource].extend(cmd['destination_group'])
                                    if cmd.get('sensor_group'):
                                        delete[resource].extend(cmd['sensor_group'])

            add[resource] = remove_duplicate_context(add[resource])
            delete[resource] = remove_duplicate_context(delete[resource])

        commands.extend(delete['TMS_SUBSCRIPTION'])
        commands.extend(delete['TMS_SENSORGROUP'])
        commands.extend(delete['TMS_DESTGROUP'])
        commands.extend(add['TMS_DESTGROUP'])
        commands.extend(add['TMS_SENSORGROUP'])
        commands.extend(add['TMS_SUBSCRIPTION'])
        commands.extend(add['TMS_GLOBAL'])
        commands = remove_duplicate_context(commands)

        return commands

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
