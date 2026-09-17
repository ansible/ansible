# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = """
    name: secret_probe
    author: Ansible Core Team
    short_description: resolve options marked as config secrets so they are registered for masking
    description:
        - Test helper for the config C(secret) keyword (FR11).
        - Each requested option is resolved and returned; because the options are marked
          C(secret), resolving them registers the value with the masker regardless of the
          source (env, ini, vars, or plugin args) that supplied it.
    options:
      str_env:
        type: str
        secret: true
        env:
          - name: ANSIBLE_SECRET_PROBE_ENV
      str_ini:
        type: str
        secret: true
        ini:
          - section: secret_probe
            key: str_ini
      str_vars:
        type: str
        secret: true
        vars:
          - name: secret_probe_vars
      string_direct:
        type: string
        secret: true
      list_direct:
        type: list
        secret: true
"""

from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        self.set_options(var_options=variables, direct=kwargs)

        result = []
        for name in terms:
            # resolving a `secret: true` option registers its value with the masker
            value = self.get_option(name)
            if isinstance(value, list):
                result.extend(str(v) for v in value)
            else:
                result.append(value)

        return result
