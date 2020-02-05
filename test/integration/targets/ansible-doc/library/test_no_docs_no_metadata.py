#!/usr/bin/python
from __future__ import absolute_import, division, print_function
__metaclass__ = type


from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(),
    )

    module.exit_json()


if __name__ == '__main__':
    main()
