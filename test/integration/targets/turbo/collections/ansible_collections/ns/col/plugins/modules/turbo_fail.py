#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (C) 2021, Aubin Bikouo <abikouo>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: turbo_fail
short_description: A short module which honor additional args when calling fail_json
version_added: "1.0.0"
description:
- "This module aims to test fail_json method on Ansible.turbo module"
options:
  params:
    description:
      - parameter to display in task output
    required: false
    type: dict
author:
- Aubin Bikouo (@abikouo)
"""

EXAMPLES = r"""
- name: Fail without additional arguments
  ns.col.turbo_fail:

- name: Fail with additional arguments
  ns.col.turbo_fail:
    params:
        test: "ansible"
"""

from ansible.module_utils.turbo.module import (
    AnsibleTurboModule as AnsibleModule,
)


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            params=dict(type="dict"),
        )
    )
    module.collection_name = "ns.col"
    msg = "ansible.cloud.fail"
    if module.params.get("params"):
        module.fail_json(msg=msg, **module.params.get("params"))
    module.fail_json(msg=msg)


def main():
    run_module()


if __name__ == "__main__":
    main()
