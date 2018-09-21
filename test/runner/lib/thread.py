"""Python threading tools."""

from __future__ import absolute_import, print_function

import threading
import sys

try:
    # noinspection PyPep8Naming
    import Queue as queue
except ImportError:
    # noinspection PyUnresolvedReferences
    import queue  # pylint: disable=locally-disabled, import-error


class WrappedThread(threading.Thread):
    """Wrapper around Thread which captures results and exceptions."""
    def __init__(self, action):
        """
        :type action: () -> any
        """
        # noinspection PyOldStyleClasses
        super(WrappedThread, self).__init__()
        self._result = queue.Queue()
        self.action = action
        self.result = None

    def run(self):
        """
        Run action and capture results or exception.
        Do not override. Do not call directly. Executed by the start() method.
        """
        # noinspection PyBroadException, PyPep8
        try:
            self._result.put((self.action(), None))
        except:  # pylint: disable=locally-disabled, bare-except
            self._result.put((None, sys.exc_info()))

    def wait_for_result(self):
        """
        Wait for thread to exit and return the result or raise an exception.
        :rtype: any
        """
        result, exception = self._result.get()

        if exception:
            if sys.version_info[0] > 2:
                raise exception[1].with_traceback(exception[2])
            # noinspection PyRedundantParentheses
            exec('raise exception[0], exception[1], exception[2]')  # pylint: disable=locally-disabled, exec-used

        self.result = result

        return result
