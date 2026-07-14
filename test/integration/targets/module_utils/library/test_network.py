#!/usr/bin/python

# Copyright: (c) 2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.network import to_subnet


def main():
    module = AnsibleModule(argument_spec=dict(
        subnet=dict(),
    ))

    subnet = module.params['subnet']

    if subnet is not None:
        split_addr = subnet.split('/')
        if len(split_addr) != 2:
            module.fail_json("Invalid CIDR notation: expected a subnet mask (e.g. 10.0.0.0/32)")
        module.exit_json(resolved=to_subnet(split_addr[0], split_addr[1]))


if __name__ == '__main__':
    main()
