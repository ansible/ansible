#!/usr/bin/python

# Copyright: (c) 2019, Christian Sandrini <mail@chrissandrini.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: serviceguard_node

short_description: HP ServiceGuard node package

version_added: "2.7"

description:
	- This package controls nodes of a HP ServiceGuard cluster

options:
    name:
        description:
            - Name of the node
        required: true
    state:
        description:
	    - Desired state of the node
	choices: ["running","halted"]
        required: false
	default: running
    path:
        description:
            - Path of the cm* binaries
        required: false
        default: /usr/local/cmcluster/bin
        



author:
    - Christian Sandrini (@sandrich)
'''

EXAMPLES = '''
# Starts the node
- name: Starts node01
  serviceguard_node:
    name: node01
    state: started

# Stops the node
- name: Stops node01
  serviceguard_node:
    name: node01
    state: stopped

'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule

def main():
    module_args = dict(
        name=dict(type='str', required=True),
        state=dict(type='str', required=False, default='started', choices=['started','stopped']),
        path=dict(type='str', required=False, default='/usr/local/cmcluster/bin')
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(changed=False)

    module.exit_json(**result)

if __name__ == '__main__':
    main()