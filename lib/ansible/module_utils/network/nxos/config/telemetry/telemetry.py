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

        import pdb ; pdb.set_trace()
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
        from pprint import pprint
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
        all_global_properties = ['certificate', 'compression', 'source_interface', 'vrf']
        dest_profile_properties = ['compression', 'source_interface', 'vrf']
        dest_profile_remote_commands = []
        for property in all_global_properties:
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

        # Process Telemetry Destination Group Want and Have Values
        # Possible states:
        # - want and have are (set) (equal: no action, not equal: replace with want)
        # - want (set) have (not set) (add want)
        # - want (not set) have (set) (delete have)
        # - want (not set) have (not set) (no action)
        global_ctx = ref['tms_destgroup']._ref['_template']['context']
        setval = ref['tms_destgroup']._ref['destination']['setval']
        if want.get('destination_groups') is None:
            if have.get('destination_groups') is not None:
                for dg in have.get('destination_groups'):
                    remove_context = ['{0} destination-group {1}'.format('no', dg['id'])]
                    delete['TMS_DESTGROUP'].extend(global_ctx)
                    if remove_context[0] not in delete['TMS_DESTGROUP']:
                        delete['TMS_DESTGROUP'].extend(remove_context)
        else:
            for want_dg in want.get('destination_groups'):
                want_dg['destination']['protocol'] = want_dg['destination']['protocol'].lower()
                want_dg['destination']['encoding'] = want_dg['destination']['encoding'].lower()
                if want_dg not in have.get('destination_groups'):
                    property_ctx = ['destination-group {0}'.format(want_dg['id'])]
                    cmd = [setval.format(**want_dg['destination'])]
                    add['TMS_DESTGROUP'].extend(global_ctx)
                    if property_ctx[0] not in add['TMS_DESTGROUP']:
                        add['TMS_DESTGROUP'].extend(property_ctx)
                    add['TMS_DESTGROUP'].extend(cmd)
            for have_dg in have.get('destination_groups'):
                if have_dg not in want.get('destination_groups'):
                    have_id_in_want_ids = False
                    for item in want.get('destination_groups'):
                        if have_dg['id'] == item['id']:
                            have_id_in_want_ids = True
                    property_ctx = ['destination-group {0}'.format(have_dg['id'])]
                    delete['TMS_DESTGROUP'].extend(global_ctx)
                    if have_id_in_want_ids:
                        cmd = ['no ' + setval.format(**have_dg['destination'])]
                        if property_ctx[0] not in delete['TMS_DESTGROUP']:
                            delete['TMS_DESTGROUP'].extend(property_ctx)
                        delete['TMS_DESTGROUP'].extend(cmd)
                    else:
                        remove_context = ['no ' + property_ctx[0]]
                        if remove_context[0] not in delete['TMS_DESTGROUP']:
                            delete['TMS_DESTGROUP'].extend(remove_context)

        add['TMS_DESTGROUP'] = remove_duplicate_context(add['TMS_DESTGROUP'])
        delete['TMS_DESTGROUP'] = remove_duplicate_context(delete['TMS_DESTGROUP'])

        # Process Telemetry Sensor Group Want and Have Values
        # Possible states:
        # - want and have are (set) (equal: no action, not equal: replace with want)
        # - want (set) have (not set) (add want)
        # - want (not set) have (set) (delete have)
        # - want (not set) have (not set) (no action)
        global_ctx = ref['tms_sensorgroup']._ref['_template']['context']
        setval = {}
        setval['data_source'] = ref['tms_sensorgroup']._ref['data_source']['setval']
        setval['path'] = ref['tms_sensorgroup']._ref['path']['setval']
        if want.get('sensor_groups') is None:
            if have.get('sensor_groups') is not None:
                for sg in have.get('sensor_groups'):
                    remove_context = ['{0} sensor-group {1}'.format('no', sg['id'])]
                    delete['TMS_SENSORGROUP'].extend(global_ctx)
                    if remove_context[0] not in delete['TMS_SENSORGROUP']:
                        delete['TMS_SENSORGROUP'].extend(remove_context)
        else:
            for want_sg in want.get('sensor_groups'):
                if want_sg not in have.get('sensor_groups'):
                    property_ctx = ['sensor-group {0}'.format(want_sg['id'])]
                    cmd = {}
                    if want_sg.get('data_source'):
                        cmd['data_source'] = [setval['data_source'].format(want_sg['data_source'])]
                    if want_sg.get('path'):
                        setval['path'] = get_setval_path(want_sg.get('path'))
                        cmd['path'] = [setval['path'].format(**want_sg['path'])]
                    add['TMS_SENSORGROUP'].extend(global_ctx)
                    if property_ctx[0] not in add['TMS_SENSORGROUP']:
                        add['TMS_SENSORGROUP'].extend(property_ctx)
                    if cmd.get('data_source'):
                        add['TMS_SENSORGROUP'].extend(cmd['data_source'])
                    if cmd.get('path'):
                        add['TMS_SENSORGROUP'].extend(cmd['path'])
            for have_sg in have.get('sensor_groups'):
                if have_sg not in want.get('sensor_groups'):
                    have_id_in_want_ids = False
                    for item in want.get('sensor_groups'):
                        if have_sg['id'] == item['id']:
                            have_id_in_want_ids = True
                    property_ctx = ['sensor-group {0}'.format(have_sg['id'])]
                    delete['TMS_SENSORGROUP'].extend(global_ctx)
                    if have_id_in_want_ids:
                        cmd = {}
                        if have_sg.get('data_source'):
                            cmd['data_source'] = ['no ' + setval['data_source'].format(have_sg['data_source'])]
                        if have_sg.get('path'):
                            setval['path'] = get_setval_path(have_sg.get('path'))
                            cmd['path'] = ['no ' + setval['path'].format(**have_sg['path'])]
                        if cmd:
                            if property_ctx[0] not in delete['TMS_SENSORGROUP']:
                                delete['TMS_SENSORGROUP'].extend(property_ctx)
                            if cmd.get('data_source'):
                                delete['TMS_SENSORGROUP'].extend(cmd['data_source'])
                            if cmd.get('path'):
                                delete['TMS_SENSORGROUP'].extend(cmd['path'])
                    else:
                        remove_context = ['no ' + property_ctx[0]]
                        if remove_context[0] not in delete['TMS_SENSORGROUP']:
                            delete['TMS_SENSORGROUP'].extend(remove_context)

        add['TMS_SENSORGROUP'] = remove_duplicate_context(add['TMS_SENSORGROUP'])
        delete['TMS_SENSORGROUP'] = remove_duplicate_context(delete['TMS_SENSORGROUP'])

        # Process Telemetry Subscription Want and Have Values
        # Possible states:
        # - want and have are (set) (equal: no action, not equal: replace with want)
        # - want (set) have (not set) (add want)
        # - want (not set) have (set) (delete have)
        # - want (not set) have (not set) (no action)
        global_ctx = ref['tms_subscription']._ref['_template']['context']
        setval = {}
        setval['destination_group'] = ref['tms_subscription']._ref['destination_group']['setval']
        setval['sensor_group'] = ref['tms_subscription']._ref['sensor_group']['setval']
        if want.get('subscriptions') is None:
            if have.get('subscriptions') is not None:
                for sub in have.get('subscriptions'):
                    remove_context = ['{0} subscription {1}'.format('no', sub['id'])]
                    delete['TMS_SUBSCRIPTION'].extend(global_ctx)
                    if remove_context[0] not in delete['TMS_SUBSCRIPTION']:
                        delete['TMS_SUBSCRIPTION'].extend(remove_context)
        else:
            for want_sub in want.get('subscriptions'):
                if want_sub not in have.get('subscriptions'):
                    property_ctx = ['subscription {0}'.format(want_sub['id'])]
                    cmd = {}
                    if want_sub.get('destination_group'):
                        cmd['destination_group'] = [setval['destination_group'].format(want_sub['destination_group'])]
                    if want_sub.get('sensor_group'):
                        cmd['sensor_group'] = [setval['sensor_group'].format(**want_sub['sensor_group'])]
                    add['TMS_SUBSCRIPTION'].extend(global_ctx)
                    if property_ctx[0] not in add['TMS_SUBSCRIPTION']:
                        add['TMS_SUBSCRIPTION'].extend(property_ctx)
                    if cmd.get('destination_group'):
                        add['TMS_SUBSCRIPTION'].extend(cmd['destination_group'])
                    if cmd.get('sensor_group'):
                        add['TMS_SUBSCRIPTION'].extend(cmd['sensor_group'])
            for have_sub in have.get('subscriptions'):
                if have_sub not in want.get('subscriptions'):
                    have_id_in_want_ids = False
                    for item in want.get('subscriptions'):
                        if have_sub['id'] == item['id']:
                            have_id_in_want_ids = True
                            if have_sub.get('destination_group') == item.get('destination_group'):
                                have_id_in_want_ids = False
                            if have_sub.get('sensor_group') == str(item.get('sensor_group')):
                                have_id_in_want_ids = False
                    property_ctx = ['subscription {0}'.format(have_sub['id'])]
                    delete['TMS_SUBSCRIPTION'].extend(global_ctx)
                    if have_id_in_want_ids:
                        cmd = {}
                        if have_sub.get('destination_group'):
                            cmd['destination_group'] = ['no ' + setval['destination_group'].format(have_sub['destination_group'])]
                        if have_sub.get('sensor_group'):
                            cmd['sensor_group'] = ['no ' + setval['sensor_group'].format(**have_sub['sensor_group'])]
                        if cmd:
                            if property_ctx[0] not in delete['TMS_SUBSCRIPTION']:
                                delete['TMS_SUBSCRIPTION'].extend(property_ctx)
                            if cmd.get('destination_group'):
                                delete['TMS_SUBSCRIPTION'].extend(cmd['destination_group'])
                            if cmd.get('sensor_group'):
                                delete['TMS_SUBSCRIPTION'].extend(cmd['sensor_group'])
                    else:
                        remove_context = ['no ' + property_ctx[0]]
                        if remove_context[0] not in delete['TMS_SUBSCRIPTION']:
                            delete['TMS_SUBSCRIPTION'].extend(remove_context)

        add['TMS_SUBSCRIPTION'] = remove_duplicate_context(add['TMS_SUBSCRIPTION'])
        delete['TMS_SUBSCRIPTION'] = remove_duplicate_context(delete['TMS_SUBSCRIPTION'])

        import pdb ; pdb.set_trace()
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
