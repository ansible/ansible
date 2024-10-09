#!/usr/bin/python

# Copyright: (c) 2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = r"""
---
module: ansible_release
short_description: Get ansible_release info from module_utils
description: Get ansible_release info from module_utils
author:
- Ansible Project
"""

EXAMPLES = r"""
#
"""

RETURN = r"""
#
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ansible_release import __version__, __author__, __codename__


def main():
    module = AnsibleModule(argument_spec={})
    result = {
        'version': __version__,
        'author': __author__,
        'codename': __codename__,
    }
    module.exit_json(**result)


if __name__ == '__main__':
    main()
