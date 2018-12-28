#
# (c) 2017 Red Hat, Inc.
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

import re
import json

from contextlib import contextmanager
from ansible.module_utils.six import iteritems
from ansible.module_utils.connection import Connection, ConnectionError

from ansible.module_utils.basic import env_fallback, return_values
from ansible.module_utils.network.common.netconf import NetconfConnection
from ansible.module_utils._text import to_text
from ansible.module_utils.network.common.utils import to_list, ComplexList

try:
    from lxml.etree import Element, SubElement, tostring as xml_to_string
    HAS_LXML = True
except ImportError:
    from xml.etree.ElementTree import Element, SubElement, tostring as xml_to_string
    HAS_LXML = False

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

try:
    from ncclient.xml_ import to_xml
    HAS_NCCLIENT = True
except ImportError:
    HAS_NCCLIENT = False

_DEVICE_CLI_CONNECTION = None
_DEVICE_NC_CONNECTION = None
ACTIONS = frozenset(['merge', 'override', 'replace', 'update', 'set'])
NE_ACTIONS = frozenset(['merge', 'override', 'update'])
FORMATS = frozenset(['xml', 'text', 'json'])
CONFIG_FORMATS = frozenset(['xml', 'text', 'json', 'set'])


ne_provider_spec = {
    'host': dict(),
    'port': dict(type='int'),
    'username': dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
    'password': dict(fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD']), no_log=True),
    'ssh_keyfile': dict(fallback=(env_fallback, ['ANSIBLE_NET_SSH_KEYFILE']), type='path'),
    'timeout': dict(type='int'),
    'transport': dict(default='cli', choices=['cli', 'netconf'])
}
ne_argument_spec = {
    'provider': dict(type='dict', options=ne_provider_spec),
}
ne_top_spec = {
    'host': dict(removed_in_version=2.9),
    'port': dict(removed_in_version=2.9, type='int'),
    'username': dict(removed_in_version=2.9),
    'password': dict(removed_in_version=2.9, no_log=True),
    'ssh_keyfile': dict(removed_in_version=2.9, type='path'),
    'timeout': dict(removed_in_version=2.9, type='int'),
    'transport': dict(removed_in_version=2.9, choices=['cli', 'netconf'])
}
ne_argument_spec.update(ne_top_spec)


def get_provider_argspec():
    return ne_provider_spec


def to_string(data):
    return re.sub(r'<data.+?(/>|>)', r'<data\1', data)


def get_connection(module):
    if hasattr(module, '_ne_connection'):
        return module._ne_connection
    capabilities = get_capabilities(module)
    network_api = capabilities.get('network_api')

    if network_api == 'cliconf':
        module._ne_connection = Connection(module._socket_path)
    elif network_api == 'netconf':
        module._ne_connection = NetconfConnection(module._socket_path)
    else:
        module.fail_json(msg='Invalid connection type %s' % network_api)
    return module._ne_connection


def get_capabilities(module):
    if hasattr(module, '_ne_capabilities'):
        return module._ne_capabilities

    capabilities = Connection(module._socket_path).get_capabilities()
    module._ne_capabilities = json.loads(capabilities)
    return module._ne_capabilities


def lock_configuration(x):
    conn = get_connection(x)
    return conn.lock()


def unlock_configuration(x):
    conn = get_connection(x)
    return conn.unlock()


@contextmanager
def locked_config(module):
    try:
        lock_configuration(module)
        yield
    finally:
        unlock_configuration(module)


def get_param(module, key):
    if module.params.get(key):
        value = module.params[key]
    elif module.params.get('provider'):
        value = module.params['provider'].get(key)
    else:
        value = None
    return value


def discard_changes(module):
    conn = get_connection(module)
    return conn.discard_changes()


def load_params(module):
    """load_params"""

    provider = module.params.get('provider') or dict()
    for key, value in iteritems(provider):
        if key in ne_argument_spec:
            if module.params.get(key) is None and value is not None:
                module.params[key] = value


def get_configuration(module, format='xml', filter=None):
    if format not in CONFIG_FORMATS:
        module.fail_json(msg='invalid config format specified')

    conn = get_connection(module)
    reply = conn.get_configuration(format=format, filter=filter)

    return reply


def get_nc_connection(module):
    """ get_config """

    conn = get_connection(module)
    return conn


def set_nc_config(module, xml_str, *args, **kwargs):
    """ set_config """

    conn = get_nc_connection(module)
    if xml_str is not None:
        try:
            out = conn.edit_config(target='running', config=xml_str, default_operation='merge',
                                   error_option='rollback-on-error')
        finally:
            pass
    else:
        return None
    return to_string(to_xml(out))


def get_config(module, flags=None):
    global _DEVICE_CONFIGS

    if _DEVICE_CONFIGS != {}:
        return _DEVICE_CONFIGS
    else:
        connection = get_connection(module)
        out = connection.get_config()
        cfg = to_text(out, errors='surrogate_then_replace').strip()
        _DEVICE_CONFIGS = cfg
        return cfg


def get_nc_config(module, xml_str, *args, **kwargs):
    """ get_config """

    conn = get_nc_connection(module)
    if xml_str is not None:
        try:
            response = conn.get(xml_str)
        finally:
            pass
    else:
        return None
    return to_string(to_xml(response))


def execute_nc_action(module, xml_str, *args, **kwargs):
    """ huawei execute-action """

    conn = get_nc_connection(module)
    if xml_str is not None:
        try:
            response = conn.dispatch(xml_str)
        finally:
            pass
    else:
        return None
    return to_string(to_xml(response))


def execute_nc_action_yang(module, xml_str, *args, **kwargs):
    """ huawei execute-action_yang """
    conn = get_nc_connection(module)
    if xml_str is not None:
        try:
            response = conn.dispatch(xml_str)
        finally:
            pass
    else:
        return None
    return to_string(to_xml(response))


def execute_nc_cli(module, xml_str, *args, **kwargs):
    """ huawei execute-cli """

    conn = get_nc_connection(module)
    return conn.execute_cli(xml_str)


def check_args(module, warnings):
    """check_args"""

    pass


def run_commands(module, commands):
    responses = list()
    connection = get_connection(module)

    for cmd in to_list(commands):
        out = connection.get(**cmd)

        try:
            out = to_text(out, errors='surrogate_or_strict')
        except UnicodeError:
            module.fail_json(msg=u'Failed to decode output from %s: %s' % (cmd, to_text(out)))
        responses.append(cmd)
        responses.append(out)

    return responses


def to_commands(module, commands):
    spec = {
        'command': dict(key=True),
        'prompt': dict(),
        'answer': dict()
    }
    transform = ComplexList(spec, module)
    return transform(commands)


NE_COMMON_XML_OPERATION_MERGE = "merge"
NE_COMMON_XML_OPERATION_CREATE = "create"
NE_COMMON_XML_OPERATION_DELETE = "delete"


def constr_leaf_value(xml_str, leafName, leafValue):
    """construct the leaf update string"""

    if leafValue is not None:
        xml_str += "<" + leafName + ">"
        xml_str += "%s" % leafValue
        xml_str += "</" + leafName + ">\r\n"
    return xml_str


def constr_leaf_novalue(xml_str, leafName):
    """onstruct the leaf update string"""

    xml_str += "<" + leafName + "></" + leafName + ">\r\n"
    return xml_str


def constr_container_head(xml_str, container):
    """construct the container update string head  """
    xml_str += "<" + container + ">\r\n"
    return xml_str


def constr_container_tail(xml_str, container):
    """construct the container update string tail  """
    xml_str += "</" + container + ">\r\n"
    return xml_str


def constr_container_process_head(xml_str, container, operation):
    """construct the container update string process  """
    xml_str += "<" + container + "s>\r\n"
    xml_str += "<" + container + " xc:operation=\"" + operation + "\">\r\n"
    return xml_str


def constr_container_process_tail(xml_str, container):
    """construct the container update string process  """
    xml_str += "</" + container + ">\r\n"
    xml_str += "</" + container + "s>\r\n"
    return xml_str
