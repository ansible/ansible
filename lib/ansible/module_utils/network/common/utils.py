# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2016 Red Hat Inc.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

# Networking tools for network modules only

import re
import ast
import operator
import socket
import json

from itertools import chain
from socket import inet_aton
from json import dumps

from ansible.module_utils._text import to_text, to_bytes
from ansible.module_utils.common._collections_compat import Mapping
from ansible.module_utils.six import iteritems, string_types
from ansible.module_utils import basic
from ansible.module_utils.parsing.convert_bool import boolean

# Backwards compatibility for 3rd party modules
from ansible.module_utils.common.network import (
    to_bits, is_netmask, is_masklen, to_netmask, to_masklen, to_subnet, to_ipv6_network, VALID_MASKS
)

try:
    from jinja2 import Environment, StrictUndefined
    from jinja2.exceptions import UndefinedError
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False


OPERATORS = frozenset(['ge', 'gt', 'eq', 'neq', 'lt', 'le'])
ALIASES = frozenset([('min', 'ge'), ('max', 'le'), ('exactly', 'eq'), ('neq', 'ne')])


def to_list(val):
    if isinstance(val, (list, tuple, set)):
        return list(val)
    elif val is not None:
        return [val]
    else:
        return list()


def to_lines(stdout):
    for item in stdout:
        if isinstance(item, string_types):
            item = to_text(item).split('\n')
        yield item


def transform_commands(module):
    transform = ComplexList(dict(
        command=dict(key=True),
        output=dict(),
        prompt=dict(type='list'),
        answer=dict(type='list'),
        newline=dict(type='bool', default=True),
        sendonly=dict(type='bool', default=False),
        check_all=dict(type='bool', default=False),
    ), module)

    return transform(module.params['commands'])


def sort_list(val):
    if isinstance(val, list):
        return sorted(val)
    return val


class Entity(object):
    """Transforms a dict to with an argument spec

    This class will take a dict and apply an Ansible argument spec to the
    values.  The resulting dict will contain all of the keys in the param
    with appropriate values set.

    Example::

        argument_spec = dict(
            command=dict(key=True),
            display=dict(default='text', choices=['text', 'json']),
            validate=dict(type='bool')
        )
        transform = Entity(module, argument_spec)
        value = dict(command='foo')
        result = transform(value)
        print result
        {'command': 'foo', 'display': 'text', 'validate': None}

    Supported argument spec:
        * key - specifies how to map a single value to a dict
        * read_from - read and apply the argument_spec from the module
        * required - a value is required
        * type - type of value (uses AnsibleModule type checker)
        * fallback - implements fallback function
        * choices - set of valid options
        * default - default value
    """

    def __init__(self, module, attrs=None, args=None, keys=None, from_argspec=False):
        args = [] if args is None else args

        self._attributes = attrs or {}
        self._module = module

        for arg in args:
            self._attributes[arg] = dict()
            if from_argspec:
                self._attributes[arg]['read_from'] = arg
            if keys and arg in keys:
                self._attributes[arg]['key'] = True

        self.attr_names = frozenset(self._attributes.keys())

        _has_key = False

        for name, attr in iteritems(self._attributes):
            if attr.get('read_from'):
                if attr['read_from'] not in self._module.argument_spec:
                    module.fail_json(msg='argument %s does not exist' % attr['read_from'])
                spec = self._module.argument_spec.get(attr['read_from'])
                for key, value in iteritems(spec):
                    if key not in attr:
                        attr[key] = value

            if attr.get('key'):
                if _has_key:
                    module.fail_json(msg='only one key value can be specified')
                _has_key = True
                attr['required'] = True

    def serialize(self):
        return self._attributes

    def to_dict(self, value):
        obj = {}
        for name, attr in iteritems(self._attributes):
            if attr.get('key'):
                obj[name] = value
            else:
                obj[name] = attr.get('default')
        return obj

    def __call__(self, value, strict=True):
        if not isinstance(value, dict):
            value = self.to_dict(value)

        if strict:
            unknown = set(value).difference(self.attr_names)
            if unknown:
                self._module.fail_json(msg='invalid keys: %s' % ','.join(unknown))

        for name, attr in iteritems(self._attributes):
            if value.get(name) is None:
                value[name] = attr.get('default')

            if attr.get('fallback') and not value.get(name):
                fallback = attr.get('fallback', (None,))
                fallback_strategy = fallback[0]
                fallback_args = []
                fallback_kwargs = {}
                if fallback_strategy is not None:
                    for item in fallback[1:]:
                        if isinstance(item, dict):
                            fallback_kwargs = item
                        else:
                            fallback_args = item
                    try:
                        value[name] = fallback_strategy(*fallback_args, **fallback_kwargs)
                    except basic.AnsibleFallbackNotFound:
                        continue

            if attr.get('required') and value.get(name) is None:
                self._module.fail_json(msg='missing required attribute %s' % name)

            if 'choices' in attr:
                if value[name] not in attr['choices']:
                    self._module.fail_json(msg='%s must be one of %s, got %s' % (name, ', '.join(attr['choices']), value[name]))

            if value[name] is not None:
                value_type = attr.get('type', 'str')
                type_checker = self._module._CHECK_ARGUMENT_TYPES_DISPATCHER[value_type]
                type_checker(value[name])
            elif value.get(name):
                value[name] = self._module.params[name]

        return value


class EntityCollection(Entity):
    """Extends ```Entity``` to handle a list of dicts """

    def __call__(self, iterable, strict=True):
        if iterable is None:
            iterable = [super(EntityCollection, self).__call__(self._module.params, strict)]

        if not isinstance(iterable, (list, tuple)):
            self._module.fail_json(msg='value must be an iterable')

        return [(super(EntityCollection, self).__call__(i, strict)) for i in iterable]


# these two are for backwards compatibility and can be removed once all of the
# modules that use them are updated
class ComplexDict(Entity):
    def __init__(self, attrs, module, *args, **kwargs):
        super(ComplexDict, self).__init__(module, attrs, *args, **kwargs)


class ComplexList(EntityCollection):
    def __init__(self, attrs, module, *args, **kwargs):
        super(ComplexList, self).__init__(module, attrs, *args, **kwargs)


def dict_diff(base, comparable):
    """ Generate a dict object of differences

    This function will compare two dict objects and return the difference
    between them as a dict object.  For scalar values, the key will reflect
    the updated value.  If the key does not exist in `comparable`, then then no
    key will be returned.  For lists, the value in comparable will wholly replace
    the value in base for the key.  For dicts, the returned value will only
    return keys that are different.

    :param base: dict object to base the diff on
    :param comparable: dict object to compare against base

    :returns: new dict object with differences
    """
    if not isinstance(base, dict):
        raise AssertionError("`base` must be of type <dict>")
    if not isinstance(comparable, dict):
        if comparable is None:
            comparable = dict()
        else:
            raise AssertionError("`comparable` must be of type <dict>")

    updates = dict()

    for key, value in iteritems(base):
        if isinstance(value, dict):
            item = comparable.get(key)
            if item is not None:
                sub_diff = dict_diff(value, comparable[key])
                if sub_diff:
                    updates[key] = sub_diff
        else:
            comparable_value = comparable.get(key)
            if comparable_value is not None:
                if sort_list(base[key]) != sort_list(comparable_value):
                    updates[key] = comparable_value

    for key in set(comparable.keys()).difference(base.keys()):
        updates[key] = comparable.get(key)

    return updates


def dict_merge(base, other):
    """ Return a new dict object that combines base and other

    This will create a new dict object that is a combination of the key/value
    pairs from base and other.  When both keys exist, the value will be
    selected from other.  If the value is a list object, the two lists will
    be combined and duplicate entries removed.

    :param base: dict object to serve as base
    :param other: dict object to combine with base

    :returns: new combined dict object
    """
    if not isinstance(base, dict):
        raise AssertionError("`base` must be of type <dict>")
    if not isinstance(other, dict):
        raise AssertionError("`other` must be of type <dict>")

    combined = dict()

    for key, value in iteritems(base):
        if isinstance(value, dict):
            if key in other:
                item = other.get(key)
                if item is not None:
                    if isinstance(other[key], Mapping):
                        combined[key] = dict_merge(value, other[key])
                    else:
                        combined[key] = other[key]
                else:
                    combined[key] = item
            else:
                combined[key] = value
        elif isinstance(value, list):
            if key in other:
                item = other.get(key)
                if item is not None:
                    try:
                        combined[key] = list(set(chain(value, item)))
                    except TypeError:
                        value.extend([i for i in item if i not in value])
                        combined[key] = value
                else:
                    combined[key] = item
            else:
                combined[key] = value
        else:
            if key in other:
                other_value = other.get(key)
                if other_value is not None:
                    if sort_list(base[key]) != sort_list(other_value):
                        combined[key] = other_value
                    else:
                        combined[key] = value
                else:
                    combined[key] = other_value
            else:
                combined[key] = value

    for key in set(other.keys()).difference(base.keys()):
        combined[key] = other.get(key)

    return combined


def param_list_to_dict(param_list, unique_key="name", remove_key=True):
    """Rotates a list of dictionaries to be a dictionary of dictionaries.

    :param param_list: The aforementioned list of dictionaries
    :param unique_key: The name of a key which is present and unique in all of param_list's dictionaries. The value
    behind this key will be the key each dictionary can be found at in the new root dictionary
    :param remove_key: If True, remove unique_key from the individual dictionaries before returning.
    """
    param_dict = {}
    for params in param_list:
        params = params.copy()
        if remove_key:
            name = params.pop(unique_key)
        else:
            name = params.get(unique_key)
        param_dict[name] = params

    return param_dict


def conditional(expr, val, cast=None):
    match = re.match(r'^(.+)\((.+)\)$', str(expr), re.I)
    if match:
        op, arg = match.groups()
    else:
        op = 'eq'
        if ' ' in str(expr):
            raise AssertionError('invalid expression: cannot contain spaces')
        arg = expr

    if cast is None and val is not None:
        arg = type(val)(arg)
    elif callable(cast):
        arg = cast(arg)
        val = cast(val)

    op = next((oper for alias, oper in ALIASES if op == alias), op)

    if not hasattr(operator, op) and op not in OPERATORS:
        raise ValueError('unknown operator: %s' % op)

    func = getattr(operator, op)
    return func(val, arg)


def ternary(value, true_val, false_val):
    '''  value ? true_val : false_val '''
    if value:
        return true_val
    else:
        return false_val


def remove_default_spec(spec):
    for item in spec:
        if 'default' in spec[item]:
            del spec[item]['default']


def validate_ip_address(address):
    try:
        socket.inet_aton(address)
    except socket.error:
        return False
    return address.count('.') == 3


def validate_ip_v6_address(address):
    try:
        socket.inet_pton(socket.AF_INET6, address)
    except socket.error:
        return False
    return True


def validate_prefix(prefix):
    if prefix and not 0 <= int(prefix) <= 32:
        return False
    return True


def load_provider(spec, args):
    provider = args.get('provider', {})
    for key, value in iteritems(spec):
        if key not in provider:
            if key in args:
                provider[key] = args[key]
            elif 'fallback' in value:
                provider[key] = _fallback(value['fallback'])
            elif 'default' in value:
                provider[key] = value['default']
            else:
                provider[key] = None
    if 'authorize' in provider:
        # Coerce authorize to provider if a string has somehow snuck in.
        provider['authorize'] = boolean(provider['authorize'] or False)
    args['provider'] = provider
    return provider


def _fallback(fallback):
    strategy = fallback[0]
    args = []
    kwargs = {}

    for item in fallback[1:]:
        if isinstance(item, dict):
            kwargs = item
        else:
            args = item
    try:
        return strategy(*args, **kwargs)
    except basic.AnsibleFallbackNotFound:
        pass


def generate_dict(spec):
    """
    Generate dictionary which is in sync with argspec

    :param spec: A dictionary that is the argspec of the module
    :rtype: A dictionary
    :returns: A dictionary in sync with argspec with default value
    """
    obj = {}
    if not spec:
        return obj

    for key, val in iteritems(spec):
        if 'default' in val:
            dct = {key: val['default']}
        elif 'type' in val and val['type'] == 'dict':
            dct = {key: generate_dict(val['options'])}
        else:
            dct = {key: None}
        obj.update(dct)
    return obj


def parse_conf_arg(cfg, arg):
    """
    Parse config based on argument

    :param cfg: A text string which is a line of configuration.
    :param arg: A text string which is to be matched.
    :rtype: A text string
    :returns: A text string if match is found
    """
    match = re.search(r'%s (.+)(\n|$)' % arg, cfg, re.M)
    if match:
        result = match.group(1).strip()
    else:
        result = None
    return result


def parse_conf_cmd_arg(cfg, cmd, res1, res2=None, delete_str='no'):
    """
    Parse config based on command

    :param cfg: A text string which is a line of configuration.
    :param cmd: A text string which is the command to be matched
    :param res1: A text string to be returned if the command is present
    :param res2: A text string to be returned if the negate command
                 is present
    :param delete_str: A text string to identify the start of the
                 negate command
    :rtype: A text string
    :returns: A text string if match is found
    """
    match = re.search(r'\n\s+%s(\n|$)' % cmd, cfg)
    if match:
        return res1
    if res2 is not None:
        match = re.search(r'\n\s+%s %s(\n|$)' % (delete_str, cmd), cfg)
        if match:
            return res2
    return None


def get_xml_conf_arg(cfg, path, data='text'):
    """
    :param cfg: The top level configuration lxml Element tree object
    :param path: The relative xpath w.r.t to top level element (cfg)
           to be searched in the xml hierarchy
    :param data: The type of data to be returned for the matched xml node.
        Valid values are text, tag, attrib, with default as text.
    :return: Returns the required type for the matched xml node or else None
    """
    match = cfg.xpath(path)
    if len(match):
        if data == 'tag':
            result = getattr(match[0], 'tag')
        elif data == 'attrib':
            result = getattr(match[0], 'attrib')
        else:
            result = getattr(match[0], 'text')
    else:
        result = None
    return result


def remove_empties(cfg_dict):
    """
    Generate final config dictionary

    :param cfg_dict: A dictionary parsed in the facts system
    :rtype: A dictionary
    :returns: A dictionary by eliminating keys that have null values
    """
    final_cfg = {}
    if not cfg_dict:
        return final_cfg

    for key, val in iteritems(cfg_dict):
        dct = None
        if isinstance(val, dict):
            child_val = remove_empties(val)
            if child_val:
                dct = {key: child_val}
        elif (isinstance(val, list) and val
              and all([isinstance(x, dict) for x in val])):
            child_val = [remove_empties(x) for x in val]
            if child_val:
                dct = {key: child_val}
        elif val not in [None, [], {}, (), '']:
            dct = {key: val}
        if dct:
            final_cfg.update(dct)
    return final_cfg


def validate_config(spec, data):
    """
    Validate if the input data against the AnsibleModule spec format
    :param spec: Ansible argument spec
    :param data: Data to be validated
    :return:
    """
    params = basic._ANSIBLE_ARGS
    basic._ANSIBLE_ARGS = to_bytes(json.dumps({'ANSIBLE_MODULE_ARGS': data}))
    validated_data = basic.AnsibleModule(spec).params
    basic._ANSIBLE_ARGS = params
    return validated_data


def search_obj_in_list(name, lst, key='name'):
    for item in lst:
        if item[key] == name:
            return item
    return None


class Template:

    def __init__(self):
        if not HAS_JINJA2:
            raise ImportError("jinja2 is required but does not appear to be installed.  "
                              "It can be installed using `pip install jinja2`")

        self.env = Environment(undefined=StrictUndefined)
        self.env.filters.update({'ternary': ternary})

    def __call__(self, value, variables=None, fail_on_undefined=True):
        variables = variables or {}

        if not self.contains_vars(value):
            return value

        try:
            value = self.env.from_string(value).render(variables)
        except UndefinedError:
            if not fail_on_undefined:
                return None
            raise

        if value:
            try:
                return ast.literal_eval(value)
            except Exception:
                return str(value)
        else:
            return None

    def contains_vars(self, data):
        if isinstance(data, string_types):
            for marker in (self.env.block_start_string, self.env.variable_start_string, self.env.comment_start_string):
                if marker in data:
                    return True
        return False
