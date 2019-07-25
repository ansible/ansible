#
# -*- coding: utf-8 -*-
# Copyright 2019 Cisco and/or its affiliates.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The nxos telemetry fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re
from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.nxos.argspec.telemetry.telemetry import TelemetryArgs
from ansible.module_utils.network.nxos.cmdref.telemetry.telemetry import TMS_GLOBAL, TMS_DESTGROUP, TMS_SENSORGROUP, TMS_SUBSCRIPTION
from ansible.module_utils.network.nxos.utils.telemetry.telemetry import get_instance_data, cr_key_lookup
from ansible.module_utils.network.nxos.utils.telemetry.telemetry import normalize_data
from ansible.module_utils.network.nxos.nxos import NxosCmdRef, normalize_interface


class TelemetryFacts(object):
    """ The nxos telemetry fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = TelemetryArgs.argument_spec
        spec = deepcopy(self.argument_spec)
        if subspec:
            if options:
                facts_argument_spec = spec[subspec][options]
            else:
                facts_argument_spec = spec[subspec]
        else:
            facts_argument_spec = spec

        self.generated_spec = utils.generate_dict(facts_argument_spec)

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for telemetry
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if connection:  # just for linting purposes, remove
            pass

        cmd_ref = {}
        cmd_ref['TMS_GLOBAL'] = {}
        cmd_ref['TMS_DESTGROUP'] = {}
        cmd_ref['TMS_SENSORGROUP'] = {}
        cmd_ref['TMS_SUBSCRIPTION'] = {}

        # For fact gathering, module state should be 'present' when using
        # NxosCmdRef to query state
        if self._module.params.get('state'):
            saved_module_state = self._module.params['state']
            self._module.params['state'] = 'present'

        # Get Telemetry Global Data
        cmd_ref['TMS_GLOBAL']['ref'] = []
        cmd_ref['TMS_GLOBAL']['ref'].append(NxosCmdRef(self._module, TMS_GLOBAL))
        ref = cmd_ref['TMS_GLOBAL']['ref'][0]
        ref.set_context()
        ref.get_existing()
        device_cache = ref.cache_existing

        if device_cache is None:
            device_cache_lines = []
        else:
            device_cache_lines = device_cache.split("\n")

        # Get Telemetry Destination Group Data
        cmd_ref['TMS_DESTGROUP']['ref'] = []
        for line in device_cache_lines:
            if re.search(r'destination-group', line):
                resource_key = line.strip()
                cmd_ref['TMS_DESTGROUP']['ref'].append(NxosCmdRef(self._module, TMS_DESTGROUP))
                ref = cmd_ref['TMS_DESTGROUP']['ref'][-1]
                ref.set_context([resource_key])
                ref.get_existing(device_cache)
                normalize_data(ref)

        # Get Telemetry Sensorgroup Group Data
        cmd_ref['TMS_SENSORGROUP']['ref'] = []
        for line in device_cache_lines:
            if re.search(r'sensor-group', line):
                resource_key = line.strip()
                cmd_ref['TMS_SENSORGROUP']['ref'].append(NxosCmdRef(self._module, TMS_SENSORGROUP))
                ref = cmd_ref['TMS_SENSORGROUP']['ref'][-1]
                ref.set_context([resource_key])
                ref.get_existing(device_cache)

        # Get Telemetry Subscription Data
        cmd_ref['TMS_SUBSCRIPTION']['ref'] = []
        for line in device_cache_lines:
            if re.search(r'subscription', line):
                resource_key = line.strip()
                cmd_ref['TMS_SUBSCRIPTION']['ref'].append(NxosCmdRef(self._module, TMS_SUBSCRIPTION))
                ref = cmd_ref['TMS_SUBSCRIPTION']['ref'][-1]
                ref.set_context([resource_key])
                ref.get_existing(device_cache)

        objs = []
        objs = self.render_config(self.generated_spec, cmd_ref)
        facts = {'telemetry': {}}
        if objs:
            # params = utils.validate_config(self.argument_spec, {'config': objs})
            facts['telemetry'] = objs

        ansible_facts['ansible_network_resources'].update(facts)
        if self._module.params.get('state'):
            self._module.params['state'] = saved_module_state
        return ansible_facts

    def render_config(self, spec, cmd_ref):
        """
        Render config as dictionary structure and delete keys
          from spec for null values

        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        config = deepcopy(spec)
        config['destination_groups'] = []
        config['sensor_groups'] = []
        config['subscriptions'] = []
        managed_objects = ['TMS_GLOBAL', 'TMS_DESTGROUP', 'TMS_SENSORGROUP', 'TMS_SUBSCRIPTION']

        # Walk the argspec and cmd_ref objects and build out config dict.
        for key in config.keys():
            for mo in managed_objects:
                for cr in cmd_ref[mo]['ref']:
                    cr_keys = cr_key_lookup(key, mo)
                    for cr_key in cr_keys:
                        if cr._ref.get(cr_key) and cr._ref[cr_key].get('existing'):
                            if isinstance(config[key], dict):
                                for k in config[key].keys():
                                    for existing_key in cr._ref[cr_key]['existing'].keys():
                                        config[key][k] = cr._ref[cr_key]['existing'][existing_key][k]
                                continue
                            if isinstance(config[key], list):
                                for existing_key in cr._ref[cr_key]['existing'].keys():
                                    data = get_instance_data(key, cr_key, cr, existing_key)
                                    config[key].append(data)
                                continue
                            for existing_key in cr._ref[cr_key]['existing'].keys():
                                config[key] = cr._ref[cr_key]['existing'][existing_key]
                        elif cr._ref.get(cr_key):
                            data = get_instance_data(key, cr_key, cr, None)
                            if isinstance(config[key], list) and data not in config[key]:
                                config[key].append(data)

        return utils.remove_empties(config)
