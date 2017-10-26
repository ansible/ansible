#!/usr/bin/python

# Copyright: (c) 2017, Dag Wieers (@dagwieers) <dag@wieers.com>

# This module accepts input directly as options to AnsibleModule,
# allowing one to mimic every behaviour from a module directly by calling it

from ansible.module_utils.basic import AnsibleModule, _load_params

params = _load_params()

# Add argument_spec itself
params['argument_spec'].update(dict(argument_spec=dict(type='dict')))

module = AnsibleModule(
    argument_spec=params['argument_spec'],
)

module.exit_json(params=params)
