#!/usr/bin/python

DOCUMENTATION = '''
Here is the documentation
'''

EXPAMLES = '''
- lightbulb:
  name: test
  enabled: yes
'''

RETURN = '''
msg:
    description: Message
    returned: success
    type: string
    sample: This is a sample
'''

ANSIBLE_METADATA = {
        'metadata_version': '1.0',
        'suppoted_by': 'community',
        'status': ['preview']
}

from ansible.module_utils.basic import AnsibleModule

def main():
    module = AnsibleModule(
        argument_spec = dict(
            echo_message = dict(required=True, type='str')
        ),
        supports_check_mode = True
    )

    echo_message = module.argument_spec['echo_message']

    if module.check_mode:
        module.exit_json(changed=True, msg='This is check mode')

    module.exit_json(change=True, msg=echo_message)

if __name__ == '__main__':
    main()
