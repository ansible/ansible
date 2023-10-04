#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec={
            'state': {},
            'secret': {'no_log': True},
            'subopt_dict': {
                'type': 'dict',
                'options': {
                    'str_sub_opt1': {'no_log': True},
                    'str_sub_opt2': {},
                    'nested_subopt': {
                        'type': 'dict',
                        'options': {
                            'n_subopt1': {'no_log': True},
                        }
                    }
                }
            },
            'subopt_list': {
                'type': 'list',
                'elements': 'dict',
                'options': {
                    'subopt1': {'no_log': True},
                    'subopt2': {},
                }
            }

        }
    )
    module.exit_json(msg='done')


if __name__ == '__main__':
    main()
