#
# (c) 2017 Red Hat Inc.
# (c) 2017 Kedar Kekan (kkekan@redhat.com)
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
author: Ansible Networking Team
netconf: iosxr
short_description: Use iosxr netconf plugin to run netconf commands on Cisco IOSXR platform
description:
  - This iosxr plugin provides low level abstraction apis for
    sending and receiving netconf commands from Cisco iosxr network devices.
version_added: "2.9"
options:
  ncclient_device_handler:
    type: str
    default: iosxr
    description:
      - Specifies the ncclient device handler name for Cisco iosxr network os. To
        identify the ncclient device handler name refer ncclient library documentation.
"""

import json
import re
import collections

from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.network.common.netconf import remove_namespaces
from ansible.module_utils.network.iosxr.iosxr import build_xml, etree_find
from ansible.errors import AnsibleConnectionFailure
from ansible.plugins.netconf import NetconfBase, ensure_ncclient

try:
    from ncclient import manager
    from ncclient.operations import RPCError
    from ncclient.transport.errors import SSHUnknownHostError
    from ncclient.xml_ import to_xml
    HAS_NCCLIENT = True
except (ImportError, AttributeError):  # paramiko and gssapi are incompatible and raise AttributeError not ImportError
    HAS_NCCLIENT = False


class Netconf(NetconfBase):
    def get_device_info(self):
        device_info = {}
        device_info['network_os'] = 'iosxr'
        install_meta = collections.OrderedDict()
        install_meta.update([
            ('boot-variables', {'xpath': 'install/boot-variables', 'tag': True}),
            ('boot-variable', {'xpath': 'install/boot-variables/boot-variable', 'tag': True, 'lead': True}),
            ('software', {'xpath': 'install/software', 'tag': True}),
            ('alias-devices', {'xpath': 'install/software/alias-devices', 'tag': True}),
            ('alias-device', {'xpath': 'install/software/alias-devices/alias-device', 'tag': True}),
            ('m:device-name', {'xpath': 'install/software/alias-devices/alias-device/device-name', 'value': 'disk0:'}),
        ])

        install_filter = build_xml('install', install_meta, opcode='filter')
        try:
            reply = self.get(install_filter)
            resp = remove_namespaces(re.sub(r'<\?xml version="1.0" encoding="UTF-8"\?>', '', reply))
            ele_boot_variable = etree_find(resp, 'boot-variable/boot-variable')
            if ele_boot_variable is not None:
                device_info['network_os_image'] = re.split('[:|,]', ele_boot_variable.text)[1]
            ele_package_name = etree_find(reply, 'package-name')
            if ele_package_name is not None:
                device_info['network_os_package'] = ele_package_name.text
                device_info['network_os_version'] = re.split('-', ele_package_name.text)[-1]

            hostname_filter = build_xml('host-names', opcode='filter')
            reply = self.get(hostname_filter)
            resp = remove_namespaces(re.sub(r'<\?xml version="1.0" encoding="UTF-8"\?>', '', reply))
            hostname_ele = etree_find(resp.strip(), 'host-name')
            device_info['network_os_hostname'] = hostname_ele.text if hostname_ele is not None else None
        except Exception as exc:
            self._connection.queue_message('vvvv', 'Fail to retrieve device info %s' % exc)
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
        """
        Guess the remote network os name
        :param obj: Netconf connection class object
        :return: Network OS name
        """
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
            if re.search('IOS-XR', c):
                guessed_os = 'iosxr'
                break

        m.close_session()
        return guessed_os

    # TODO: change .xml to .data_xml, when ncclient supports data_xml on all platforms
    def get(self, filter=None, remove_ns=False):
        if isinstance(filter, list):
            filter = tuple(filter)
        try:
            resp = self.m.get(filter=filter)
            if remove_ns:
                response = remove_namespaces(resp)
            else:
                response = resp.data_xml if hasattr(resp, 'data_xml') else resp.xml
            return response
        except RPCError as exc:
            raise Exception(to_xml(exc.xml))

    def get_config(self, source=None, filter=None, remove_ns=False):
        if isinstance(filter, list):
            filter = tuple(filter)
        try:
            resp = self.m.get_config(source=source, filter=filter)
            if remove_ns:
                response = remove_namespaces(resp)
            else:
                response = resp.data_xml if hasattr(resp, 'data_xml') else resp.xml
            return response
        except RPCError as exc:
            raise Exception(to_xml(exc.xml))

    def edit_config(self, config=None, format='xml', target='candidate', default_operation=None, test_option=None, error_option=None, remove_ns=False):
        if config is None:
            raise ValueError('config value must be provided')
        try:
            resp = self.m.edit_config(config, format=format, target=target, default_operation=default_operation, test_option=test_option,
                                      error_option=error_option)
            if remove_ns:
                response = remove_namespaces(resp)
            else:
                response = resp.data_xml if hasattr(resp, 'data_xml') else resp.xml
            return response
        except RPCError as exc:
            raise Exception(to_xml(exc.xml))

    def commit(self, confirmed=False, timeout=None, persist=None, remove_ns=False):
        timeout = to_text(timeout, errors='surrogate_or_strict')

        try:
            resp = self.m.commit(confirmed=confirmed, timeout=timeout, persist=persist)
            if remove_ns:
                response = remove_namespaces(resp)
            else:
                response = resp.data_xml if hasattr(resp, 'data_xml') else resp.xml
            return response
        except RPCError as exc:
            raise Exception(to_xml(exc.xml))

    def validate(self, source="candidate", remove_ns=False):
        try:
            resp = self.m.validate(source=source)
            if remove_ns:
                response = remove_namespaces(resp)
            else:
                response = resp.data_xml if hasattr(resp, 'data_xml') else resp.xml
            return response
        except RPCError as exc:
            raise Exception(to_xml(exc.xml))

    def discard_changes(self, remove_ns=False):
        try:
            resp = self.m.discard_changes()
            if remove_ns:
                response = remove_namespaces(resp)
            else:
                response = resp.data_xml if hasattr(resp, 'data_xml') else resp.xml
            return response
        except RPCError as exc:
            raise Exception(to_xml(exc.xml))
