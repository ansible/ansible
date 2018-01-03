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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import re

from ansible import constants as C
from ansible.module_utils._text import to_text, to_bytes
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


class Netconf(NetconfBase):

    def get_text(self, ele, tag):
        try:
            return to_text(ele.find(tag).text, errors='surrogate_then_replace').strip()
        except AttributeError:
            pass

    def get_device_info(self):
        device_info = dict()
        device_info['network_os'] = 'default'
        return device_info

    #@ensure_connected
    #def execute_rpc(self, name):
    #    """RPC to be execute on remote device
    #       :name: Name of rpc in string format"""
    #    try:
    #        obj = to_ele(to_bytes(name, errors='surrogate_or_strict'))
    #        return self.m.rpc(obj).data_xml
    #    except RPCError as exc:
    #        raise Exception(to_xml(exc.xml))

    def get_capabilities(self):
        result = dict()
        result['rpc'] = self.get_base_rpc() + ['commit', 'discard_changes', 'validate', 'lock', 'unlock', 'copy_copy',
                                               'execute_rpc', 'load_configuration', 'get_configuration', 'command',
                                               'reboot', 'halt']
        result['network_api'] = 'netconf'
        result['device_info'] = self.get_device_info()
        result['server_capabilities'] = [c for c in self.m.server_capabilities]
        result['client_capabilities'] = [c for c in self.m.client_capabilities]
        result['session_id'] = self.m.session_id
        return json.dumps(result)

    #def __getattr__(self, name):
    #    try:
    #        return getattr(self, m, name)(*args, **kwargs).data_xml
    #        return partial(self.__rpc__, name)
    #    except RPCError as exc:
    #        raise Exception(to_xml(exc.xml))

    #        return self.__dict__[name]
    #    except KeyError:
    #        if name.startswith('_'):
    #            raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, name))
    #        return partial(self.__rpc__, name)


