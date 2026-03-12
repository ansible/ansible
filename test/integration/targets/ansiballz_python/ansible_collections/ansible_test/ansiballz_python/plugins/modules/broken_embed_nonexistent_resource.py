#!/usr/bin/python

from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.embed import EmbedManager

e1 = EmbedManager.embed('..module_utils', 'embed_nonexistent.py')

AnsibleModule(dict()).exit_json()  # no-op for sanity
