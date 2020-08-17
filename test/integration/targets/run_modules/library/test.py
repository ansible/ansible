#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

module = AnsibleModule(argument_spec=dict())

module.exit_json(**{'tempdir': module._remote_tmp})
