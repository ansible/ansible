#!/usr/bin/python
from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(argument_spec=dict(
        marker=dict(type='str'),
        secret=dict(type='str', no_log=True),
        opts=dict(
            type='dict',
            options=dict(
                secret=dict(type='str', no_log=True),
                plain=dict(type='str'),
            ),
        ),
        entries=dict(
            type='list',
            elements='dict',
            options=dict(
                secret=dict(type='str', no_log=True),
                plain=dict(type='str'),
            ),
        ),
    ))

    module.exit_json()


if __name__ == '__main__':
    main()
