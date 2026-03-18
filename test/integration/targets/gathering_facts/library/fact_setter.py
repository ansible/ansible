from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            key=dict(type='str'),
            value=dict(type='str'),
        )
    )

    key = module.params['key']
    value = module.params['value']

    module.exit_json(ansible_facts={key: value})


if __name__ == '__main__':
    main()
