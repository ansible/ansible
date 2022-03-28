#!/usr/bin/python
from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
# overridden
from ansible.module_utils.ansible_release import data

results = {"data": data}

AnsibleModule(argument_spec=dict()).exit_json(**results)
