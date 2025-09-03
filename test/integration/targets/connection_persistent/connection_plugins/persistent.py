from __future__ import annotations

import json
import os
import pickle

from ansible.playbook.play_context import PlayContext
from ansible.plugins.connection import NetworkConnectionBase


class Connection(NetworkConnectionBase):
    transport = 'persistent'
    supports_persistence = True

    def _connect(self):
        self._connected = True

    def update_play_context(self, pc_data):
        pc = self._play_context = PlayContext()

        pc.deserialize(
            pickle.loads(
                pc_data.encode(errors='surrogateescape')
            )
        )

    def get_capabilities(self, *args, **kwargs):
        return json.dumps({
            'pid': os.getpid(),
            'ppid': os.getppid(),
            **self._play_context.dump_attrs()
        })
