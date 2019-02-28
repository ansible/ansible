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

PASS_VARS = {
    'check_mode': 'check_mode',
    'debug': '_debug',
    'diff': '_diff',
    'keep_remote_files': '_keep_remote_files',
    'module_name': '_name',
    'no_log': 'no_log',
    'remote_tmp': '_remote_tmp',
    'selinux_special_fs': '_selinux_special_fs',
    'shell_executable': '_shell',
    'socket': '_socket_path',
    'string_conversion_action': '_string_conversion_action',
    'syslog_facility': '_syslog_facility',
    'tmpdir': '_tmpdir',
    'verbosity': '_verbosity',
    'version': 'ansible_version',
}


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
