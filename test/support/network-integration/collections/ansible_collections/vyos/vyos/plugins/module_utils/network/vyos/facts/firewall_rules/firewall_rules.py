#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vyos firewall_rules fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from re import findall, search, M
from copy import deepcopy
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common import (
    utils,
)
from ansible_collections.vyos.vyos.plugins.module_utils.network.vyos.argspec.firewall_rules.firewall_rules import (
    Firewall_rulesArgs,
)


class Firewall_rulesFacts(object):
    """ The vyos firewall_rules fact class
    """

    def __init__(self, module, subspec="config", options="options"):
        self._module = module
        self.argument_spec = Firewall_rulesArgs.argument_spec
        spec = deepcopy(self.argument_spec)
        if subspec:
            if options:
                facts_argument_spec = spec[subspec][options]
            else:
                facts_argument_spec = spec[subspec]
        else:
            facts_argument_spec = spec

        self.generated_spec = utils.generate_dict(facts_argument_spec)

    def get_device_data(self, connection):
        return connection.get_config()

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for firewall_rules
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if not data:
            # typically data is populated from the current device configuration
            # data = connection.get('show running-config | section ^interface')
            # using mock data instead
            data = self.get_device_data(connection)
        # split the config into instances of the resource
        objs = []
        v6_rules = findall(
            r"^set firewall ipv6-name (?:\'*)(\S+)(?:\'*)", data, M
        )
        v4_rules = findall(r"^set firewall name (?:\'*)(\S+)(?:\'*)", data, M)
        if v6_rules:
            config = self.get_rules(data, v6_rules, type="ipv6")
            if config:
                config = utils.remove_empties(config)
                objs.append(config)
        if v4_rules:
            config = self.get_rules(data, v4_rules, type="ipv4")
            if config:
                config = utils.remove_empties(config)
                objs.append(config)

        ansible_facts["ansible_network_resources"].pop("firewall_rules", None)
        facts = {}
        if objs:
            facts["firewall_rules"] = []
            params = utils.validate_config(
                self.argument_spec, {"config": objs}
            )
            for cfg in params["config"]:
                facts["firewall_rules"].append(utils.remove_empties(cfg))

        ansible_facts["ansible_network_resources"].update(facts)
        return ansible_facts

    def get_rules(self, data, rules, type):
        """
        This function performs following:
        - Form regex to fetch 'rule-sets' specific config from data.
        - Form the rule-set list based on ip address.
        :param data: configuration.
        :param rules: list of rule-sets.
        :param type: ip address type.
        :return: generated rule-sets configuration.
        """
        r_v4 = []
        r_v6 = []
        for r in set(rules):
            rule_regex = r" %s .+$" % r.strip("'")
            cfg = findall(rule_regex, data, M)
            fr = self.render_config(cfg, r.strip("'"))
            fr["name"] = r.strip("'")
            if type == "ipv6":
                r_v6.append(fr)
            else:
                r_v4.append(fr)
        if r_v4:
            config = {"afi": "ipv4", "rule_sets": r_v4}
        if r_v6:
            config = {"afi": "ipv6", "rule_sets": r_v6}
        return config

    def render_config(self, conf, match):
        """
        Render config as dictionary structure and delete keys
          from spec for null values

        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        conf = "\n".join(filter(lambda x: x, conf))
        a_lst = ["description", "default_action", "enable_default_log"]
        config = self.parse_attr(conf, a_lst, match)
        if not config:
            config = {}
        config["rules"] = self.parse_rules_lst(conf)
        return config

    def parse_rules_lst(self, conf):
        """
        This function forms the regex to fetch the 'rules' with in
        'rule-sets'
        :param conf: configuration data.
        :return: generated rule list configuration.
        """
        r_lst = []
        rules = findall(r"rule (?:\'*)(\d+)(?:\'*)", conf, M)
        if rules:
            rules_lst = []
            for r in set(rules):
                r_regex = r" %s .+$" % r
                cfg = "\n".join(findall(r_regex, conf, M))
                obj = self.parse_rules(cfg)
                obj["number"] = int(r)
                if obj:
                    rules_lst.append(obj)
            r_lst = sorted(rules_lst, key=lambda i: i["number"])
        return r_lst

    def parse_rules(self, conf):
        """
        This function triggers the parsing of 'rule' attributes.
        a_lst is a list having rule attributes which doesn't
        have further sub attributes.
        :param conf: configuration
        :return: generated rule configuration dictionary.
        """
        a_lst = [
            "ipsec",
            "action",
            "protocol",
            "fragment",
            "disabled",
            "description",
        ]
        rule = self.parse_attr(conf, a_lst)
        r_sub = {
            "p2p": self.parse_p2p(conf),
            "tcp": self.parse_tcp(conf, "tcp"),
            "icmp": self.parse_icmp(conf, "icmp"),
            "time": self.parse_time(conf, "time"),
            "limit": self.parse_limit(conf, "limit"),
            "state": self.parse_state(conf, "state"),
            "recent": self.parse_recent(conf, "recent"),
            "source": self.parse_src_or_dest(conf, "source"),
            "destination": self.parse_src_or_dest(conf, "destination"),
        }
        rule.update(r_sub)
        return rule

    def parse_p2p(self, conf):
        """
        This function forms the regex to fetch the 'p2p' with in
        'rules'
        :param conf: configuration data.
        :return: generated rule list configuration.
        """
        a_lst = []
        applications = findall(r"p2p (?:\'*)(\d+)(?:\'*)", conf, M)
        if applications:
            app_lst = []
            for r in set(applications):
                obj = {"application": r.strip("'")}
                app_lst.append(obj)
            a_lst = sorted(app_lst, key=lambda i: i["application"])
        return a_lst

    def parse_src_or_dest(self, conf, attrib=None):
        """
        This function triggers the parsing of 'source or
        destination' attributes.
        :param conf: configuration.
        :param attrib:'source/destination'.
        :return:generated source/destination configuration dictionary.
        """
        a_lst = ["port", "address", "mac_address"]
        cfg_dict = self.parse_attr(conf, a_lst, match=attrib)
        cfg_dict["group"] = self.parse_group(conf, attrib + " group")
        return cfg_dict

    def parse_recent(self, conf, attrib=None):
        """
        This function triggers the parsing of 'recent' attributes
        :param conf: configuration.
        :param attrib: 'recent'.
        :return: generated config dictionary.
        """
        a_lst = ["time", "count"]
        cfg_dict = self.parse_attr(conf, a_lst, match=attrib)
        return cfg_dict

    def parse_tcp(self, conf, attrib=None):
        """
        This function triggers the parsing of 'tcp' attributes.
        :param conf: configuration.
        :param attrib: 'tcp'.
        :return: generated config dictionary.
        """
        cfg_dict = self.parse_attr(conf, ["flags"], match=attrib)
        return cfg_dict

    def parse_time(self, conf, attrib=None):
        """
        This function triggers the parsing of 'time' attributes.
        :param conf: configuration.
        :param attrib: 'time'.
        :return: generated config dictionary.
        """
        a_lst = [
            "stopdate",
            "stoptime",
            "weekdays",
            "monthdays",
            "startdate",
            "starttime",
        ]
        cfg_dict = self.parse_attr(conf, a_lst, match=attrib)
        return cfg_dict

    def parse_state(self, conf, attrib=None):
        """
        This function triggers the parsing of 'state' attributes.
        :param conf: configuration
        :param attrib: 'state'.
        :return: generated config dictionary.
        """
        a_lst = ["new", "invalid", "related", "established"]
        cfg_dict = self.parse_attr(conf, a_lst, match=attrib)
        return cfg_dict

    def parse_group(self, conf, attrib=None):
        """
        This function triggers the parsing of 'group' attributes.
        :param conf: configuration.
        :param attrib: 'group'.
        :return: generated config dictionary.
        """
        a_lst = ["port_group", "address_group", "network_group"]
        cfg_dict = self.parse_attr(conf, a_lst, match=attrib)
        return cfg_dict

    def parse_icmp(self, conf, attrib=None):
        """
        This function triggers the parsing of 'icmp' attributes.
        :param conf: configuration to be parsed.
        :param attrib: 'icmp'.
        :return: generated config dictionary.
        """
        a_lst = ["code", "type", "type_name"]
        cfg_dict = self.parse_attr(conf, a_lst, match=attrib)
        return cfg_dict

    def parse_limit(self, conf, attrib=None):
        """
        This function triggers the parsing of 'limit' attributes.
        :param conf: configuration to be parsed.
        :param attrib: 'limit'
        :return: generated config dictionary.
        """
        cfg_dict = self.parse_attr(conf, ["burst"], match=attrib)
        cfg_dict["rate"] = self.parse_rate(conf, "rate")
        return cfg_dict

    def parse_rate(self, conf, attrib=None):
        """
        This function triggers the parsing of 'rate' attributes.
        :param conf: configuration.
        :param attrib: 'rate'
        :return: generated config dictionary.
        """
        a_lst = ["unit", "number"]
        cfg_dict = self.parse_attr(conf, a_lst, match=attrib)
        return cfg_dict

    def parse_attr(self, conf, attr_list, match=None):
        """
        This function peforms the following:
        - Form the regex to fetch the required attribute config.
        - Type cast the output in desired format.
        :param conf: configuration.
        :param attr_list: list of attributes.
        :param match: parent node/attribute name.
        :return: generated config dictionary.
        """
        config = {}
        for attrib in attr_list:
            regex = self.map_regex(attrib)
            if match:
                regex = match + " " + regex
            if conf:
                if self.is_bool(attrib):
                    out = conf.find(attrib.replace("_", "-"))

                    dis = conf.find(attrib.replace("_", "-") + " 'disable'")
                    if out >= 1:
                        if dis >= 1:
                            config[attrib] = False
                        else:
                            config[attrib] = True
                else:
                    out = search(r"^.*" + regex + " (.+)", conf, M)
                    if out:
                        val = out.group(1).strip("'")
                        if self.is_num(attrib):
                            val = int(val)
                        config[attrib] = val
        return config

    def map_regex(self, attrib):
        """
        - This function construct the regex string.
        - replace the underscore with hyphen.
        :param attrib: attribute
        :return: regex string
        """
        regex = attrib.replace("_", "-")
        if attrib == "disabled":
            regex = "disable"
        return regex

    def is_bool(self, attrib):
        """
        This function looks for the attribute in predefined bool type set.
        :param attrib: attribute.
        :return: True/False
        """
        bool_set = (
            "new",
            "invalid",
            "related",
            "disabled",
            "established",
            "enable_default_log",
        )
        return True if attrib in bool_set else False

    def is_num(self, attrib):
        """
        This function looks for the attribute in predefined integer type set.
        :param attrib: attribute.
        :return: True/false.
        """
        num_set = ("time", "code", "type", "count", "burst", "number")
        return True if attrib in num_set else False
