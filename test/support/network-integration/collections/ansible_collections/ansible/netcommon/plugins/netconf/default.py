#
# (c) 2017 Red Hat Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """author: Ansible Networking Team
netconf: default
short_description: Use default netconf plugin to run standard netconf commands as
  per RFC
description:
- This default plugin provides low level abstraction apis for sending and receiving
  netconf commands as per Netconf RFC specification.
options:
  ncclient_device_handler:
    type: str
    default: default
    description:
    - Specifies the ncclient device handler name for network os that support default
      netconf implementation as per Netconf RFC specification. To identify the ncclient
      device handler name refer ncclient library documentation.
"""
import json

from ansible.module_utils._text import to_text
from ansible.plugins.netconf import NetconfBase


class Netconf(NetconfBase):
    def get_text(self, ele, tag):
        try:
            return to_text(
                ele.find(tag).text, errors="surrogate_then_replace"
            ).strip()
        except AttributeError:
            pass

    def get_device_info(self):
        device_info = dict()
        device_info["network_os"] = "default"
        return device_info

    def get_capabilities(self):
        result = dict()
        result["rpc"] = self.get_base_rpc()
        result["network_api"] = "netconf"
        result["device_info"] = self.get_device_info()
        result["server_capabilities"] = [c for c in self.m.server_capabilities]
        result["client_capabilities"] = [c for c in self.m.client_capabilities]
        result["session_id"] = self.m.session_id
        result["device_operations"] = self.get_device_operations(
            result["server_capabilities"]
        )
        return json.dumps(result)
