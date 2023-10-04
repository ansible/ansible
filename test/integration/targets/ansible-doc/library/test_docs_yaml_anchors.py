#!/usr/bin/python
from __future__ import annotations


DOCUMENTATION = '''
---
module: test_docs_yaml_anchors
short_description: Test module with YAML anchors in docs
description:
    - Test module
author:
    - Ansible Core Team
options:
  at_the_top: &toplevel_anchor
    description:
        - Short desc
    default: some string
    type: str

  last_one: *toplevel_anchor

  egress:
    description:
        - Egress firewall rules
    type: list
    elements: dict
    suboptions: &sub_anchor
        port:
            description:
                - Rule port
            type: int
            required: true

  ingress:
    description:
        - Ingress firewall rules
    type: list
    elements: dict
    suboptions: *sub_anchor
'''

EXAMPLES = '''
'''

RETURN = '''
'''


from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            at_the_top=dict(type='str', default='some string'),
            last_one=dict(type='str', default='some string'),
            egress=dict(type='list', elements='dict', options=dict(
                port=dict(type='int', required=True),
            )),
            ingress=dict(type='list', elements='dict', options=dict(
                port=dict(type='int', required=True),
            )),
        ),
    )

    module.exit_json()


if __name__ == '__main__':
    main()
