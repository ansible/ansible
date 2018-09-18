# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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

from collections import Mapping

from jinja2.utils import missing

from ansible.errors import AnsibleError, AnsibleUndefinedVariable
from ansible.module_utils.six import iteritems
from ansible.module_utils._text import to_native


__all__ = ['AnsibleJ2Vars']


class AnsibleJ2Vars(Mapping):
    '''
    Helper class to template all variable content before jinja2 sees it. This is
    done by hijacking the variable storage that jinja2 uses, and overriding __contains__
    and __getitem__ to look like a dict. Added bonus is avoiding duplicating the large
    hashes that inject tends to be.

    To facilitate using builtin jinja2 things like range, globals are also handled here.
    '''

    def __init__(self, templar, globals, locals=None, *extras):
        '''
        Initializes this object with a valid Templar() object, as
        well as several dictionaries of variables representing
        different scopes (in jinja2 terminology).
        '''

        self._templar = templar
        self._globals = globals
        self._extras = extras
        self._locals = dict()
        if isinstance(locals, dict):
            for key, val in iteritems(locals):
                if val is not missing:
                    if key[:2] == 'l_':
                        self._locals[key[2:]] = val
                    elif key not in ('context', 'environment', 'template'):
                        self._locals[key] = val

    def __contains__(self, k):
        if k in self._templar._available_variables:
            return True
        if k in self._locals:
            return True
        for i in self._extras:
            if k in i:
                return True
        if k in self._globals:
            return True
        return False

    def __iter__(self):
        keys = set()
        keys.update(self._templar._available_variables, self._locals, self._globals, *self._extras)
        return iter(keys)

    def __len__(self):
        keys = set()
        keys.update(self._templar._available_variables, self._locals, self._globals, *self._extras)
        return len(keys)

    def __getitem__(self, varname):
        if varname not in self._templar._available_variables:
            if varname in self._locals:
                return self._locals[varname]
            for i in self._extras:
                if varname in i:
                    return i[varname]
            if varname in self._globals:
                return self._globals[varname]
            else:
                raise KeyError("undefined variable: %s" % varname)

        variable = self._templar._available_variables[varname]

        # HostVars is special, return it as-is, as is the special variable
        # 'vars', which contains the vars structure
        from ansible.vars.hostvars import HostVars
        if isinstance(variable, dict) and varname == "vars" or isinstance(variable, HostVars) or hasattr(variable, '__UNSAFE__'):
            return variable
        else:
            value = None
            try:
                value = self._templar.template(variable)
            except AnsibleUndefinedVariable:
                raise
            except Exception as e:
                msg = getattr(e, 'message') or to_native(e)
                raise AnsibleError("An unhandled exception occurred while templating '%s'. "
                                   "Error was a %s, original message: %s" % (to_native(variable), type(e), msg))

            return value

    def add_locals(self, locals):
        '''
        If locals are provided, create a copy of self containing those
        locals in addition to what is already in this variable proxy.
        '''
        if locals is None:
            return self

        # FIXME run this only on jinja2>=2.9?
        # prior to version 2.9, locals contained all of the vars and not just the current
        # local vars so this was not necessary for locals to propagate down to nested includes
        new_locals = self._locals.copy()
        new_locals.update(locals)

        return AnsibleJ2Vars(self._templar, self._globals, locals=new_locals, *self._extras)
