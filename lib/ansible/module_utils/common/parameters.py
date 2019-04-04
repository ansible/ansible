# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils._text import to_native
from ansible.module_utils.common._collections_compat import Mapping
from ansible.module_utils.common.collections import is_iterable

from ansible.module_utils.six import (
    binary_type,
    integer_types,
    text_type,
)

# Python2 & 3 way to get NoneType
NoneType = type(None)

# if adding boolean attribute, also add to PASS_BOOL
# some of this dupes defaults from controller config
PASS_VARS = {
    'check_mode': ('check_mode', False),
    'debug': ('_debug', False),
    'diff': ('_diff', False),
    'keep_remote_files': ('_keep_remote_files', False),
    'module_name': ('_name', None),
    'no_log': ('no_log', False),
    'remote_tmp': ('_remote_tmp', None),
    'selinux_special_fs': ('_selinux_special_fs', ['fuse', 'nfs', 'vboxsf', 'ramfs', '9p']),
    'shell_executable': ('_shell', '/bin/sh'),
    'socket': ('_socket_path', None),
    'string_conversion_action': ('_string_conversion_action', 'warn'),
    'syslog_facility': ('_syslog_facility', 'INFO'),
    'tmpdir': ('_tmpdir', None),
    'verbosity': ('_verbosity', 0),
    'version': ('ansible_version', '0.0'),
}

PASS_BOOLS = ('check_mode', 'debug', 'diff', 'keep_remote_files', 'no_log')


def _return_datastructure_name(obj):
    """ Return native stringified values from datastructures.

    For use with removing sensitive values pre-jsonification."""
    if isinstance(obj, (text_type, binary_type)):
        if obj:
            yield to_native(obj, errors='surrogate_or_strict')
        return
    elif isinstance(obj, Mapping):
        for element in obj.items():
            for subelement in _return_datastructure_name(element[1]):
                yield subelement
    elif is_iterable(obj):
        for element in obj:
            for subelement in _return_datastructure_name(element):
                yield subelement
    elif isinstance(obj, (bool, NoneType)):
        # This must come before int because bools are also ints
        return
    elif isinstance(obj, tuple(list(integer_types) + [float])):
        yield to_native(obj, nonstring='simplerepr')
    else:
        raise TypeError('Unknown parameter type: %s, %s' % (type(obj), obj))


def list_no_log_values(argument_spec, params):
    """Return set of no log values

    :arg argument_spec: An argument spec dictionary from a module
    :arg params: Dictionary of all module parameters

    :returns: Set of strings that should be hidden from output::

        {'secret_dict_value', 'secret_list_item_one', 'secret_list_item_two', 'secret_string'}
    """

    no_log_values = set()
    for arg_name, arg_opts in argument_spec.items():
        if arg_opts.get('no_log', False):
            # Find the value for the no_log'd param
            no_log_object = params.get(arg_name, None)

            if no_log_object:
                no_log_values.update(_return_datastructure_name(no_log_object))

    return no_log_values


def list_deprecations(argument_spec, params):
    """Return a list of deprecations

    :arg argument_spec: An argument spec dictionary from a module
    :arg params: Dictionary of all module parameters

    :returns: List of dictionaries containing a message and version in which
        the deprecated parameter will be removed, or an empty list::

            [{'msg': "Param 'deptest' is deprecated. See the module docs for more information", 'version': '2.9'}]
    """

    deprecations = []
    for arg_name, arg_opts in argument_spec.items():
        if arg_opts.get('removed_in_version') is not None and arg_name in params:
            deprecations.append({
                'msg': "Param '%s' is deprecated. See the module docs for more information" % arg_name,
                'version': arg_opts.get('removed_in_version')
            })

    return deprecations


def handle_aliases(argument_spec, params):
    """Return a two item tuple. The first is a dictionary of aliases, the second is
    a list of legal inputs."""

    legal_inputs = ['_ansible_%s' % k for k in PASS_VARS]
    aliases_results = {}  # alias:canon

    for (k, v) in argument_spec.items():
        legal_inputs.append(k)
        aliases = v.get('aliases', None)
        default = v.get('default', None)
        required = v.get('required', False)
        if default is not None and required:
            # not alias specific but this is a good place to check this
            raise ValueError("internal error: required and default are mutually exclusive for %s" % k)
        if aliases is None:
            continue
        if not is_iterable(aliases) or isinstance(aliases, (binary_type, text_type)):
            raise TypeError('internal error: aliases must be a list or tuple')
        for alias in aliases:
            legal_inputs.append(alias)
            aliases_results[alias] = k
            if alias in params:
                params[k] = params[alias]

    return aliases_results, legal_inputs
