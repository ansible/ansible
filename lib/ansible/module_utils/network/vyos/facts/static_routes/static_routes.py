#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vyos static_routes fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from re import findall, search, M
from copy import deepcopy
from ansible.module_utils.network.common import utils
from ansible.module_utils.network.vyos.argspec.static_routes.static_routes import Static_routesArgs


class Static_routesFacts(object):
    """ The vyos static_routes fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = Static_routesArgs.argument_spec
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
        """ Populate the facts for static_routes
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if not data:
            data = connection.get_config()

            # typically data is populated from the current device configuration
            # data = connection.get('show running-config | section ^interface')
            # using mock data instead
            objs = []
            static_routes = findall(r'^set protocols static route(6)? (\S+)', data, M)
            if static_routes:
                for route in set(static_routes):
                    route_regex = r' %s .+$' % route[1]
                    cfg = findall(route_regex, data, M)
                    obj = self.render_config(cfg)
                    obj['address'] = route[1].strip("'")
                    if obj:
                        objs.append(obj)

            ansible_facts['ansible_network_resources'].pop('static_routes', None)
            facts = {}
            if objs:
                facts['static_routes'] = []
                params = utils.validate_config(self.argument_spec, {'config': objs})
                for cfg in params['config']:
                    facts['static_routes'].append(utils.remove_empties(cfg))

            ansible_facts['ansible_network_resources'].update(facts)
        return ansible_facts

    def render_config(self, conf):
        """
        Render config as dictionary structure and delete keys
          from spec for null values

        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        config = {}
        next_hop_conf = '\n'.join(filter(lambda x: ('next-hop' in x), conf))
        blackhole_conf = '\n'.join(filter(lambda x: ('blackhole' in x), conf))
        config['blackhole'] = self.parse_blackhole(blackhole_conf)
        config['next_hop'] = self.parse_next_hop(next_hop_conf)
        return utils.remove_empties(config)


    def parse_blackhole(self, conf):
        blackhole = None
        if conf:

            distance = search(r'^.*blackhole distance (.+)', conf, M)
            bh = conf.find('blackhole')
            if distance:
                blackhole = {}
                value = distance.group(1).strip("'")
                blackhole['distance'] = int(value)
            elif bh:
                blackhole = {}
                blackhole['enabled'] = True
        return blackhole

    def parse_next_hop(self, conf):
        next_hop_list = None
        if conf:
            next_hop_list = []
            hop_list = findall(r"^.*next-hop (.+)", conf, M)

            if hop_list:
                for hop in hop_list:
                    distance = search(r'^.*distance (.+)', hop, M)
                    dis = hop.find('disable')
                    hop_info = hop.split(' ')
                    next_hop_info = {}
                    next_hop_info['address'] = hop_info[0].strip("'")
                    if distance:
                        value = distance.group(1).strip("'")
                        next_hop_info['distance'] = int(value)
                    elif dis >= 1:
                        next_hop_info['enabled'] = False
                    next_hop_list.append(next_hop_info)
        return next_hop_list

