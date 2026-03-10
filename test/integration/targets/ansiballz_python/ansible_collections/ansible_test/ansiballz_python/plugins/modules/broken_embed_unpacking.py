#!/usr/bin/python

from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule

ANSIBLE_EMBED, other = ('abc', 'def')

AnsibleModule(dict()).exit_json()
