#!/usr/bin/python

from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule

ANSIBLE_EMBED = (('abc', 123),)

AnsibleModule(dict()).exit_json()
