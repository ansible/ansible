#
# -*- coding: utf-8 -*-
# Copyright 2019 Cisco and/or its affiliates.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The nxos telemetry utility library
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re
from copy import deepcopy


def get_module_params_subsection(module_params, tms_config, resource_key=None):
    """
    Helper method to get a specific module_params subsection
    """
    mp = {}
    if tms_config == 'TMS_GLOBAL':
        relevant_keys = ['certificate',
                         'compression',
                         'source_interface',
                         'vrf']
        for key in relevant_keys:
            mp[key] = module_params[key]

    if tms_config == 'TMS_DESTGROUP':
        mp['destination_groups'] = []
        for destgrp in module_params['destination_groups']:
            if destgrp['id'] == resource_key:
                mp['destination_groups'].append(destgrp)

    if tms_config == 'TMS_SENSORGROUP':
        mp['sensor_groups'] = []
        for sensor in module_params['sensor_groups']:
            if sensor['id'] == resource_key:
                mp['sensor_groups'].append(sensor)

    if tms_config == 'TMS_SUBSCRIPTION':
        mp['subscriptions'] = []
        for sensor in module_params['subscriptions']:
            if sensor['id'] == resource_key:
                mp['subscriptions'].append(sensor)

    return mp


def valiate_input(playvals, type, module):
    """
    Helper method to validate playbook values for destination groups
    """
    if type == 'destination_groups':
        if not playvals.get('id'):
            msg = "Invalid playbook value: {0}.".format(playvals)
            msg += " Parameter <id> under <destination_groups> is required"
            module.fail_json(msg=msg)
        if playvals.get('destination') and not isinstance(playvals['destination'], dict):
            msg = "Invalid playbook value: {0}.".format(playvals)
            msg += " Parameter <destination> under <destination_groups> must be a dict"
            module.fail_json(msg=msg)
        if not playvals.get('destination') and len(playvals) > 1:
            msg = "Invalid playbook value: {0}.".format(playvals)
            msg += " Playbook entry contains unrecongnized parameters."
            msg += " Make sure <destination> keys under <destination_groups> are specified as follows:"
            msg += " destination: {ip: <ip>, port: <port>, protocol: <prot>, encoding: <enc>}}"
            module.fail_json(msg=msg)

    if type == 'sensor_groups':
        if not playvals.get('id'):
            msg = "Invalid playbook value: {0}.".format(playvals)
            msg += " Parameter <id> under <sensor_groups> is required"
            module.fail_json(msg=msg)
        if playvals.get('path') and 'name' not in playvals['path'].keys():
            msg = "Invalid playbook value: {0}.".format(playvals)
            msg += " Parameter <path> under <sensor_groups> requires <name> key"
            module.fail_json(msg=msg)


def get_instance_data(key, cr_key, cr, existing_key):
    """
    Helper method to get instance data used to populate list structure in config
    fact dictionary
    """
    data = {}
    if existing_key is None:
        instance = None
    else:
        instance = cr._ref[cr_key]['existing'][existing_key]

    patterns = {
        'destination_groups': r"destination-group (\d+)",
        'sensor_groups': r"sensor-group (\d+)",
        'subscriptions': r"subscription (\d+)",
    }
    if key in patterns.keys():
        m = re.search(patterns[key], cr._ref['_resource_key'])
        instance_key = m.group(1)
        data = {'id': instance_key, cr_key: instance}

    # Remove None values
    data = dict((k, v) for k, v in data.items() if v is not None)
    return data


def cr_key_lookup(key, mo):
    """
    Helper method to get instance key value for Managed Object (mo)
    """
    cr_keys = [key]
    if key == 'destination_groups' and mo == 'TMS_DESTGROUP':
        cr_keys = ['destination']
    elif key == 'sensor_groups' and mo == 'TMS_SENSORGROUP':
        cr_keys = ['data_source', 'path']
    elif key == 'subscriptions' and mo == 'TMS_SUBSCRIPTION':
        cr_keys = ['destination_group', 'sensor_group']

    return cr_keys


def normalize_data(cmd_ref):
    ''' Normalize playbook values and get_exisiting data '''

    playval = cmd_ref._ref.get('destination').get('playval')
    existing = cmd_ref._ref.get('destination').get('existing')

    dest_props = ['protocol', 'encoding']
    if playval:
        for prop in dest_props:
            for key in playval.keys():
                playval[key][prop] = playval[key][prop].lower()
    if existing:
        for key in existing.keys():
            for prop in dest_props:
                existing[key][prop] = existing[key][prop].lower()


def remove_duplicate_context(cmds):
    ''' Helper method to remove duplicate telemetry context commands '''
    if not cmds:
        return cmds
    feature_indices = [i for i, x in enumerate(cmds) if x == "feature telemetry"]
    telemetry_indices = [i for i, x in enumerate(cmds) if x == "telemetry"]
    if len(feature_indices) == 1 and len(telemetry_indices) == 1:
        return cmds
    if len(feature_indices) == 1 and not telemetry_indices:
        return cmds
    if len(telemetry_indices) == 1 and not feature_indices:
        return cmds
    if feature_indices and feature_indices[-1] > 1:
        cmds.pop(feature_indices[-1])
        return remove_duplicate_context(cmds)
    if telemetry_indices and telemetry_indices[-1] > 1:
        cmds.pop(telemetry_indices[-1])
        return remove_duplicate_context(cmds)


def get_setval_path(module_or_path_data):
    ''' Build setval for path parameter based on playbook inputs
        Full Command:
          - path {name} depth {depth} query-condition {query_condition} filter-condition {filter_condition}
        Required:
          - path {name}
        Optional:
          - depth {depth}
          - query-condition {query_condition},
          - filter-condition {filter_condition}
    '''
    if isinstance(module_or_path_data, dict):
        path = module_or_path_data
    else:
        path = module_or_path_data.params['config']['sensor_groups'][0].get('path')
    if path is None:
        return path

    setval = 'path {name}'
    if 'depth' in path.keys():
        if path.get('depth') != 'None':
            setval = setval + ' depth {depth}'
    if 'query_condition' in path.keys():
        if path.get('query_condition') != 'None':
            setval = setval + ' query-condition {query_condition}'
    if 'filter_condition' in path.keys():
        if path.get('filter_condition') != 'None':
            setval = setval + ' filter-condition {filter_condition}'

    return setval


def remove_duplicate_commands(commands_list):
    # Remove any duplicate commands.
    # pylint: disable=unnecessary-lambda
    return sorted(set(commands_list), key=lambda x: commands_list.index(x))


def massage_data(have_or_want):
    # Massage non global into a data structure that is indexed by id and
    # normalized for destination_groups, sensor_groups and subscriptions.
    data = deepcopy(have_or_want)
    massaged = {}
    massaged['destination_groups'] = {}
    massaged['sensor_groups'] = {}
    massaged['subscriptions'] = {}
    from pprint import pprint
    for subgroup in ['destination_groups', 'sensor_groups', 'subscriptions']:
        for item in data.get(subgroup, []):
            id = str(item.get('id'))
            if id not in massaged[subgroup].keys():
                massaged[subgroup][id] = []
            item.pop('id')
            if not item:
                item = None
            else:
                if item.get('destination'):
                    if item.get('destination').get('port'):
                        item['destination']['port'] = str(item['destination']['port'])
                    if item.get('destination').get('protocol'):
                        item['destination']['protocol'] = item['destination']['protocol'].lower()
                    if item.get('destination').get('encoding'):
                        item['destination']['encoding'] = item['destination']['encoding'].lower()
                if item.get('path'):
                    for key in ['filter_condition', 'query_condition', 'depth']:
                        if item.get('path').get(key) == 'None':
                            del item['path'][key]
                    if item.get('path').get('depth') is not None:
                        item['path']['depth'] = str(item['path']['depth'])
                if item.get('destination_group'):
                    item['destination_group'] = str(item['destination_group'])
                if item.get('sensor_group'):
                    if item.get('sensor_group').get('id'):
                        item['sensor_group']['id'] = str(item['sensor_group']['id'])
                    if item.get('sensor_group').get('sample_interval'):
                        item['sensor_group']['sample_interval'] = str(item['sensor_group']['sample_interval'])
                if item.get('destination_group') and item.get('sensor_group'):
                    item_copy = deepcopy(item)
                    del item_copy['sensor_group']
                    del item['destination_group']
                    massaged[subgroup][id].append(item_copy)
                    massaged[subgroup][id].append(item)
                    continue
                if item.get('path') and item.get('data_source'):
                    item_copy = deepcopy(item)
                    del item_copy['data_source']
                    del item['path']
                    massaged[subgroup][id].append(item_copy)
                    massaged[subgroup][id].append(item)
                    continue
            massaged[subgroup][id].append(item)
    return massaged
