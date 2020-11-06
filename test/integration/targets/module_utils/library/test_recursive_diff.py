#!/usr/bin/python
# Copyright: (c) 2020, Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.dict_transformations import recursive_diff


def main():
    module = AnsibleModule(
        {
            'a': {'type': 'dict'},
            'b': {'type': 'dict'},
        }
    )

    module.exit_json(
        the_diff=recursive_diff(
            module.params['a'],
            module.params['b'],
        ),
    )


if __name__ == '__main__':
    main()
