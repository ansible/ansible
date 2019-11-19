#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)#!/usr/bin/python
"""
The nxos vlans fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re
import ast
from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.common.utils import parse_conf_arg, parse_conf_cmd_arg
from ansible.module_utils.network.nxos.argspec.vlans.vlans import VlansArgs


class VlansFacts(object):
    """ The nxos vlans fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = VlansArgs.argument_spec
        spec = deepcopy(self.argument_spec)
        if subspec:
            if options:
                facts_argument_spec = spec[subspec][options]
            else:
                facts_argument_spec = spec[subspec]
        else:
            facts_argument_spec = spec

        self.generated_spec = utils.generate_dict(facts_argument_spec)

    def get_device_data(self, connection, show_cmd):
        """Wrapper method for `connection.get()`
        This exists solely to allow the unit test framework to mock device connection calls.
        """
        return connection.get(show_cmd)

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for vlans
        :param connection: the device connection
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        objs = []
        # **TBD**
        # N7K EOL/legacy image 6.2 does not support show vlan | json output.
        # If support is still required for this image then:
        # - Wrapp the json calls below in a try/except
        # - When excepted, use a helper method to parse the run_cfg_output,
        #   using the run_cfg_output data to generate compatible json data that
        #   can be read by normalize_table_data.
        if not data:
            # Use structured for most of the vlan parameter states.
            # This data is consistent across the supported nxos platforms.
            structured = self.get_device_data(connection, 'show vlan | json')

            # Raw cli config is needed for mapped_vni, which is not included in structured.
            run_cfg_output = self.get_device_data(connection, 'show running-config | section ^vlan')

            # Create a single dictionary from all data sources
            data = self.normalize_table_data(structured, run_cfg_output)

        for vlan in data:
            obj = self.render_config(self.generated_spec, vlan)
            if obj:
                objs.append(obj)

        ansible_facts['ansible_network_resources'].pop('vlans', None)
        facts = {}
        if objs:
            facts['vlans'] = []
            params = utils.validate_config(self.argument_spec, {'config': objs})
            for cfg in params['config']:
                facts['vlans'].append(utils.remove_empties(cfg))
        ansible_facts['ansible_network_resources'].update(facts)
        return ansible_facts

    def render_config(self, spec, vlan):
        """
        Render config as dictionary structure and delete keys
          from spec for null values
        :param spec: The facts tree, generated from the argspec
        :param vlan: structured data vlan settings (dict) and raw cfg from device
        :rtype: dictionary
        :returns: The generated config
        Sample inputs: test/units/modules/network/nxos/fixtures/nxos_vlans/show_vlan
        """
        obj = deepcopy(spec)

        obj['vlan_id'] = vlan['vlan_id']

        # name: 'VLAN000x' (default name) or custom name
        name = vlan['vlanshowbr-vlanname']
        if name and re.match("VLAN%04d" % int(vlan['vlan_id']), name):
            name = None
        obj['name'] = name

        # mode: 'ce-vlan' or 'fabricpath-vlan'
        obj['mode'] = vlan['vlanshowinfo-vlanmode'].replace('-vlan', '')

        # enabled: shutdown, noshutdown
        obj['enabled'] = True if 'noshutdown' in vlan['vlanshowbr-shutstate'] else False

        # state: active, suspend
        obj['state'] = vlan['vlanshowbr-vlanstate']

        # non-structured data
        obj['mapped_vni'] = parse_conf_arg(vlan['run_cfg'], 'vn-segment')

        return utils.remove_empties(obj)

    def normalize_table_data(self, structured, run_cfg_output):
        """Normalize structured output and raw running-config output into
        a single dict to simplify render_config usage.
        This is needed because:
        - The NXOS devices report most of the vlan settings within two
          structured data keys: 'vlanbrief' and 'mtuinfo', but the output is
          incomplete and therefore raw running-config data is also needed.
        - running-config by itself is insufficient because of major differences
          in the cli config syntax across platforms.
        - Thus a helper method combines settings from the separate top-level keys,
          and adds a 'run_cfg' key containing raw cli from the device.
        """
        # device output may be string, convert to list
        structured = ast.literal_eval(str(structured))

        vlanbrief = []
        mtuinfo = []
        if 'TABLE_vlanbrief' in structured:
            # SAMPLE: {"TABLE_vlanbriefid": {"ROW_vlanbriefid": {
            #   "vlanshowbr-vlanid": "4", "vlanshowbr-vlanid-utf": "4",
            #   "vlanshowbr-vlanname": "VLAN0004", "vlanshowbr-vlanstate": "active",
            #   "vlanshowbr-shutstate": "noshutdown"}},
            vlanbrief = structured['TABLE_vlanbrief']['ROW_vlanbrief']

            # SAMPLE: "TABLE_mtuinfoid": {"ROW_mtuinfoid": {
            #   "vlanshowinfo-vlanid": "4", "vlanshowinfo-media-type": "enet",
            #   "vlanshowinfo-vlanmode": "ce-vlan"}}
            mtuinfo = structured['TABLE_mtuinfo']['ROW_mtuinfo']

        if type(vlanbrief) is not list:
            # vlanbrief is not a list when only one vlan is found.
            vlanbrief = [vlanbrief]
            mtuinfo = [mtuinfo]

        # split out any per-vlan cli config
        run_cfg_list = re.split(r'[\n^]vlan ', run_cfg_output)

        # Create a list of vlan dicts where each dict contains vlanbrief,
        # mtuinfo, and non-structured running-config data for one vlan.
        vlans = []
        for index, v in enumerate(vlanbrief):
            v['vlan_id'] = v.get('vlanshowbr-vlanid-utf')
            vlan = {}
            vlan.update(v)
            vlan.update(mtuinfo[index])

            run_cfg = [i for i in run_cfg_list if "%s\n" % v['vlan_id'] in i] or ['']
            vlan['run_cfg'] = run_cfg.pop()
            vlans.append(vlan)
        return vlans
