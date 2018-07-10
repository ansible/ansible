# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import re

from copy import deepcopy

from ansible import constants as C
from ansible.module_utils._text import to_text
from ansible.module_utils.six import string_types
from ansible.plugins.loader import connection_loader

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


def strip_internal_keys(dirty, exceptions=None):
    '''
    All keys starting with _ansible_ are internal, so create a copy of the 'dirty' dict
    and remove them from the clean one before returning it
    '''

    if exceptions is None:
        exceptions = ()
    clean = dirty.copy()
    for k in dirty.keys():
        if isinstance(k, string_types) and k.startswith('_ansible_'):
            if k not in exceptions:
                del clean[k]
        elif isinstance(dirty[k], dict):
            clean[k] = strip_internal_keys(dirty[k])
    return clean


def remove_internal_keys(data):
    '''
    More nuanced version of strip_internal_keys
    '''
    for key in list(data.keys()):
        if (key.startswith('_ansible_') and key != '_ansible_parsed') or key in C.INTERNAL_RESULT_KEYS:
            display.warning("Removed unexpected internal key in module return: %s = %s" % (key, data[key]))
            del data[key]

    # remove bad/empty internal keys
    for key in ['warnings', 'deprecations']:
        if key in data and not data[key]:
            del data[key]


def clean_facts(facts):
    ''' remove facts that can override internal keys or otherwise deemed unsafe '''
    data = deepcopy(facts)

    remove_keys = set()
    fact_keys = set(data.keys())
    # first we add all of our magic variable names to the set of
    # keys we want to remove from facts
    # NOTE: these will eventually disappear in favor of others below
    for magic_var in C.MAGIC_VARIABLE_MAPPING:
        remove_keys.update(fact_keys.intersection(C.MAGIC_VARIABLE_MAPPING[magic_var]))

    # remove common connection vars
    remove_keys.update(fact_keys.intersection(C.COMMON_CONNECTION_VARS))

    # next we remove any connection plugin specific vars
    for conn_path in connection_loader.all(path_only=True):
        try:
            conn_name = os.path.splitext(os.path.basename(conn_path))[0]
            re_key = re.compile('^ansible_%s_' % conn_name)
            for fact_key in fact_keys:
                # most lightweight VM or container tech creates devices with this pattern, this avoids filtering them out
                if (re_key.match(fact_key) and not fact_key.endswith(('_bridge', '_gwbridge'))) or re_key.startswith('ansible_become_'):
                    remove_keys.add(fact_key)
        except AttributeError:
            pass

    # remove some KNOWN keys
    for hard in C.RESTRICTED_RESULT_KEYS + C.INTERNAL_RESULT_KEYS:
        if hard in fact_keys:
            remove_keys.add(hard)

    # finally, we search for interpreter keys to remove
    re_interp = re.compile('^ansible_.*_interpreter$')
    for fact_key in fact_keys:
        if re_interp.match(fact_key):
            remove_keys.add(fact_key)
    # then we remove them (except for ssh host keys)
    for r_key in remove_keys:
        if not r_key.startswith('ansible_ssh_host_key_'):
            try:
                r_val = to_text(data[r_key])
                if len(r_val) > 24:
                    r_val = '%s ... %s' % (r_val[:13], r_val[-6:])
            except Exception:
                r_val = ' <failed to convert value to a string> '
            display.warning("Removed restricted key from module data: %s = %s" % (r_key, r_val))
            del data[r_key]

    return strip_internal_keys(data)


def namespace_facts(facts):
    ''' return all facts inside 'ansible_facts' w/o an ansible_ prefix '''
    deprefixed = {}
    for k in facts:
        if k in ('ansible_local',):
            # exceptions to 'deprefixing'
            deprefixed[k] = deepcopy(facts[k])
        else:
            deprefixed[k.replace('ansible_', '', 1)] = deepcopy(facts[k])

    return {'ansible_facts': deprefixed}
