#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_rabbitmq_plugin
short_description: Manage RabbitMQ plugins
description:
  - Manage RabbitMQ plugins.
version_added: "2.4"
author:
  - Artem Zinenko (@ar7z1)
options:
  names:
    description:
      - Comma-separated list of plugin names.
    required: yes
    aliases: [ name ]
  new_only:
    description:
      - Only enable missing plugins.
      - Does not disable plugins that are not in the names list.
    type: bool
    default: "no"
  state:
    description:
      - Specify if plugins are to be enabled or disabled.
    choices: [ disabled, enabled ]
    default: enabled
  prefix:
    description:
      - Specify a custom install prefix to a Rabbit.
'''

EXAMPLES = r'''
- name: Enables the rabbitmq_management plugin
  win_rabbitmq_plugin:
    names: rabbitmq_management
    state: enabled
'''

RETURN = r'''
enabled:
  description: list of plugins enabled during task run
  returned: always
  type: list
  sample: ["rabbitmq_management"]
disabled:
  description: list of plugins disabled during task run
  returned: always
  type: list
  sample: ["rabbitmq_management"]
'''
