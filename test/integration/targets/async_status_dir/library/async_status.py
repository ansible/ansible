#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
import os

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def main():

    module = AnsibleModule(argument_spec=dict(
        jid=dict(type='str', required=True),
        mode=dict(type='str', default='status', choices=['cleanup', 'status']),
        # Tests that async_dir is always set, this shouldn't change in case a collection's async_status relies on this.
        async_dir=dict(type='path', required=True),
    ))

    module.exit_json(async_dir=module.params['async_dir'])


if __name__ == '__main__':
    main()
