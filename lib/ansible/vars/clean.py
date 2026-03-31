# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import os
import re

from collections.abc import MutableMapping, Sequence, Mapping

from ansible import constants as C
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

    * ``ansible.executor.task_result._as_callback_task_result``
    * ``ansible.vars.clean.clean_facts``
    * ``ansible.vars.namespace_facts``
    """
    if isinstance(v, dict):
        ret = v.copy()
        items = ret.items()
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


def strip_internal_keys[T: Sequence | MutableMapping](dirty: T, exceptions: set[str] | frozenset[str] = frozenset()) -> T:
    """Recursively remove items from mappings whose keys start with `_ansible`, unless the key is in `exceptions`."""
    match dirty:
        case str():
            return dirty
        case Sequence():
            for element in dirty:
                strip_internal_keys(element, exceptions=exceptions)
        case MutableMapping():
            for key in list(dirty.keys()):
                if isinstance(key, str) and key.startswith('_ansible_') and key not in exceptions:
                    del dirty[key]
                else:
                    strip_internal_keys(dirty[key], exceptions=exceptions)

    return dirty


def clean_facts(facts: Mapping[str, object]):
    """ remove facts that can override internal keys or otherwise deemed unsafe """
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
    for hard in C.RESTRICTED_RESULT_KEYS:
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


def namespace_facts(facts: Mapping[str, object]) -> dict[str, object]:
    """ return all facts inside 'ansible_facts' w/o an ansible_ prefix """
    deprefixed = {}
    for k in facts:
        if k.startswith('ansible_') and k not in ('ansible_local',):
            deprefixed[k[8:]] = module_response_deepcopy(facts[k])
        else:
            deprefixed[k] = module_response_deepcopy(facts[k])

    return {'ansible_facts': deprefixed}
