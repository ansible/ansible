#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import tempfile

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec={
            'dest': {'type': 'path'},
            'call_fs_attributes': {'type': 'bool', 'default': True},
        },
        add_file_common_args=True,
    )

    results = {}

    with tempfile.NamedTemporaryFile(delete=False) as tf:
        file_args = module.load_file_common_arguments(module.params)
        module.atomic_move(tf.name, module.params['dest'])

        if module.params['call_fs_attributes']:
            results['changed'] = module.set_fs_attributes_if_different(file_args, True)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
