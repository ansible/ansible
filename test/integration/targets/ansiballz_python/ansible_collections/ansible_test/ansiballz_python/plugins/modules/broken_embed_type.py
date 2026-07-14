#!/usr/bin/python

from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.embed import EmbedManager

e1 = EmbedManager.embed(1234, 'embed_this.py')


AnsibleModule(dict()).exit_json()  # no-op for sanity
