#!/usr/bin/python

results = {}
# Test that we are rooted correctly
# Following files:
#   module_utils/yak/zebra/foo.py
from ansible.module_utils.zebra import foo

results['zebra'] = foo.data

from ansible.module_utils.basic import AnsibleModule
AnsibleModule(argument_spec=dict()).exit_json(**results)
