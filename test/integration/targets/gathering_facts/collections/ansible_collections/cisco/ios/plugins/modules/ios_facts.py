#!/usr/bin/python
from __future__ import annotations

DOCUMENTATION = """
---
module: ios_facts
short_description: supporting network facts module
description:
  - supporting network facts module for gather_facts + module_defaults tests
options:
  gather_subset:
    description:
      - When supplied, this argument restricts the facts collected
         to a given subset.
      - Possible values for this argument include
         C(all), C(hardware), C(config), and C(interfaces).
      - Specify a list of values to include a larger subset.
      - Use a value with an initial C(!) to collect all facts except that subset.
    required: false
    default: '!config'
"""

from ansible.module_utils.basic import AnsibleModule


def main():
    """main entry point for module execution
    """
    argument_spec = dict(
        gather_subset=dict(default='!config')
    )
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    module.exit_json(ansible_facts={'gather_subset': module.params['gather_subset'], '_ansible_facts_gathered': True})


if __name__ == '__main__':
    main()
