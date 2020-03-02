#
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The junos acls fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from copy import deepcopy

from ansible.module_utils._text import to_bytes
from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.network.common import utils
from ansible.module_utils.network.junos.argspec.acls.acls import AclsArgs
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


class AclsFacts(object):
    """ The junos acls fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = AclsArgs.argument_spec
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
        """ Populate the facts for acls
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if not HAS_LXML:
            self._module.fail_json(msg=missing_required_lib("lxml"))

        if not data:
            config_filter = """
                <configuration>
                  <firewall/>
                </configuration>
                """
            data = connection.get_configuration(filter=config_filter)

        if isinstance(data, string_types):
            data = etree.fromstring(to_bytes(data,
                                             errors='surrogate_then_replace'))

        resources = data.xpath('configuration/firewall')

        objs = []
        for resource in resources:
            if resource:
                xml = self._get_xml_dict(resource)
                for family, sub_dict in xml["firewall"]["family"].items():
                    sub_dict["family"] = family
                    obj = self.render_config(self.generated_spec, dict(firewall=sub_dict))
                    if obj:
                        objs.append(obj)

        facts = {}
        if objs:
            facts['junos_acls'] = []
            params = utils.validate_config(self.argument_spec, {'config': objs})
            for cfg in params['config']:
                facts['junos_acls'].append(utils.remove_empties(cfg))

        ansible_facts['ansible_network_resources'].update(facts)
        return ansible_facts

    def _get_xml_dict(self, xml_root):
        if not HAS_XMLTODICT:
            self._module.fail_json(msg=missing_required_lib("xmltodict"))

        xml_dict = xmltodict.parse(etree.tostring(xml_root), dict_constructor=dict)
        return xml_dict

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
        config["afi"] = "ipv6" if conf["firewall"].pop("family") == "inet6" else "ipv4"
        acls = conf.get('firewall').get('filter')
        if not isinstance(acls, list):
            acls = [acls]
        config['acls'] = []
        for acl in acls:
            acl_dict = {'name': acl['name'],
                        'aces': []}
            if acl.get('term'):
                terms = acl["term"]
                if not isinstance(terms, list):
                    terms = [terms]
                for term in terms:
                    ace = {'name': term.get('name')}
                    if term.get('from'):
                        if term['from'].get('source-address'):
                            ace['source'] = ace.get('source', {})
                            ace['source']['address'] = term['from']['source-address']['name']
                        if term['from'].get('source-prefix-list'):
                            ace['source'] = ace.get('source', {})
                            ace['source']['prefix_list'] = term['from']['source-prefix-list']['name']
                        if term['from'].get('source-port'):
                            ace['source'] = ace.get('source', {})
                            ace['source']['port_protocol'] = dict(eq=term['from']['source-port'])
                        if term['from'].get('destination-address'):
                            ace['destination'] = ace.get('destination', {})
                            ace['destination']['address'] = term['from']['destination-address']['name']
                        if term['from'].get('destination-prefix-list'):
                            ace['destination'] = ace.get('destination', {})
                            ace['destination']['prefix_list'] = term['from']['destination-prefix-list']['name']
                        if term['from'].get('destination-port'):
                            ace['destination']['port_protocol'] = dict(eq=term['from']['destination-port'])
                        if term['from'].get('protocol'):
                            ace['protocol'] = term['from']['protocol']
                        if term["from"].get("icmp-type"):
                            ace["protocol_options"] = dict(icmp={})
                            icmp_type = term["from"]["icmp-type"]
                            if icmp_type == "echo-reply":
                                ace["protocol_options"]["icmp"]["echo_reply"] = True
                            if icmp_type == "echo-request":
                                ace["protocol_options"]["icmp"]["echo"] = True
                            if icmp_type == "redirect":
                                ace["protocol_options"]["icmp"]["redirect"] = True
                            if icmp_type == "router-advertisement":
                                ace["protocol_options"]["icmp"]["router_advertisement"] = True
                            if icmp_type == "router-solicit":
                                ace["protocol_options"]["icmp"]["router_solicitation"] = True
                            if icmp_type == "time-exceeded":
                                ace["protocol_options"]["icmp"]["time_exceeded"] = True
                        if term["from"].get("icmp-code"):
                            ace["protocol_options"] = dict(icmp={})
                            icmp_code = term["from"]["icmp-code"]
                            if icmp_code == "destination-host-prohibited":
                                ace["protocol_options"]["icmp"]["dod_host_prohibited"] = True
                            if icmp_code == "destination-host-unknown":
                                ace["protocol_options"]["icmp"]["host_unknown"] = True
                            if icmp_code == "destination-network-prohibited":
                                ace["protocol_options"]["icmp"]["dod_net_prohibited"] = True
                            if icmp_code == "destination-network-unknown":
                                ace["protocol_options"]["icmp"]["network_unknown"] = True
                            if icmp_code == "host-unreachable":
                                ace["protocol_options"]["icmp"]["host_unreachable"] = True
                            if icmp_code == "host-unreachable-for-tos":
                                ace["protocol_options"]["icmp"]["host_tos_unreachable"] = True
                            if icmp_code == "port-unreachable":
                                ace["protocol_options"]["icmp"]["port_unreachable"] = True
                            if icmp_code == "protocol-unreachable":
                                ace["protocol_options"]["icmp"]["protocol_unreachable"] = True
                            if icmp_code == "redirect-for-host":
                                ace["protocol_options"]["icmp"]["host_redirect"] = True
                            if icmp_code == "redirect-for-network":
                                ace["protocol_options"]["icmp"]["net_redirect"] = True
                            if icmp_code == "redirect-for-tos-and-host":
                                ace["protocol_options"]["icmp"]["host_tos_redirect"] = True
                            if icmp_code == "redirect-for-tos-and-net":
                                ace["protocol_options"]["icmp"]["net_tos_redirect"] = True
                            if icmp_code == "source-route-failed":
                                ace["protocol_options"]["icmp"]["source_route_failed"] = True
                            if icmp_code == "ttl-eq-zero-during-reassembly":
                                ace["protocol_options"]["icmp"]["reassembly-timeout"] = True
                            if icmp_code == "ttl-eq-zero-during-transit":
                                ace["protocol_options"]["icmp"]["ttl_exceeded"] = True

                    if term.get("then"):
                        if "accept" in term["then"]:
                            ace["grant"] = "permit"
                        if "discard" in term["then"]:
                            ace["grant"] = "deny"
                    acl_dict['aces'].append(ace)
            config['acls'].append(acl_dict)
        return utils.remove_empties(config)
