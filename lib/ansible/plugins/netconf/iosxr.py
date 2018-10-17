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

import json
import re
import collections

from ansible import constants as C
from ansible.module_utils.network.common.netconf import remove_namespaces
from ansible.module_utils.network.iosxr.iosxr import build_xml, etree_find
from ansible.errors import AnsibleConnectionFailure, AnsibleError
from ansible.plugins.netconf import NetconfBase
from ansible.plugins.netconf import ensure_connected

try:
    from ncclient import manager
    from ncclient.operations import RPCError
    from ncclient.transport.errors import SSHUnknownHostError
    from ncclient.xml_ import to_ele, to_xml, new_ele
except ImportError:
    raise AnsibleError("ncclient is not installed")

try:
    from lxml import etree
except ImportError:
    raise AnsibleError("lxml is not installed")


class Netconf(NetconfBase):

    @ensure_connected
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

        reply = self.get(install_filter)
        ele_boot_variable = etree_find(reply, 'boot-variable/boot-variable')
        if ele_boot_variable is not None:
            device_info['network_os_image'] = re.split('[:|,]', ele_boot_variable.text)[1]
        ele_package_name = etree_find(reply, 'package-name')
        if ele_package_name is not None:
            device_info['network_os_package'] = ele_package_name.text
            device_info['network_os_version'] = re.split('-', ele_package_name.text)[-1]

        hostname_filter = build_xml('host-names', opcode='filter')

        reply = self.get(hostname_filter)
        hostname_ele = etree_find(reply, 'host-name')
        device_info['network_os_hostname'] = hostname_ele.text if hostname_ele is not None else None

        return device_info

    def get_capabilities(self):
        result = dict()
        result['rpc'] = self.get_base_rpc() + ['commit', 'discard_changes', 'validate', 'lock', 'unlock', 'get-schema']
        result['network_api'] = 'netconf'
        result['device_info'] = self.get_device_info()
        result['server_capabilities'] = [c for c in self.m.server_capabilities]
        result['client_capabilities'] = [c for c in self.m.client_capabilities]
        result['session_id'] = self.m.session_id
        result['device_operations'] = self.get_device_operations(result['server_capabilities'])
        return json.dumps(result)

    @staticmethod
    def guess_network_os(obj):

        try:
            m = manager.connect(
                host=obj._play_context.remote_addr,
                port=obj._play_context.port or 830,
                username=obj._play_context.remote_user,
                password=obj._play_context.password,
                key_filename=obj._play_context.private_key_file,
                hostkey_verify=C.HOST_KEY_CHECKING,
                look_for_keys=C.PARAMIKO_LOOK_FOR_KEYS,
                allow_agent=obj._play_context.allow_agent,
                timeout=obj._play_context.timeout
            )
        except SSHUnknownHostError as exc:
            raise AnsibleConnectionFailure(str(exc))

        guessed_os = None
        for c in m.server_capabilities:
            if re.search('IOS-XR', c):
                guessed_os = 'iosxr'
                break

        m.close_session()
        return guessed_os

    # TODO: change .xml to .data_xml, when ncclient supports data_xml on all platforms
    @ensure_connected
    def get(self, filter=None):
        if isinstance(filter, list):
            filter = tuple(filter)
        try:
            response = self.m.get(filter=filter)
            return remove_namespaces(response)
        except RPCError as exc:
            raise Exception(to_xml(exc.xml))

    @ensure_connected
    def get_config(self, source=None, filter=None):
        if isinstance(filter, list):
            filter = tuple(filter)
        try:
            response = self.m.get_config(source=source, filter=filter)
            return remove_namespaces(response)
        except RPCError as exc:
            raise Exception(to_xml(exc.xml))

    @ensure_connected
    def edit_config(self, *args, **kwargs):
        try:
            response = self.m.edit_config(*args, **kwargs)
            return remove_namespaces(response)
        except RPCError as exc:
            raise Exception(to_xml(exc.xml))

    @ensure_connected
    def commit(self, *args, **kwargs):
        try:
            response = self.m.commit(*args, **kwargs)
            return remove_namespaces(response)
        except RPCError as exc:
            raise Exception(to_xml(exc.xml))

    @ensure_connected
    def validate(self, *args, **kwargs):
        try:
            response = self.m.validate(*args, **kwargs)
            return remove_namespaces(response)
        except RPCError as exc:
            raise Exception(to_xml(exc.xml))

    @ensure_connected
    def discard_changes(self):
        try:
            response = self.m.discard_changes()
            return remove_namespaces(response)
        except RPCError as exc:
            raise Exception(to_xml(exc.xml))
