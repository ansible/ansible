#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The junos static_routes fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from copy import deepcopy

from ansible.module_utils._text import to_bytes
from ansible.module_utils.network.common import utils
from ansible.module_utils.network.junos.argspec.static_routes.static_routes import Static_routesArgs
from ansible.module_utils.six import string_types
try:
    from lxml import etree
    HAS_LXML = True
except ImportError:
    HAS_LXML = False


class Static_routesFacts(object):
    """ The junos static_routes fact class
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
        if not HAS_LXML:
            self._module.fail_json(msg='lxml is not installed.')

        if not data:
            config_filter = """
                <configuration>
                  <routing-instances/>
                  <routing-options/>
                </configuration>
                """
            data = connection.get_configuration(filter=config_filter)

        if isinstance(data, string_types):
            data = etree.fromstring(to_bytes(data,
                                             errors='surrogate_then_replace'))

        resources = data.xpath('configuration/routing-options')
        vrf_resources = data.xpath('configuration/routing-instances')
        resources.extend(vrf_resources)

        self.update_ansible_facts(ansible_facts, resources)
        return ansible_facts

    def update_ansible_facts(self, ansible_facts, resources):
        objs = {'address_families': []}
        for resource in resources:
            if resource:
                obj = self.render_config(self.generated_spec, resource)
                if obj:
                    objs['address_families'].extend(obj['address_families'])

        facts = {}
        if objs:
            facts['static_routes'] = []
            params = {'config': [objs]}
            for cfg in params['config']:
                facts['static_routes'].append(utils.remove_empties(cfg))
            ansible_facts['ansible_network_resources'].update(facts)

    def _create_route_dict(self, dest, next_hop, metric=''):
        route_dict = {'dest': dest,
                      'next_hop': [
                          {'forward_router_address': next_hop}],
                      'metric': metric}
        return route_dict

    def render_config(self, spec, conf):
        """
        Render config as dictionary structure and delete keys
          from spec for null values

        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        config = deepcopy(spec)

        ipv6_routes = conf.xpath('rib/static/route')
        ipv4_routes = conf.xpath('static/route')
        vrfs = conf.xpath('instance')
        routes = []

        for vrf in vrfs:
            vrf_name = utils.get_xml_conf_arg(vrf, 'name')
            ipv4_vrf_routes = vrf.xpath('routing-options/static/route')
            ipv6_vrf_routes = vrf.xpath('routing-options/rib/static/route')
            ip_dict = {'vrf': vrf_name,
                       'vrf_routes': []}
            ipv4_dict = {'afi': 'ipv4',
                         'routes': []}
            ipv6_dict = {'afi': 'ipv6',
                         'routes': []}

            for ipv4_r in ipv4_vrf_routes:
                ipv4_route_dict = {'dest': utils.get_xml_conf_arg(ipv4_r, 'name'),
                                   'next_hop': [
                                       {'forward_router_address':
                                        utils.get_xml_conf_arg(ipv4_r, 'next-hop')}],
                                   'metric': utils.get_xml_conf_arg(ipv4_r, 'metric')}
                ipv4_dict['routes'].append(ipv4_route_dict)

            for ipv6_r in ipv6_vrf_routes:
                ipv6_route_dict = {'dest': utils.get_xml_conf_arg(ipv6_r, 'name'),
                                   'next_hop': [
                                       {'forward_router_address':
                                        utils.get_xml_conf_arg(ipv6_r, 'next-hop')}],
                                   'metric': utils.get_xml_conf_arg(ipv6_r, 'metric')}
                ipv6_dict['routes'].append(ipv6_route_dict)

            if ipv4_dict['routes']:
                ip_dict['vrf_routes'].append(ipv4_dict)
            if ipv6_dict['routes']:
                ip_dict['vrf_routes'].append(ipv6_dict)
            routes.append(ip_dict)

        ipv4_global_routes = {'afi': 'ipv4',
                              'routes': []}
        for route in ipv4_routes:
            dest = utils.get_xml_conf_arg(route, 'name')
            next_hop = utils.get_xml_conf_arg(route, 'next-hop')
            metric = utils.get_xml_conf_arg(route, 'metric/metric-value')
            route_dict = self._create_route_dict(dest, next_hop, metric)
            ipv4_global_routes['routes'].append(route_dict)

        if ipv4_routes:
            routes.append(ipv4_global_routes)

        ipv6_global_routes = {'afi': 'ipv6',
                              'routes': []}
        for route in ipv6_routes:
            dest = utils.get_xml_conf_arg(route, 'name')
            next_hop = utils.get_xml_conf_arg(route, 'next-hop')
            metric = utils.get_xml_conf_arg(route, 'metric/metric-value')
            route_dict = self._create_route_dict(dest, next_hop, metric)
            ipv6_global_routes['routes'].append(route_dict)

        if ipv6_routes:
            routes.append(ipv6_global_routes)

        config['address_families'] = routes
        return utils.remove_empties(config)
