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
import collections
import json
from contextlib import contextmanager
from copy import deepcopy

from ansible.module_utils.basic import env_fallback, return_values
from ansible.module_utils.connection import Connection, ConnectionError
from ansible.module_utils.network.common.netconf import NetconfConnection
from ansible.module_utils._text import to_text

try:
    from lxml.etree import Element, SubElement, tostring as xml_to_string
    HAS_LXML = True
except ImportError:
    from xml.etree.ElementTree import Element, SubElement, tostring as xml_to_string
    HAS_LXML = False

ACTIONS = frozenset(['merge', 'override', 'replace', 'update', 'set'])
JSON_ACTIONS = frozenset(['merge', 'override', 'update'])
FORMATS = frozenset(['xml', 'text', 'json'])
CONFIG_FORMATS = frozenset(['xml', 'text', 'json', 'set'])

junos_provider_spec = {
    'host': dict(),
    'port': dict(type='int'),
    'username': dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
    'password': dict(fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD']), no_log=True),
    'ssh_keyfile': dict(fallback=(env_fallback, ['ANSIBLE_NET_SSH_KEYFILE']), type='path'),
    'timeout': dict(type='int'),
    'transport': dict(default='netconf', choices=['cli', 'netconf'])
}
junos_argument_spec = {
    'provider': dict(type='dict', options=junos_provider_spec),
}
junos_top_spec = {
    'host': dict(removed_in_version=2.9),
    'port': dict(removed_in_version=2.9, type='int'),
    'username': dict(removed_in_version=2.9),
    'password': dict(removed_in_version=2.9, no_log=True),
    'ssh_keyfile': dict(removed_in_version=2.9, type='path'),
    'timeout': dict(removed_in_version=2.9, type='int'),
    'transport': dict(removed_in_version=2.9)
}
junos_argument_spec.update(junos_top_spec)


def tostring(element, encoding='UTF-8'):
    if HAS_LXML:
        return xml_to_string(element, encoding='unicode')
    else:
        return to_text(xml_to_string(element, encoding), encoding=encoding)


def get_provider_argspec():
    return junos_provider_spec


def get_connection(module):
    if hasattr(module, '_junos_connection'):
        return module._junos_connection

    capabilities = get_capabilities(module)
    network_api = capabilities.get('network_api')
    if network_api == 'cliconf':
        module._junos_connection = Connection(module._socket_path)
    elif network_api == 'netconf':
        module._junos_connection = NetconfConnection(module._socket_path)
    else:
        module.fail_json(msg='Invalid connection type %s' % network_api)

    return module._junos_connection


def get_capabilities(module):
    if hasattr(module, '_junos_capabilities'):
        return module._junos_capabilities

    try:
        capabilities = Connection(module._socket_path).get_capabilities()
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
    module._junos_capabilities = json.loads(capabilities)
    return module._junos_capabilities


def _validate_rollback_id(module, value):
    try:
        if not 0 <= int(value) <= 49:
            raise ValueError
    except ValueError:
        module.fail_json(msg='rollback must be between 0 and 49')


def load_configuration(module, candidate=None, action='merge', rollback=None, format='xml'):

    if all((candidate is None, rollback is None)):
        module.fail_json(msg='one of candidate or rollback must be specified')

    elif all((candidate is not None, rollback is not None)):
        module.fail_json(msg='candidate and rollback are mutually exclusive')

    if format not in FORMATS:
        module.fail_json(msg='invalid format specified')

    if format == 'json' and action not in JSON_ACTIONS:
        module.fail_json(msg='invalid action for format json')
    elif format in ('text', 'xml') and action not in ACTIONS:
        module.fail_json(msg='invalid action format %s' % format)
    if action == 'set' and not format == 'text':
        module.fail_json(msg='format must be text when action is set')

    conn = get_connection(module)
    try:
        if rollback is not None:
            _validate_rollback_id(module, rollback)
            obj = Element('load-configuration', {'rollback': str(rollback)})
            conn.execute_rpc(tostring(obj))
        else:
            return conn.load_configuration(config=candidate, action=action, format=format)
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))


def get_configuration(module, compare=False, format='xml', rollback='0', filter=None):
    if format not in CONFIG_FORMATS:
        module.fail_json(msg='invalid config format specified')

    conn = get_connection(module)
    try:
        if compare:
            xattrs = {'format': format}
            _validate_rollback_id(module, rollback)
            xattrs['compare'] = 'rollback'
            xattrs['rollback'] = str(rollback)
            reply = conn.execute_rpc(tostring(Element('get-configuration', xattrs)))
        else:
            reply = conn.get_configuration(format=format, filter=filter)
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
    return reply


def commit_configuration(module, confirm=False, check=False, comment=None, confirm_timeout=None, synchronize=False,
                         at_time=None, exit=False):
    conn = get_connection(module)
    try:
        if check:
            reply = conn.validate()
        else:
            reply = conn.commit(confirmed=confirm, timeout=confirm_timeout, comment=comment, synchronize=synchronize, at_time=at_time)
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
    return reply


def command(module, cmd, format='text', rpc_only=False):
    conn = get_connection(module)
    if rpc_only:
        cmd += ' | display xml rpc'
    try:
        response = conn.command(command=cmd, format=format)
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
    return response


def lock_configuration(module):
    conn = get_connection(module)
    try:
        response = conn.lock()
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
    return response


def unlock_configuration(module):
    conn = get_connection(module)
    try:
        response = conn.unlock()
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
    return response


@contextmanager
def locked_config(module):
    try:
        lock_configuration(module)
        yield
    finally:
        unlock_configuration(module)


def discard_changes(module):
    conn = get_connection(module)
    try:
        response = conn.discard_changes()
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
    return response


def get_diff(module, rollback='0'):
    reply = get_configuration(module, compare=True, format='text', rollback=rollback)
    # if warning is received from device diff is empty.
    if isinstance(reply, list):
        return None

    output = reply.find('.//configuration-output')
    if output is not None:
        return to_text(output.text, encoding='latin-1').strip()


def load_config(module, candidate, warnings, action='merge', format='xml'):
    get_connection(module)
    if not candidate:
        return

    if isinstance(candidate, list):
        candidate = '\n'.join(candidate)

    reply = load_configuration(module, candidate, action=action, format=format)
    if isinstance(reply, list):
        warnings.extend(reply)

    module._junos_connection.validate()
    return get_diff(module)


def get_param(module, key):
    if module.params.get(key):
        value = module.params[key]
    elif module.params.get('provider'):
        value = module.params['provider'].get(key)
    else:
        value = None
    return value


def map_params_to_obj(module, param_to_xpath_map, param=None):
    """
    Creates a new dictionary with key as xpath corresponding
    to param and value is a list of dict with metadata and values for
    the xpath.
    Acceptable metadata keys:
        'value': Value of param.
        'tag_only': Value is indicated by tag only in xml hierarchy.
        'leaf_only': If operation is to be added at leaf node only.
        'value_req': If value(text) is requried for leaf node.
        'is_key': If the field is key or not.
    eg: Output
    {
        'name': [{'value': 'ge-0/0/1'}]
        'disable': [{'value': True, tag_only': True}]
    }

    :param module:
    :param param_to_xpath_map: Modules params to xpath map
    :return: obj
    """
    if not param:
        param = module.params

    obj = collections.OrderedDict()
    for key, attribute in param_to_xpath_map.items():
        if key in param:
            is_attribute_dict = False

            value = param[key]
            if not isinstance(value, (list, tuple)):
                value = [value]

            if isinstance(attribute, dict):
                xpath = attribute.get('xpath')
                is_attribute_dict = True
            else:
                xpath = attribute

            if not obj.get(xpath):
                obj[xpath] = list()

            for val in value:
                if is_attribute_dict:
                    attr = deepcopy(attribute)
                    del attr['xpath']

                    attr.update({'value': val})
                    obj[xpath].append(attr)
                else:
                    obj[xpath].append({'value': val})
    return obj


def map_obj_to_ele(module, want, top, value_map=None, param=None):
    if not HAS_LXML:
        module.fail_json(msg='lxml is not installed.')

    if not param:
        param = module.params

    root = Element('root')
    top_ele = top.split('/')
    ele = SubElement(root, top_ele[0])

    if len(top_ele) > 1:
        for item in top_ele[1:-1]:
            ele = SubElement(ele, item)
    container = ele
    state = param.get('state')
    active = param.get('active')
    if active:
        oper = 'active'
    else:
        oper = 'inactive'

    # build xml subtree
    if container.tag != top_ele[-1]:
        node = SubElement(container, top_ele[-1])
    else:
        node = container

    for fxpath, attributes in want.items():
        for attr in attributes:
            tag_only = attr.get('tag_only', False)
            leaf_only = attr.get('leaf_only', False)
            value_req = attr.get('value_req', False)
            is_key = attr.get('is_key', False)
            parent_attrib = attr.get('parent_attrib', True)
            value = attr.get('value')
            field_top = attr.get('top')

            # operation 'delete' is added as element attribute
            # only if it is key or leaf only node
            if state == 'absent' and not (is_key or leaf_only):
                continue

            # convert param value to device specific value
            if value_map and fxpath in value_map:
                value = value_map[fxpath].get(value)

            if (value is not None) or tag_only or leaf_only:
                ele = node
                if field_top:
                    # eg: top = 'system/syslog/file'
                    #     field_top = 'system/syslog/file/contents'
                    # <file>
                    #   <name>test</name>
                    #   <contents>
                    #   </contents>
                    # </file>
                    ele_list = root.xpath(top + '/' + field_top)

                    if not len(ele_list):
                        fields = field_top.split('/')
                        ele = node
                        for item in fields:
                            inner_ele = root.xpath(top + '/' + item)
                            if len(inner_ele):
                                ele = inner_ele[0]
                            else:
                                ele = SubElement(ele, item)
                    else:
                        ele = ele_list[0]

                if value is not None and not isinstance(value, bool):
                    value = to_text(value, errors='surrogate_then_replace')

                if fxpath:
                    tags = fxpath.split('/')
                    for item in tags:
                        ele = SubElement(ele, item)

                if tag_only:
                    if state == 'present':
                        if not value:
                            # if value of tag_only node is false, delete the node
                            ele.set('delete', 'delete')

                elif leaf_only:
                    if state == 'present':
                        ele.set(oper, oper)
                        ele.text = value
                    else:
                        ele.set('delete', 'delete')
                        # Add value of leaf node if required while deleting.
                        # in some cases if value is present while deleting, it
                        # can result in error, hence the check
                        if value_req:
                            ele.text = value
                        if is_key:
                            par = ele.getparent()
                            par.set('delete', 'delete')
                else:
                    ele.text = value
                    par = ele.getparent()

                    if parent_attrib:
                        if state == 'present':
                            # set replace attribute at parent node
                            if not par.attrib.get('replace'):
                                par.set('replace', 'replace')

                            # set active/inactive at parent node
                            if not par.attrib.get(oper):
                                par.set(oper, oper)
                        else:
                            par.set('delete', 'delete')

    return root.getchildren()[0]


def to_param_list(module):
    aggregate = module.params.get('aggregate')
    if aggregate:
        if isinstance(aggregate, dict):
            return [aggregate]
        else:
            return aggregate
    else:
        return [module.params]
