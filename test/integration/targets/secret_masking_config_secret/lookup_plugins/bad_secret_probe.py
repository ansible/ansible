# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = """
    name: bad_secret_probe
    author: Ansible Core Team
    short_description: invalid config secret plugin used to assert the secret/type guard
    description:
        - Declares an option that marks a non-string C(int) type as C(secret), which is not allowed.
        - Loading this plugin must fail because C(secret) is only supported for string-producing types.
    options:
      port:
        type: int
        secret: true
        default: 0
"""

from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        self.set_options(var_options=variables, direct=kwargs)
        return list(terms)
