# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = """
"""

EXAMPLES = """
"""

RETURN = """
"""
import pathlib

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(),
    )

    result = dict(
        me=str(pathlib.Path(__file__).absolute()),
    )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
