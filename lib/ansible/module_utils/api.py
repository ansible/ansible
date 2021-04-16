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

import random
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


def _retry_limit_exceeded(retries):
    def function_wrapper(function):
        def raise_error(*args, **kwargs):
            raise Exception("Retry limit exceeded: %d" % retries)
        return raise_error
    return function_wrapper


def retry(retries=None, retry_pause=1):
    """Retry decorator.

    This assumes the function has already been called, so if retries == 1, the maximum attempts
    have been reached. If retries is None, the function is a no-op.
    """
    if retries is None:
        return lambda function: lambda *args, **kwargs: None
    if retries <= 1:
        return _retry_limit_exceeded(retries)
    try:
        backoff_delays = [retry_pause for delay in range(0, retries)]
        return retry_wrapper(backoff_iterator=backoff_delays, retry_condition=lambda x: True)
    except Exception:
        raise Exception("Retry limit exceeded: %d" % retries)


def jittered_backoff_generator(retries=10, delay=3, max_delay=60):
    for retry in range(0, retries):
        yield random.randint(0, min(max_delay, delay * 2 ** retry))


def retry_wrapper(backoff_iterator, retry_condition):
    """Generic retry decorator.

    :param backoff_iterator: An iterable of delays in seconds.
    :param retry_condition: A function that takes an exception as an argument and returns a boolean.
    """
    def function_wrapper(function):
        def run_function(*args, **kwargs):
            """This assumes the function has not already been called.
            If backoff_iterator is empty, we should still run the function a single time with no delay.
            """

            for delay in backoff_iterator:
                try:
                    return function(*args, **kwargs)
                except Exception as e:
                    if retry_condition(e):
                        time.sleep(delay)
                    else:
                        raise e
            # Only or final attempt
            return function(*args, **kwargs)

        return run_function
    return function_wrapper
