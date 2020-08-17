#!/usr/bin/python
from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            arg1=dict(type='str', default='default1'),
            arg2=dict(type='str', default='default2'),
            arg3=dict(type='str', default='default3'),
        ),
        supports_check_mode=True
    )

    result = dict(
        test_module_defaults=dict(
            arg1=module.params['arg1'],
            arg2=module.params['arg2'],
            arg3=module.params['arg3'],
        ),
    )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
