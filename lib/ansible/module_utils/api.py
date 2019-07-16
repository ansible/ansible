# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2015 Brian Ccoa, <bcoca@ansible.com>
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
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
            if minrate is not None:
                elapsed = time.clock() - last[0]
                left = minrate - elapsed
                if left > 0:
                    time.sleep(left)
                last[0] = time.clock()
            ret = f(*args, **kwargs)
            return ret

        return ratelimited
    return wrapper


def retry(retries=None, retry_pause=1):
    """Retry decorator"""
    def wrapper(f):
        retry_count = 0

        def retried(*args, **kwargs):
            if retries is not None:
                ret = None
                while True:
                    # pylint doesn't understand this is a closure
                    retry_count += 1  # pylint: disable=undefined-variable
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
