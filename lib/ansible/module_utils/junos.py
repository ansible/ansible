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
from contextlib import contextmanager
from copy import deepcopy

from ansible.module_utils.basic import env_fallback, return_values
from ansible.module_utils.netconf import send_request, children
from ansible.module_utils.netconf import discard_changes, validate
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_text

try:
    from lxml.etree import Element, SubElement, fromstring, tostring
    HAS_LXML = True
except ImportError:
    from xml.etree.ElementTree import Element, SubElement, fromstring, tostring
    HAS_LXML = False

ACTIONS = frozenset(['merge', 'override', 'replace', 'update', 'set'])
JSON_ACTIONS = frozenset(['merge', 'override', 'update'])
FORMATS = frozenset(['xml', 'text', 'json'])
CONFIG_FORMATS = frozenset(['xml', 'text', 'json', 'set'])

junos_argument_spec = {
    'host': dict(),
    'port': dict(type='int'),
    'username': dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
    'password': dict(fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD']), no_log=True),
    'ssh_keyfile': dict(fallback=(env_fallback, ['ANSIBLE_NET_SSH_KEYFILE']), type='path'),
    'timeout': dict(type='int'),
    'provider': dict(type='dict'),
    'transport': dict()
}

# Add argument's default value here
ARGS_DEFAULT_VALUE = {
    'timeout': 10
}

OPERATION_LOOK_UP = {
    'absent': 'delete',
    'active': 'active',
    'suspend': 'inactive'
}


def get_argspec():
    return junos_argument_spec


def check_args(module, warnings):
    provider = module.params['provider'] or {}
    for key in junos_argument_spec:
        if key not in ('provider',) and module.params[key]:
            warnings.append('argument %s has been deprecated and will be '
                            'removed in a future version' % key)

    # set argument's default value if not provided in input
    # This is done to avoid unwanted argument deprecation warning
    # in case argument is not given as input (outside provider).
    for key in ARGS_DEFAULT_VALUE:
        if not module.params.get(key, None):
            module.params[key] = ARGS_DEFAULT_VALUE[key]

    if provider:
        for param in ('password',):
            if provider.get(param):
                module.no_log_values.update(return_values(provider[param]))


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

    if rollback is not None:
        _validate_rollback_id(module, rollback)
        xattrs = {'rollback': str(rollback)}
    else:
        xattrs = {'action': action, 'format': format}

    obj = Element('load-configuration', xattrs)

    if candidate is not None:
        lookup = {'xml': 'configuration', 'text': 'configuration-text',
                  'set': 'configuration-set', 'json': 'configuration-json'}

        if action == 'set':
            cfg = SubElement(obj, 'configuration-set')
        else:
            cfg = SubElement(obj, lookup[format])

        if isinstance(candidate, string_types):
            if format == 'xml':
                cfg.append(fromstring(candidate))
            else:
                cfg.text = to_text(candidate, encoding='latin1')
        else:
            cfg.append(candidate)
    return send_request(module, obj)


def get_configuration(module, compare=False, format='xml', rollback='0'):
    if format not in CONFIG_FORMATS:
        module.fail_json(msg='invalid config format specified')
    xattrs = {'format': format}
    if compare:
        _validate_rollback_id(module, rollback)
        xattrs['compare'] = 'rollback'
        xattrs['rollback'] = str(rollback)
    return send_request(module, Element('get-configuration', xattrs))


def commit_configuration(module, confirm=False, check=False, comment=None, confirm_timeout=None):
    obj = Element('commit-configuration')
    if confirm:
        SubElement(obj, 'confirmed')
    if check:
        SubElement(obj, 'check')
    if comment:
        subele = SubElement(obj, 'log')
        subele.text = str(comment)
    if confirm_timeout:
        subele = SubElement(obj, 'confirm-timeout')
        subele.text = str(confirm_timeout)
    return send_request(module, obj)


def command(module, command, format='text', rpc_only=False):
    xattrs = {'format': format}
    if rpc_only:
        command += ' | display xml rpc'
        xattrs['format'] = 'text'
    return send_request(module, Element('command', xattrs, text=command))


def lock_configuration(x):
    return send_request(x, Element('lock-configuration'))


def unlock_configuration(x):
    return send_request(x, Element('unlock-configuration'))


@contextmanager
def locked_config(module):
    try:
        lock_configuration(module)
        yield
    finally:
        unlock_configuration(module)


def get_diff(module):

    reply = get_configuration(module, compare=True, format='text')
    output = reply.find('.//configuration-output')
    if output is not None:
        return to_text(output.text, encoding='latin1').strip()


def load_config(module, candidate, warnings, action='merge', commit=False, format='xml',
                comment=None, confirm=False, confirm_timeout=None):

    if not candidate:
        return

    with locked_config(module):
        if isinstance(candidate, list):
            candidate = '\n'.join(candidate)

        reply = load_configuration(module, candidate, action=action, format=format)
        if isinstance(reply, list):
            warnings.extend(reply)

        validate(module)
        diff = get_diff(module)

        if diff:
            if commit:
                commit_configuration(module, confirm=confirm, comment=comment,
                                     confirm_timeout=confirm_timeout)
            else:
                discard_changes(module)

        return diff


def get_param(module, key):
    return module.params[key] or module.params['provider'].get(key)


def map_params_to_obj(module, param_to_xpath_map):
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
    obj = collections.OrderedDict()
    for key, attribute in param_to_xpath_map.items():
        if key in module.params:
            is_attribute_dict = False

            value = module.params[key]
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


def map_obj_to_ele(module, want, top, value_map=None):
    top_ele = top.split('/')
    root = Element(top_ele[0])
    ele = root

    if len(top_ele) > 1:
        for item in top_ele[1:-1]:
            ele = SubElement(ele, item)
    container = ele
    state = module.params.get('state')

    # build xml subtree
    for obj in want:
        oper = None
        if container.tag != top_ele[-1]:
            node = SubElement(container, top_ele[-1])
        else:
            node = container

        if state and state != 'present':
            oper = OPERATION_LOOK_UP.get(state)

        for xpath, attributes in obj.items():
            for attr in attributes:
                tag_only = attr.get('tag_only', False)
                leaf_only = attr.get('leaf_only', False)
                is_value = attr.get('value_req', False)
                is_key = attr.get('is_key', False)
                value = attr.get('value')

                # operation (delete/active/inactive) is added as element attribute
                # only if it is key or tag only or leaf only node
                if oper and not (is_key or tag_only or leaf_only):
                    continue

                # convert param value to device specific value
                if value_map and xpath in value_map:
                    value = value_map[xpath].get(value)

                if value or tag_only or (leaf_only and value):
                    ele = node
                    tags = xpath.split('/')
                    if value:
                        value = to_text(value, errors='surrogate_then_replace')

                    for item in tags:
                        ele = SubElement(ele, item)

                    if tag_only:
                        if not value:
                            ele.set('delete', 'delete')
                    elif leaf_only:
                        if oper:
                            ele.set(oper, oper)
                            if is_value:
                                ele.text = value
                        else:
                            ele.text = value
                    else:
                        ele.text = value
                        if HAS_LXML:
                            par = ele.getparent()
                        else:
                            module.fail_json(msg='lxml is not installed.')
                        if is_key and oper and not par.attrib.get(oper):
                            par.set(oper, oper)

    return root
