#
# (c) 2018 Red Hat Inc.
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
---
netconf: sros
short_description: Use Nokia SROS netconf plugin to run netconf commands on Nokia SROS platform
deprecated:
    why: This plugin moved in 'nokia.sros' collection
    removed_in: '2.13'
    alternative: "Use the netconf plugin in 'nokia.sros' collection within Ansible galaxy"
description:
  - This sros plugin provides low level abstraction apis for
    sending and receiving netconf commands from Nokia sros network devices.
version_added: "2.9"
options:
  ncclient_device_handler:
    type: str
    default: default
    description:
      - Specifies the ncclient device handler name for Nokia sros network os. To
        identify the ncclient device handler name refer ncclient library documentation.
"""

import json
import re

from ansible.module_utils._text import to_text, to_native
from ansible.errors import AnsibleConnectionFailure
from ansible.plugins.netconf import NetconfBase
from ansible.plugins.netconf import ensure_ncclient

try:
    from ncclient import manager
    from ncclient.transport.errors import SSHUnknownHostError
    from ncclient.xml_ import to_ele
    HAS_NCCLIENT = True
except (ImportError, AttributeError):  # paramiko and gssapi are incompatible and raise AttributeError not ImportError
    HAS_NCCLIENT = False


class Netconf(NetconfBase):
    def get_text(self, ele, tag):
        try:
            return to_text(ele.find(tag).text, errors='surrogate_then_replace').strip()
        except AttributeError:
            pass

    @ensure_ncclient
    def get_device_info(self):
        device_info = dict()
        device_info['network_os'] = 'sros'

        xmlns = "urn:nokia.com:sros:ns:yang:sr:state"
        f = '<state xmlns="%s"><system><platform/><bootup/><version/><lldp/></system></state>' % xmlns
        reply = to_ele(self.m.get(filter=('subtree', f)).data_xml)

        device_info['network_os_hostname'] = reply.findtext('.//{%s}state/{*}system/{*}lldp/{*}system-name' % xmlns)
        device_info['network_os_version'] = reply.findtext('.//{%s}state/{*}system/{*}version/{*}version-number' % xmlns)
        device_info['network_os_model'] = reply.findtext('.//{%s}state/{*}system/{*}platform' % xmlns)
        device_info['network_os_platform'] = 'Nokia 7x50'
        return device_info

    def get_capabilities(self):
        result = dict()
        result['rpc'] = self.get_base_rpc()
        result['network_api'] = 'netconf'
        result['device_info'] = self.get_device_info()
        result['server_capabilities'] = [c for c in self.m.server_capabilities]
        result['client_capabilities'] = [c for c in self.m.client_capabilities]
        result['session_id'] = self.m.session_id
        result['device_operations'] = self.get_device_operations(result['server_capabilities'])
        return json.dumps(result)

    @staticmethod
    @ensure_ncclient
    def guess_network_os(obj):
        try:
            m = manager.connect(
                host=obj._play_context.remote_addr,
                port=obj._play_context.port or 830,
                username=obj._play_context.remote_user,
                password=obj._play_context.password,
                key_filename=obj.key_filename,
                hostkey_verify=obj.get_option('host_key_checking'),
                look_for_keys=obj.get_option('look_for_keys'),
                allow_agent=obj._play_context.allow_agent,
                timeout=obj.get_option('persistent_connect_timeout'),
                # We need to pass in the path to the ssh_config file when guessing
                # the network_os so that a jumphost is correctly used if defined
                ssh_config=obj._ssh_config
            )
        except SSHUnknownHostError as exc:
            raise AnsibleConnectionFailure(to_native(exc))

        guessed_os = None
        for c in m.server_capabilities:
            if re.search('urn:nokia.com:sros:ns:yang:sr', c):
                guessed_os = 'sros'

        m.close_session()
        return guessed_os
