# (c) 2018 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils import six


def naive_deepcopy(v):
    """Function to create a deep copy of simple data types

    Designed to be used within the Ansible "engine" to improve performance
    issues where ``copy.deepcopy`` was used previously, largely with CPU
    and memory contention.

    This only supports the following data types, and was designed to only
    handle specific workloads:

    * ``dict``
    * ``list``

    Most often the data we pass here will come from a serialization such
    as JSON, so we shouldn't have need for other data types such as
    ``set`` or ``tuple``.

    Take note that this function should not be used extensively as a
    repalcement for ``deepcopy``  due to the naive way in which this
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
            ret[key] = naive_deepcopy(value)
        else:
            ret[key] = value

    return ret
