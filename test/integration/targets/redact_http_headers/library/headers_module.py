#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule


def main():
    """A module which accepts headers in the shapes real modules use, so the returned invocation can be inspected."""
    module = AnsibleModule(
        argument_spec=dict(
            url=dict(type='str'),
            headers=dict(type='dict'),
            json_headers=dict(type='str'),
            unredirected_headers=dict(type='list', elements='str'),
            nested=dict(type='dict'),
            entries=dict(type='list', elements='dict'),
            body=dict(type='dict'),
        ),
    )

    module.exit_json(changed=False, msg='done')


if __name__ == '__main__':
    main()
