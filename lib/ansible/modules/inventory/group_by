# -*- mode: python -*-

DOCUMENTATION = '''
---
module: group_by
short_description: Create Ansible groups based on facts
description:
  - Use facts to create ad-hoc groups that can be used later in a playbook.
version_added: "0.9"
options:
  key:
    description:
    - The variables whose values will be used as groups
    required: true
author: Jeroen Hoekx
notes:
  - Spaces in group names are converted to dashes '-'.
'''

EXAMPLES = '''
# Create groups based on the machine architecture
-  group_by: key=machine_{{ ansible_machine }}
# Create groups like 'kvm-host'
-  group_by: key=virt_{{ ansible_virtualization_type }}_{{ ansible_virtualization_role }}
'''
