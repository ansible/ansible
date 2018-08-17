# (c) 2018 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils import six


def deepishcopy(v):
    """Function to create a deep copy of simple data types

    Designed to be used within the Ansible "engine" to improve performance
    issues where ``copy.deepcopy`` was used previously.

    This may not support all data types, and was designed to handle specific workloads.

    Most often, the data we pass here came from a serialization such as JSON.
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
            ret[key] = deepishcopy(value)
        else:
            ret[key] = value

    return ret
