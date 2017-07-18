#!/usr/bin/python

DOCUMENTATION = '''
---
module: filament
short_description: This is a hello world module.
'''

EXAMPLES = '''
'''

RETURN = '''
'''

import epdb

from ansible.module_utils.basic import AnsibleModule

def main():
    module = AnsibleModule(
        argument_spec = dict(
            state     = dict(default='present', choices=['present', 'absent']),
            foo       = dict(default='bar'),
        ),
        supports_check_mode=True
    )
    epdb.st()

    if module.params['state'] == 'absent':
        module.exit_json(changed=False)

    module.exit_json(changed=True, filament="hello world")


if __name__ == '__main__':
    main()
