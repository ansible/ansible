# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

from collections import ChainMap

from jinja2.utils import missing

from ansible.errors import AnsibleError, AnsibleUndefinedVariable
from ansible.module_utils.common.text.converters import to_native


__all__ = ['AnsibleJ2Vars']


def _process_locals(_l):
    if _l is None:
        return {}
    return {
        k: v for k, v in _l.items()
        if v is not missing
        and k not in {'context', 'environment', 'template'}  # NOTE is this really needed?
    }


class AnsibleJ2Vars(ChainMap):
    """Helper variable storage class that allows for nested variables templating: `foo: "{{ bar }}"`."""

    def __init__(self, templar, globals, locals=None):
        self._templar = templar
        super().__init__(
            _process_locals(locals),  # first mapping has the highest precedence
            self._templar.available_variables,
            globals,
        )

    def __getitem__(self, varname):
        variable = super().__getitem__(varname)

        from ansible.vars.hostvars import HostVars
        if (varname == "vars" and isinstance(variable, dict)) or isinstance(variable, HostVars) or hasattr(variable, '__UNSAFE__'):
            return variable

        try:
            return self._templar.template(variable)
        except AnsibleUndefinedVariable as e:
            # Instead of failing here prematurely, return an Undefined
            # object which fails only after its first usage allowing us to
            # do lazy evaluation and passing it into filters/tests that
            # operate on such objects.
            return self._templar.environment.undefined(
                hint=f"{variable}: {e.message}",
                name=varname,
                exc=AnsibleUndefinedVariable,
            )
        except Exception as e:
            msg = getattr(e, 'message', None) or to_native(e)
            raise AnsibleError(
                f"An unhandled exception occurred while templating '{to_native(variable)}'. "
                f"Error was a {type(e)}, original message: {msg}"
            )

    def add_locals(self, locals):
        """If locals are provided, create a copy of self containing those
        locals in addition to what is already in this variable proxy.
        """
        if locals is None:
            return self

        current_locals = self.maps[0]
        current_globals = self.maps[2]

        # prior to version 2.9, locals contained all of the vars and not just the current
        # local vars so this was not necessary for locals to propagate down to nested includes
        new_locals = current_locals | locals

        return AnsibleJ2Vars(self._templar, current_globals, locals=new_locals)
