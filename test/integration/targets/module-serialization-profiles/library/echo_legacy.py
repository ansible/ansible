from __future__ import annotations

METADATA = """
schema_version: 1
serialization_profile: legacy
"""

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            data=dict(type='raw'),
        ),
        supports_check_mode=True,
    )

    if module.params['data'] == 'crash':
        raise Exception("boom")

    result = dict(
        data=module.params['data'],
    )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
