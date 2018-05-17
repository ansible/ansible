# -*- mode: python -*-
#
# Copyright: Ansible Team
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: group_by
short_description: Create Ansible groups based on facts
description:
  - Use facts to create ad-hoc groups that can be used later in a playbook.
  - This module is also supported for Windows targets.
version_added: "0.9"
options:
  key:
    description:
    - The variables whose values will be used as groups
    required: true
  parents:
    description:
    - The list of the parent groups
    required: false
    default: "all"
    version_added: "2.4"
author: "Jeroen Hoekx (@jhoekx)"
notes:
  - Spaces in group names are converted to dashes '-'.
  - This module is also supported for Windows targets.
'''

EXAMPLES = '''
# Create groups based on the machine architecture
- group_by:
    key: machine_{{ ansible_machine }}

# Create groups like 'kvm-host'
- group_by:
    key: virt_{{ ansible_virtualization_type }}_{{ ansible_virtualization_role }}

# Create nested groups
- group_by:
    key: el{{ ansible_distribution_major_version }}-{{ ansible_architecture }}
    parents:
      - el{{ ansible_distribution_major_version }}

'''
