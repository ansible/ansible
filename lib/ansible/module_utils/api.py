# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright: (c) 2015, Brian Coca, <bcoca@ansible.com>
#
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)
"""
This module adds shared support for generic api modules

In order to use this module, include it as part of a custom
module as shown below.

The 'api' module provides the following common argument specs:

    * rate limit spec
        - rate: number of requests per time unit (int)
        - rate_limit: time window in which the limit is applied in seconds

    * retry spec
        - retries: number of attempts
        - retry_pause: delay between attempts in seconds
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
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


def basic_auth_argument_spec(spec=None):
    arg_spec = (dict(
        api_username=dict(type='str'),
        api_password=dict(type='str', no_log=True),
        api_url=dict(type='str'),
        validate_certs=dict(type='bool', default=True)
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

        def ratelimited(*args, **kwargs):
            if sys.version_info >= (3, 8):
                real_time = time.process_time
            else:
                real_time = time.clock
            if minrate is not None:
                elapsed = real_time() - last[0]
                left = minrate - elapsed
                if left > 0:
                    time.sleep(left)
                last[0] = real_time()
            ret = f(*args, **kwargs)
            return ret

        return ratelimited
    return wrapper


def retry(retries=None, retry_pause=1):
    """Retry decorator"""
    def wrapper(f):

        def retried(*args, **kwargs):
            retry_count = 0
            if retries is not None:
                ret = None
                while True:
                    retry_count += 1
                    if retry_count >= retries:
                        raise Exception("Retry limit exceeded: %d" % retries)
                    try:
                        ret = f(*args, **kwargs)
                    except Exception:
                        pass
                    if ret:
                        break
                    time.sleep(retry_pause)
                return ret

        return retried
    return wrapper
