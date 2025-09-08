#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = """
module: return_fragments_not_exist
short_description: Non-existing return doc fragment
description: A module with a non-existing return doc fragment.
author:
  - Ansible Core Team
"""

EXAMPLES = """#"""

RETURN = """
extends_documentation_fragment:
  - does.not.exist
"""

from ansible.module_utils.basic import AnsibleModule


def main():
    AnsibleModule().exit_json(bar=42)


if __name__ == '__main__':
    main()
