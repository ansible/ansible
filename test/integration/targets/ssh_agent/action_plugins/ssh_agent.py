from __future__ import annotations

import os

from ansible.plugins.action import ActionBase
from ansible.utils._ssh_agent import SshAgentClient


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        results = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect
        match self._task.args['action']:
            case 'list':
                return self.list()
            case _:
                return {'failed': True, 'msg': 'not implemented'}

    def list(self):
        result = {'keys': [], 'nkeys': 0}
        with SshAgentClient(os.environ['SSH_AUTH_SOCK']) as client:
            key_list = client.list()
            result['nkeys'] = key_list.nkeys
            for key in key_list.keys:
                public_key = key.public_key
                key_size = getattr(public_key, 'key_size', 256)
                fingerprint = key.fingerprint
                key_type = key.type.main_type
                result['keys'].append({
                    'type': key_type,
                    'key_size': key_size,
                    'fingerprint': f'SHA256:{fingerprint}',
                    'comments': key.comments,
                })

        return result
