from __future__ import annotations

import atexit
import os
import sys

from ansible.plugins.callback import CallbackBase
from ansible.utils.display import Display
from threading import Thread

# This callback plugin reliably triggers the deadlock from https://github.com/ansible/ansible-runner/issues/1164 when
# run on a TTY/PTY. It starts a thread in the controller that spews unprintable characters to stdout as fast as
# possible, while causing forked children to write directly to the inherited stdout immediately post-fork. If a fork
# occurs while the spew thread holds stdout's internal BufferedIOWriter lock, the lock will be orphaned in the child,
# and attempts to write to stdout there will hang forever.

# Any mechanism that ensures non-main threads do not hold locks before forking should allow this test to pass.

# ref: https://docs.python.org/3/library/io.html#multi-threading
# ref: https://github.com/python/cpython/blob/0547a981ae413248b21a6bb0cb62dda7d236fe45/Modules/_io/bufferedio.c#L268


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_NAME = 'spewstdio'

    def __init__(self):
        super().__init__()
        self.display = Display()

        if os.environ.get('SPEWSTDIO_ENABLED', '0') != '1':
            self.display.warning('spewstdio test plugin loaded but disabled; set SPEWSTDIO_ENABLED=1 to enable')
            return

        self.display = Display()
        self._keep_spewing = True

        # cause the child to write directly to stdout immediately post-fork
        os.register_at_fork(after_in_child=lambda: print(f"hi from forked child pid {os.getpid()}"))

        # in passing cases, stop spewing when the controller is exiting to prevent fatal errors on final flush
        atexit.register(self.stop_spew)

        self._spew_thread = Thread(target=self.spew, daemon=True)
        self._spew_thread.start()

    def stop_spew(self):
        self._keep_spewing = False

    def spew(self):
        # dump a message so we know the callback thread has started
        self.display.warning("spewstdio STARTING NONPRINTING SPEW ON BACKGROUND THREAD")

        while self._keep_spewing:
            # dump a non-printing control character directly to stdout to avoid junking up the screen while still
            # doing lots of writes and flushes.
            sys.stdout.write('\x1b[K')
            sys.stdout.flush()

        self.display.warning("spewstdio STOPPING SPEW")
