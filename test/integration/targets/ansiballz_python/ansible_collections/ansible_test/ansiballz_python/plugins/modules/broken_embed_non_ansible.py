#!/usr/bin/python

from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule

ANSIBLE_EMBED = (
    ('ansible_collections.ansible_test.ansiballz_python.plugins.module_utils', 'embed_this.py'),
    ('jinja2.runtime', 'environment.py'),
)

AnsibleModule(dict()).exit_json()  # no-op for sanity
