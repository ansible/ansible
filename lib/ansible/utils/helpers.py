# (c) 2016, Ansible by Red Hat <info@ansible.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_native


class Chameleon(object):
    ''' Create an object that disguises itself as the class of the object passed in '''
    def __init__(self, obj):
        self._type = type(obj)
        self.__class__ == self._type

        def __type__(self):
            return self._type

def pct_to_int(value, num_items, min_value=1):
    '''
    Converts a given value to a percentage if specified as "x%",
    otherwise converts the given value to an integer.
    '''
    if isinstance(value, string_types) and value.endswith('%'):
        value_pct = int(value.replace("%", ""))
        return int((value_pct / 100.0) * num_items) or min_value
    else:
        return int(value)


def object_to_dict(obj, exclude=None, starts='_'):
    """
    Converts an object into a dict making the properties into keys, allows excluding certain keys
    """
    if exclude is None or not isinstance(exclude, list):
        exclude = []
    return dict((key, getattr(obj, key)) for key in dir(obj) if not (callable(getattr(obj, key)) or key.startswith(starts) or key in exclude))


def data_object_shim(obj, exclude=None, shim_methods=None):
    """
    creates scaled down object copy containing properties of original but no methods
    """
    def _unauthorized(*args, **kwargs):
        raise Exception('You are not allowed to use this method!')

    if exclude is None or not isinstance(exclude, list):
        exclude = []
    d = object_to_dict(obj, exclude=exclude, starts='__')

    # FIXME: create generic method that returns 'unauthorized' error/msg for 'callable' attributes
    new = Chameleon(obj)
    for k in d:
        setattr(new, k, d[k])

    #set explosives
    for method in [key for key in dir(obj) if callable(getattr(obj, key)) and not key.startswith('__')]:
        if method not in shim_methods:
            setattr(new, method, _unauthorized)

    if shim_methods:
        for method in shim_methods:
            try:
                setattr(new, method, getattr(obj, method))
            except AttributeError:
                pass

    return new
