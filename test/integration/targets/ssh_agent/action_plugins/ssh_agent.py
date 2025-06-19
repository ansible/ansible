from __future__ import annotations

import os

from ansible.plugins.action import ActionBase
from ansible._internal._ssh._ssh_agent import SshAgentClient

from cryptography.hazmat.primitives.serialization import ssh


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        results = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect
        match self._task.args['action']:
            case 'list':
                return self.list()
            case 'remove':
                return self.remove(self._task.args['pubkey'])
            case 'remove_all':
                return self.remove_all()
            case _:
                return {'failed': True, 'msg': 'not implemented'}

    def remove(self, pubkey_data):
        with SshAgentClient(os.environ['SSH_AUTH_SOCK']) as client:
            public_key = ssh.load_ssh_public_key(pubkey_data.encode())
            client.remove(public_key)
            return {'failed': public_key in client}

    def remove_all(self):
        with SshAgentClient(os.environ['SSH_AUTH_SOCK']) as client:
            nkeys_before = client.list().nkeys
            client.remove_all()
            nkeys_after = client.list().nkeys
            return {
                'failed': nkeys_after != 0,
                'nkeys_removed': nkeys_before,
            }

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
