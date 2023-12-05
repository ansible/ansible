from __future__ import annotations

from ansible.plugins.callback import CallbackBase

DOCUMENTATION = '''
    callback: usercallback
    callback_type: notification
    short_description: does stuff
    description:
      - does some stuff
'''


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'usercallback'

    def __init__(self):

        super(CallbackModule, self).__init__()
        self._display.display("loaded usercallback from collection, yay")

    def v2_runner_on_ok(self, result):
        self._display.display("usercallback says ok")
