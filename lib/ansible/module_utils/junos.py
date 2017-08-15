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
ARGS_DEFAULT_VALUE = {}


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
    # if warning is received from device diff is empty.
    if isinstance(reply, list):
        return None

    output = reply.find('.//configuration-output')
    if output is not None:
        return to_text(output.text, encoding='latin1').strip()


def load_config(module, candidate, warnings, action='merge', format='xml'):

    if not candidate:
        return

    if isinstance(candidate, list):
        candidate = '\n'.join(candidate)

    reply = load_configuration(module, candidate, action=action, format=format)
    if isinstance(reply, list):
        warnings.extend(reply)

    validate(module)

    return get_diff(module)


def get_param(module, key):
    return module.params[key] or module.params['provider'].get(key)


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
