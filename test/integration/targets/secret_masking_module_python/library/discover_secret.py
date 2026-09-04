#!/usr/bin/python
# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.secrets import register_secret, register_secrets, mask_secrets


def main():
    module = AnsibleModule(argument_spec=dict(
        incoming=dict(type='str', required=True),
        register_as_secret=dict(type='str', required=False, default=None),
        no_log_option=dict(type='str', required=True, no_log=True),
    ))

    incoming = module.params['incoming']

    secrets = ['PyModuleSecret1', 'PyModuleSecret2', 'PyModuleSecret3']

    discovered = register_secret(secrets[0])

    register_secrets(secrets)

    masked = mask_secrets(f"{secrets[0]} {secrets[1]} {secrets[2]}")

    register_as_secret = module.params['register_as_secret']
    if register_as_secret is not None:
        register_secret(register_as_secret)

    module.exit_json(
        changed=False,
        discovered=discovered,
        masked=masked,
        incoming=incoming,
        incoming_masked=mask_secrets(incoming),
        register_as_secret=register_as_secret,
        no_log_option=module.params['no_log_option'],
        no_log_option_masked=mask_secrets(module.params['no_log_option']),
    )


if __name__ == '__main__':
    main()
