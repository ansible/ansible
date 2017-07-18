#!/usr/bin/env python
from ansible.module_utils.basic import AnsibleModule
import logging
logging.basicConfig(filename='example.log',level=logging.DEBUG)
#!/usr/bin/python
ANSIBLE_METADATA = {
            'metadata_version': '1.0',
                'supported_by': 'community',
                    'status': ['preview', 'deprecated']
                    }

DOCUMENTATION = '''
---
module: modulename
short_description: This is a sentence describing the module
short_description: short descriptio
description: description
version_added: 3.4
author: nlove
options:
    foo:
        description: foo
        required: false
        default: bar
'''
def main():
    module = AnsibleModule(
        argument_spec = dict(
            foo = dict(required=False, default='bar')
        )
    )
    logging.debug(module.params['foo'])
    module.exit_json(changed=True, inputs=module.params)

if __name__ == '__main__':
    main()
