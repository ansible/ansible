# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = """
    name: lookup_test
    author: Ansible Core Team
    short_description: register secrets and prove Display egress redacts them immediately
    description:
        - Test helper that registers secrets via the public C(ansible.module_utils.secrets) API
          and proves a subsequent C(Display) egress redacts them without any propagation delay.
"""

from ansible.module_utils.secrets import register_secret, register_secrets, mask_secrets
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display

display = Display()


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        secrets = ['LookupSecret1', 'LookupSecret2', 'LookupSecret3']

        register_secret(secrets[0])
        display.display(f"MARKER lookup_register: {secrets[0]}")

        register_secrets(secrets)
        display.display(f"MARKER lookup_registers: {secrets[0]} {secrets[1]} {secrets[2]}")

        if mask_secrets(f"{secrets[0]} {secrets[1]} {secrets[2]}") != '$REDACTED$ $REDACTED$ $REDACTED$':
            raise Exception("mask_secrets did not redact all the registered secrets")

        return ['done']
