#!/usr/bin/python

from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule
globals()["ANSIBLE_EMBED"] = []

ANSIBLE_EMBED[:] = []  # pylint: disable=undefined-variable

AnsibleModule(dict()).exit_json()
