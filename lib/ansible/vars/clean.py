# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import re

from collections.abc import MutableMapping, MutableSequence

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.module_utils import six
from ansible.module_utils._text import to_text
from ansible.plugins.loader import connection_loader
from ansible.utils.display import Display

display = Display()


def module_response_deepcopy(v):
    """Function to create a deep copy of module response data

    Designed to be used within the Ansible "engine" to improve performance
    issues where ``copy.deepcopy`` was used previously, largely with CPU
    and memory contention.

    This only supports the following data types, and was designed to only
    handle specific workloads:

    * ``dict``
    * ``list``

    The data we pass here will come from a serialization such
    as JSON, so we shouldn't have need for other data types such as
    ``set`` or ``tuple``.

    Take note that this function should not be used extensively as a
    replacement for ``deepcopy`` due to the naive way in which this
    handles other data types.

    Do not expect uses outside of those listed below to maintain
    backwards compatibility, in case we need to extend this function
    to handle our specific needs:

    * ``ansible.executor.task_result.TaskResult.clean_copy``
    * ``ansible.vars.clean.clean_facts``
    * ``ansible.vars.namespace_facts``
    """
    if isinstance(v, dict):
        ret = v.copy()
        items = six.iteritems(ret)
    elif isinstance(v, list):
        ret = v[:]
        items = enumerate(ret)
    else:
        return v

    for key, value in items:
        if isinstance(value, (dict, list)):
            ret[key] = module_response_deepcopy(value)
        else:
            ret[key] = value

    return ret


def strip_internal_keys(dirty, exceptions=None):
    # All keys starting with _ansible_ are internal, so change the 'dirty' mapping and remove them.

    if exceptions is None:
        exceptions = tuple()

    if isinstance(dirty, MutableSequence):

        for element in dirty:
            if isinstance(element, (MutableMapping, MutableSequence)):
                strip_internal_keys(element, exceptions=exceptions)

    elif isinstance(dirty, MutableMapping):

        # listify to avoid updating dict while iterating over it
        for k in list(dirty.keys()):
            if isinstance(k, six.string_types):
                if k.startswith('_ansible_') and k not in exceptions:
                    del dirty[k]
                    continue

            if isinstance(dirty[k], (MutableMapping, MutableSequence)):
                strip_internal_keys(dirty[k], exceptions=exceptions)
    else:
        raise AnsibleError("Cannot strip invalid keys from %s" % type(dirty))

    return dirty


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

    # cleanse fact values that are allowed from actions but not modules
    for key in list(data.get('ansible_facts', {}).keys()):
        if key.startswith('discovered_interpreter_') or key.startswith('ansible_discovered_interpreter_'):
            del data['ansible_facts'][key]


def clean_facts(facts):
    ''' remove facts that can override internal keys or otherwise deemed unsafe '''
    data = module_response_deepcopy(facts)

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
        conn_name = os.path.splitext(os.path.basename(conn_path))[0]
        re_key = re.compile('^ansible_%s_' % re.escape(conn_name))
        for fact_key in fact_keys:
            # most lightweight VM or container tech creates devices with this pattern, this avoids filtering them out
            if (re_key.match(fact_key) and not fact_key.endswith(('_bridge', '_gwbridge'))) or fact_key.startswith('ansible_become_'):
                remove_keys.add(fact_key)

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
            display.warning("Removed restricted key from module data: %s" % (r_key))
            del data[r_key]

    return strip_internal_keys(data)


def namespace_facts(facts):
    ''' return all facts inside 'ansible_facts' w/o an ansible_ prefix '''
    deprefixed = {}
    for k in facts:
        if k.startswith('ansible_') and k not in ('ansible_local',):
            deprefixed[k[8:]] = module_response_deepcopy(facts[k])
        else:
            deprefixed[k] = module_response_deepcopy(facts[k])

    return {'ansible_facts': deprefixed}
