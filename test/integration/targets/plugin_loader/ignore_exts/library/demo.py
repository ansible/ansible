#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule


def main():
    module_args = dict(
        name=dict(type='str', required=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    result = {}
    result['message'] = 'ping, {0}'.format(module.params['name'])
    result['changed'] = False

    module.exit_json(**result)


if __name__ == '__main__':
    main()
