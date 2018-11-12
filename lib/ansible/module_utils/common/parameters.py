# -*- coding: utf-8 -*-
# Copyright (c) 2018 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.common._collections_compat import (
    KeysView,
    Sequence,
)

from ansible.module_utils.six import (
    binary_type,
    text_type,
)

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

# Note: When getting Sequence from collections, it matches with strings. If
# this matters, make sure to check for strings before checking for sequencetype
SEQUENCETYPE = frozenset, KeysView, Sequence


def handle_aliases(params, argument_spec, legal_inputs=None, spec=None, param=None):
    if legal_inputs is None:
        legal_inputs = ['_ansible_%s' % k for k in PASS_VARS]
    # this uses exceptions as it happens before we can safely call fail_json
    aliases_results = {}  # alias:canon
    if param is None:
        param = params

    if spec is None:
        spec = argument_spec
    for (k, v) in spec.items():
        legal_inputs.append(k)
        aliases = v.get('aliases', None)
        default = v.get('default', None)
        required = v.get('required', False)
        if default is not None and required:
            # not alias specific but this is a good place to check this
            raise Exception("internal error: required and default are mutually exclusive for %s" % k)
        if aliases is None:
            continue
        if not isinstance(aliases, SEQUENCETYPE) or isinstance(aliases, (binary_type, text_type)):
            raise Exception('internal error: aliases must be a list or tuple')
        for alias in aliases:
            legal_inputs.append(alias)
            aliases_results[alias] = k
            if alias in param:
                param[k] = param[alias]

    return aliases_results
