#
# -*- coding: utf-8 -*-
# Copyright 2019 Fortinet, Inc.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The fortios system facts class
It is in this file the runtime information is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re
from ansible.module_utils.network.common import utils
from ansible.module_utils.network.fortios.argspec.system.system import SystemArgs


class SystemFacts(object):
    """ The fortios system facts class
    """

    def __init__(self, module, fos=None, subset=None, subspec='config', options='options'):
        self._module = module
        self._fos = fos
        self._subset = subset

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for system
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :rtype: dictionary
        :returns: facts
        """
        ansible_facts['ansible_network_resources'].pop('system', None)
        facts = {}
        if self._subset['fact'].startswith(tuple(SystemArgs.FACT_SYSTEM_SUBSETS)):
            gather_method = getattr(self, self._subset['fact'].replace('-', '_'), self.system_fact)
            resp = gather_method()
            facts.update({self._subset['fact']: resp})

        ansible_facts['ansible_network_resources'].update(facts)
        return ansible_facts

    def system_fact(self):
        fos = self._fos
        vdom = self._module.params['vdom']
        return fos.monitor('system', self._subset['fact'][len('system_'):].replace('_', '/'), vdom=vdom)

    def system_interface_select(self):
        fos = self._fos
        vdom = self._module.params['vdom']

        query_string = '?vdom=' + vdom
        system_interface_select_param = self._subset['filters']
        if system_interface_select_param:
            for filter in system_interface_select_param:
                for key, val in filter.items():
                    if val:
                        query_string += '&' + str(key) + '=' + str(val)

        return fos.monitor('system', self._subset['fact'][len('system_'):].replace('_', '/') + query_string, vdom=None)
