# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import signal

# timeout function to make sure some fact gathering
# steps do not exceed a time limit

GATHER_TIMEOUT = None
DEFAULT_GATHER_TIMEOUT = 10


class TimeoutError(Exception):
    pass


def timeout(seconds=None, error_message="Timer expired"):

    def decorator(func):
        def _handle_timeout(signum, frame):
            msg = 'Timer expired after %s seconds' % globals().get('GATHER_TIMEOUT')
            raise TimeoutError(msg)

        def wrapper(*args, **kwargs):
            local_seconds = seconds
            if local_seconds is None:
                local_seconds = globals().get('GATHER_TIMEOUT') or DEFAULT_GATHER_TIMEOUT
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(local_seconds)

            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wrapper

    # If we were called as @timeout, then the first parameter will be the
    # function we are to wrap instead of the number of seconds.  Detect this
    # and correct it by setting seconds to our default value and return the
    # inner decorator function manually wrapped around the function
    if callable(seconds):
        func = seconds
        seconds = None
        return decorator(func)

    # If we were called as @timeout([...]) then python itself will take
    # care of wrapping the inner decorator around the function

    return decorator
