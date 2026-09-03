# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = """
    name: vars_test
    short_description: register secrets and prove Display egress redacts them immediately
    description:
        - Test helper that registers secrets via the public C(ansible.module_utils.secrets) API
          and proves a subsequent C(Display) egress redacts them without any propagation delay.
    extends_documentation_fragment:
        - vars_plugin_staging
"""

from ansible.module_utils.secrets import register_secret, register_secrets, mask_secrets
from ansible.plugins.vars import BaseVarsPlugin
from ansible.utils.display import Display

display = Display()


class VarsModule(BaseVarsPlugin):

    REQUIRES_ENABLED = True

    # get_vars runs many times during a play; only probe once so the output stays deterministic
    _probed = False

    def get_vars(self, loader, path, entities):
        if not self._probed:
            type(self)._probed = True

            secrets = ['VarsSecret1', 'VarsSecret2', 'VarsSecret3']

            register_secret(secrets[0])
            display.display(f"SCN vars_register: {secrets[0]}")

            register_secrets(secrets)
            display.display(f"SCN vars_registers: {secrets[0]} {secrets[1]} {secrets[2]}")

            if mask_secrets(f"{secrets[0]} {secrets[1]} {secrets[2]}") != '$REDACTED$ $REDACTED$ $REDACTED$':
                raise Exception("mask_secrets did not redact all the registered secrets")

        return {}
