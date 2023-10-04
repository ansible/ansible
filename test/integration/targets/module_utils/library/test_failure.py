#!/usr/bin/python
from __future__ import annotations

results = {}
# Test that we are rooted correctly
# Following files:
#   module_utils/yak/zebra/foo.py
from ansible.module_utils.zebra import foo4

results['zebra'] = foo4.data

from ansible.module_utils.basic import AnsibleModule
AnsibleModule(argument_spec=dict()).exit_json(**results)
