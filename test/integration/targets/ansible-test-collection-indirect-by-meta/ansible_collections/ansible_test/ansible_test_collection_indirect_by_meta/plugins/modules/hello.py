from __future__ import annotations


from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(argument_spec=dict())
    module.exit_json(source='meta')


if __name__ == '__main__':
    main()
