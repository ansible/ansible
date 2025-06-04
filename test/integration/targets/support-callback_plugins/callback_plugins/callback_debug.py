# (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import functools

from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'callback_debug'

    def __init__(self, *args, **kwargs):
        super(CallbackModule, self).__init__(*args, **kwargs)
        self._display.display('__init__')

        for name in (cb for cb in dir(self) if cb.startswith('v2_')):
            setattr(self, name, functools.partial(self.handle_v2, name))

    def handle_v2(self, name, *args, **kwargs):
        self._display.display(name)
