# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The VyOS interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import platform
import re
from ansible_collections.vyos.vyos.plugins.module_utils.network.vyos.vyos import (
    run_commands,
    get_capabilities,
)


class LegacyFactsBase(object):

    COMMANDS = frozenset()

    def __init__(self, module):
        self.module = module
        self.facts = dict()
        self.warnings = list()
        self.responses = None

    def populate(self):
        self.responses = run_commands(self.module, list(self.COMMANDS))


class Default(LegacyFactsBase):

    COMMANDS = [
        "show version",
    ]

    def populate(self):
        super(Default, self).populate()
        data = self.responses[0]
        self.facts["serialnum"] = self.parse_serialnum(data)
        self.facts.update(self.platform_facts())

    def parse_serialnum(self, data):
        match = re.search(r"HW S/N:\s+(\S+)", data)
        if match:
            return match.group(1)

    def platform_facts(self):
        platform_facts = {}

        resp = get_capabilities(self.module)
        device_info = resp["device_info"]

        platform_facts["system"] = device_info["network_os"]

        for item in ("model", "image", "version", "platform", "hostname"):
            val = device_info.get("network_os_%s" % item)
            if val:
                platform_facts[item] = val

        platform_facts["api"] = resp["network_api"]
        platform_facts["python_version"] = platform.python_version()

        return platform_facts


class Config(LegacyFactsBase):

    COMMANDS = [
        "show configuration commands",
        "show system commit",
    ]

    def populate(self):
        super(Config, self).populate()

        self.facts["config"] = self.responses

        commits = self.responses[1]
        entries = list()
        entry = None

        for line in commits.split("\n"):
            match = re.match(r"(\d+)\s+(.+)by(.+)via(.+)", line)
            if match:
                if entry:
                    entries.append(entry)

                entry = dict(
                    revision=match.group(1),
                    datetime=match.group(2),
                    by=str(match.group(3)).strip(),
                    via=str(match.group(4)).strip(),
                    comment=None,
                )
            else:
                entry["comment"] = line.strip()

        self.facts["commits"] = entries


class Neighbors(LegacyFactsBase):

    COMMANDS = [
        "show lldp neighbors",
        "show lldp neighbors detail",
    ]

    def populate(self):
        super(Neighbors, self).populate()

        all_neighbors = self.responses[0]
        if "LLDP not configured" not in all_neighbors:
            neighbors = self.parse(self.responses[1])
            self.facts["neighbors"] = self.parse_neighbors(neighbors)

    def parse(self, data):
        parsed = list()
        values = None
        for line in data.split("\n"):
            if not line:
                continue
            elif line[0] == " ":
                values += "\n%s" % line
            elif line.startswith("Interface"):
                if values:
                    parsed.append(values)
                values = line
        if values:
            parsed.append(values)
        return parsed

    def parse_neighbors(self, data):
        facts = dict()
        for item in data:
            interface = self.parse_interface(item)
            host = self.parse_host(item)
            port = self.parse_port(item)
            if interface not in facts:
                facts[interface] = list()
            facts[interface].append(dict(host=host, port=port))
        return facts

    def parse_interface(self, data):
        match = re.search(r"^Interface:\s+(\S+),", data)
        return match.group(1)

    def parse_host(self, data):
        match = re.search(r"SysName:\s+(.+)$", data, re.M)
        if match:
            return match.group(1)

    def parse_port(self, data):
        match = re.search(r"PortDescr:\s+(.+)$", data, re.M)
        if match:
            return match.group(1)
