#!/usr/bin/python
# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = """
    module: display_probe
    short_description: route text through Display sinks for secret-masking tests
    description:
        - Test helper for the controller C(Display) egress sinks.
        - Emits the supplied text via C(module.warn) and C(module.deprecate) so the warning
          and deprecation sinks can be checked for masking.
        - Accepts C(invocation_arg) which is intentionally NOT returned in the result, so it
          only appears in the injected C(invocation) dump (with C(INJECT_INVOCATION) enabled
          at C(-vvv)); that isolates the invocation-display sink from ordinary result masking.
    options:
      warning:
        description: text to emit via C(module.warn).
        type: str
        required: true
      deprecation:
        description: text to emit via C(module.deprecate).
        type: str
        required: true
      invocation_arg:
        description: arbitrary text that surfaces only in the invocation dump.
        type: str
        required: true
"""

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            warning=dict(type='str', required=True),
            deprecation=dict(type='str', required=True),
            invocation_arg=dict(type='str', required=True),
        ),
    )

    module.warn(module.params['warning'])
    module.deprecate(module.params['deprecation'], version='9.9.9')

    # invocation_arg is deliberately not echoed back, so it only appears in the invocation dump
    module.exit_json(changed=False)


if __name__ == '__main__':
    main()
