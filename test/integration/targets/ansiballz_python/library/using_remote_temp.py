# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = """
---
module: using_remote_temp
version_added: historical
short_description: see name
description: see name
options:
extends_documentation_fragment:
    - action_common_attributes
attributes:
    check_mode:
        support: full
    diff_mode:
        support: none
    platform:
        platforms: posix
author:
  - Ansible Core Team
"""

EXAMPLES = """
# Test we where module is unzipped to by ansiballz

- name: Example from an Ansible Playbook
  using_remote_temp:

"""

RETURN = """
me:
    description: output of __file__
    returned: success
    type: str
    sample: /var/tmp/me.py
"""
import pathlib

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(),
        supports_check_mode=True
    )

    result = dict(
        me=str(pathlib.Path(__file__).absolute()),
    )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
