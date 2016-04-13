#
# (c) 2015 Brian Ccoa, <bcoca@ansible.com>
#
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
#
"""
This module adds shared support for generic api modules

In order to use this module, include it as part of a custom
module as shown below.

** Note: The order of the import statements does matter. **

from ansible.module_utils.basic import *
from ansible.module_utils.api import *

The 'api' module provides the following common argument specs:

    * rate limit spec
        - rate: number of requests per time unit (int)
        - rate_limit: time window in which the limit is applied in seconds

    * retry spec
        - retries: number of attempts
        - retry_pause: delay between attempts in seconds

"""
import time

def rate_limit_argument_spec(spec=None):
    """Creates an argument spec for working with rate limiting"""
    arg_spec = (dict(
        rate=dict(type='int'),
        rate_limit=dict(type='int'),
    ))
    if spec:
        arg_spec.update(spec)
    return arg_spec

def retry_argument_spec(spec=None):
    """Creates an argument spec for working with retrying"""
    arg_spec = (dict(
        retries=dict(type='int'),
        retry_pause=dict(type='float', default=1),
    ))
    if spec:
        arg_spec.update(spec)
    return arg_spec

def rate_limit(rate=None, rate_limit=None):
    """rate limiting decorator"""
    minrate = None
    if rate is not None and rate_limit is not None:
        minrate = float(rate_limit) / float(rate)
    def wrapper(f):
        last = [0.0]
        def ratelimited(*args,**kwargs):
            if minrate is not None:
                elapsed = time.clock() - last[0]
                left = minrate - elapsed
                if left > 0:
                    time.sleep(left)
                last[0] = time.clock()
            ret = f(*args,**kwargs)
            return ret
        return ratelimited
    return wrapper

def retry(retries=None, retry_pause=1):
    """Retry decorator"""
    def wrapper(f):
        retry_count = 0
        def retried(*args,**kwargs):
            if retries is not None:
                ret = None
                while True:
                    retry_count += 1
                    if retry_count >= retries:
                        raise Exception("Retry limit exceeded: %d" % retries)
                    try:
                        ret = f(*args,**kwargs)
                    except:
                        pass
                    if ret:
                        break
                    time.sleep(retry_pause)
                return ret
        return retried
    return wrapper

