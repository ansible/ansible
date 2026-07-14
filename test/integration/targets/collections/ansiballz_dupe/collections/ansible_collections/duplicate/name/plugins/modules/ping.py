#!/usr/bin/python
from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule
AnsibleModule({}).exit_json(ping='duplicate.name.pong')
