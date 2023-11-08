from __future__ import annotations

import os

from ansible.plugins.action import ActionBase
from ansible.utils.ssh_agent import Client
from ansible.module_utils.common.text.converters import to_bytes


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        results = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect
        match self._task.args['action']:
            case 'list':
                return self.list()
            case 'lock':
                return self.lock(self._task.args['password'])
            case 'unlock':
                return self.unlock(self._task.args['password'])
            case _:
                return {'failed': True, 'msg': 'not implemented'}

    def lock(self, password):
        with Client(os.environ['SSH_AUTH_SOCK']) as client:
            client.lock(to_bytes(password))
        return {'changed': True}

    def unlock(self, password):
        with Client(os.environ['SSH_AUTH_SOCK']) as client:
            client.unlock(to_bytes(password))
        return {'changed': True}

    def list(self):
        result = {'keys': [], 'nkeys': 0}
        with Client(os.environ['SSH_AUTH_SOCK']) as client:
            key_list = client.list()
            result['nkeys'] = key_list.nkeys
            for key in key_list.keys:
                public_key = key.public_key()
                key_size = getattr(public_key, 'key_size', 256)
                fingerprint = key.fingerprint()
                key_type = key.type.main_type
                result['keys'].append({
                    'type': key_type,
                    'key_size': key_size,
                    'fingerprint': f'SHA256:{fingerprint}',
                    'comments': key.comments,
                })

        return result
