#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (C) 2020, Gonéri Le Bouder <goneri@lebouder.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: turbo_demo
short_description: A demo module for ansible_module.turbo
version_added: "1.0.0"
description:
- "This module is an example of an ansible_module.turbo integration."
author:
- Gonéri Le Bouder (@goneri)
"""

EXAMPLES = r"""
- name: Run the module
  ns.col.turbo_demo:
"""

import os

from ansible.module_utils.turbo.module import (
    AnsibleTurboModule as AnsibleModule,
)


def counter():
    counter.i += 1
    return counter.i


# NOTE: workaround to avoid a warning with ansible-doc
if True:  # pylint: disable=using-constant-test
    counter.i = 0


def get_message():
    return f"This is me running with PID: {os.getpid()}, called {counter.i} time(s)"


def run_module():
    result = {}

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(argument_spec={}, supports_check_mode=True)
    module.collection_name = "ns.col"
    previous_value = counter.i
    if not module.check_mode:
        counter()
        result["changed"] = True
    result["message"] = get_message()
    result["counter"] = counter.i
    result["envvar"] = os.environ.get("TURBO_TEST_VAR")

    if module._diff:
        result["diff"] = {"before": previous_value, "after": counter.i}

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
