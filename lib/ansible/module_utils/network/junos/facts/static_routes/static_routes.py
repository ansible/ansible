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
try:
    import xmltodict
    HAS_XMLTODICT = True
except ImportError:
    HAS_XMLTODICT = False


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
        if not HAS_XMLTODICT:
            self._module.fail_json(msg='xmltodict is not installed.')

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

        objs = []
        for resource in resources:
            if resource is not None:
                xml = self._get_xml_dict(resource)
                obj = self.render_config(self.generated_spec, xml)
                if obj:
                    objs.append(obj)

        facts = {}
        if objs:
            facts['static_routes'] = []
            params = utils.validate_config(self.argument_spec,
                                           {'config': objs})
            for cfg in params['config']:
                facts['static_routes'].append(utils.remove_empties(cfg))
        ansible_facts['ansible_network_resources'].update(facts)
        return ansible_facts

    def _get_xml_dict(self, xml_root):
        xml_dict = xmltodict.parse(etree.tostring(xml_root), dict_constructor=dict)
        return xml_dict

    def _create_route_dict(self, afi, route_path):
        routes_dict = {'afi': afi,
                       'routes': []}
        if isinstance(route_path, dict):
            route_path = [route_path]
        for route in route_path:
            route_dict = {}
            route_dict['dest'] = route['name']
            if route.get('metric'):
                route_dict['metric'] = route['metric']['metric-value']
            route_dict['next_hop'] = []
            route_dict['next_hop'].append({'forward_router_address': route['next-hop']})
            routes_dict['routes'].append(route_dict)
        return routes_dict

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
        routes = []
        config['address_families'] = []

        if conf.get('routing-options'):
            if conf['routing-options'].get('rib'):
                if conf['routing-options'].get('rib').get('name') == 'inet6.0':
                    if conf['routing-options'].get('rib').get('static'):
                        route_path = conf['routing-options']['rib']['static'].get('route')
                        routes.append(self._create_route_dict('ipv6', route_path))
            if conf['routing-options'].get('static'):
                route_path = conf['routing-options']['static'].get('route')
                routes.append(self._create_route_dict('ipv4', route_path))

        if conf.get('routing-instances'):
            config['vrf'] = conf['routing-instances']['instance']['name']
            if conf['routing-instances'].get('instance').get('routing-options').get('rib').get('name') == config['vrf'] + '.inet6.0':
                if conf['routing-instances']['instance']['routing-options']['rib'].get('static'):
                    route_path = conf['routing-instances']['instance']['routing-options']['rib']['static'].get('route')
                    routes.append(self._create_route_dict('ipv6', route_path))
            if conf['routing-instances'].get('instance').get('routing-options').get('static'):
                route_path = conf['routing-instances']['instance']['routing-options']['static'].get('route')
                routes.append(self._create_route_dict('ipv4', route_path))
        config['address_families'].extend(routes)
        return utils.remove_empties(config)
