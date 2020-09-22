#!/usr/bin/python
# Copyright: (c) 2020, Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        {
            'state': {
                'default': 'present',
                'type': 'str',
                'choices': ['absent', 'present'],
            },
            'path': {},
            'content': {},
        },
        required_if=(
            ('state', 'present', ('path', 'content'), True),
        ),
        mutually_exclusive=(
            ('path', 'content'),
        ),
    )

    module.exit_json(**module.params)


if __name__ == '__main__':
    main()
