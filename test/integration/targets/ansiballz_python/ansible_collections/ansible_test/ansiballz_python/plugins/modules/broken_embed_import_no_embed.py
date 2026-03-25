#!/usr/bin/python

from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.embed import EmbedManager

assert EmbedManager is not None, "no-op usage of the imported type"

AnsibleModule(dict()).exit_json()  # no-op for sanity
