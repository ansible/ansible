#
# (c) 2016 Allen Sanabria, <asanabria@linuxdynasty.org>
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
This module adds shared support for generic cloud modules

In order to use this module, include it as part of a custom
module as shown below.

from ansible.module_utils.cloud import CloudRetry

The 'cloud' module provides the following common classes:

    * CloudRetry
        - The base class to be used by other cloud providers, in order to
          provide a backoff/retry decorator based on status codes.

        - Example using the AWSRetry class which inherits from CloudRetry.

          @AWSRetry.exponential_backoff(retries=10, delay=3)
          get_ec2_security_group_ids_from_names()

          @AWSRetry.jittered_backoff()
          get_ec2_security_group_ids_from_names()

"""
import random
from functools import wraps
import syslog
import time


def _exponential_backoff(retries=10, delay=2, backoff=2, max_delay=60):
    """ Customizable exponential backoff strategy.
    Args:
        retries (int): Maximum number of times to retry a request.
        delay (float): Initial (base) delay.
        backoff (float): base of the exponent to use for exponential
            backoff.
        max_delay (int): Optional. If provided each delay generated is capped
            at this amount. Defaults to 60 seconds.
    Returns:
        Callable that returns a generator. This generator yields durations in
        seconds to be used as delays for an exponential backoff strategy.
    Usage:
        >>> backoff = _exponential_backoff()
        >>> backoff
        <function backoff_backoff at 0x7f0d939facf8>
        >>> list(backoff())
        [2, 4, 8, 16, 32, 60, 60, 60, 60, 60]
    """
    def backoff_gen():
        for retry in range(0, retries):
            sleep = delay * backoff ** retry
            yield sleep if max_delay is None else min(sleep, max_delay)
    return backoff_gen


def _full_jitter_backoff(retries=10, delay=3, max_delay=60, _random=random):
    """ Implements the "Full Jitter" backoff strategy described here
    https://www.awsarchitectureblog.com/2015/03/backoff.html
    Args:
        retries (int): Maximum number of times to retry a request.
        delay (float): Approximate number of seconds to sleep for the first
            retry.
        max_delay (int): The maximum number of seconds to sleep for any retry.
            _random (random.Random or None): Makes this generator testable by
            allowing developers to explicitly pass in the a seeded Random.
    Returns:
        Callable that returns a generator. This generator yields durations in
        seconds to be used as delays for a full jitter backoff strategy.
    Usage:
        >>> backoff = _full_jitter_backoff(retries=5)
        >>> backoff
        <function backoff_backoff at 0x7f0d939facf8>
        >>> list(backoff())
        [3, 6, 5, 23, 38]
        >>> list(backoff())
        [2, 1, 6, 6, 31]
    """
    def backoff_gen():
        for retry in range(0, retries):
            yield _random.randint(0, min(max_delay, delay * 2 ** retry))
    return backoff_gen


class CloudRetry(object):
    """ CloudRetry can be used by any cloud provider, in order to implement a
        backoff algorithm/retry effect based on Status Code from Exceptions.
    """
    # This is the base class of the exception.
    # AWS Example botocore.exceptions.ClientError
    base_class = None

    @staticmethod
    def status_code_from_exception(error):
        """ Return the status code from the exception object
        Args:
            error (object): The exception itself.
        """
        pass

    @staticmethod
    def found(response_code, catch_extra_error_codes=None):
        """ Return True if the Response Code to retry on was found.
        Args:
            response_code (str): This is the Response Code that is being matched against.
        """
        pass

    @classmethod
    def _backoff(cls, backoff_strategy, catch_extra_error_codes=None):
        """ Retry calling the Cloud decorated function using the provided
        backoff strategy.
        Args:
            backoff_strategy (callable): Callable that returns a generator. The
            generator should yield sleep times for each retry of the decorated
            function.
        """
        def deco(f):
            @wraps(f)
            def retry_func(*args, **kwargs):
                for delay in backoff_strategy():
                    try:
                        return f(*args, **kwargs)
                    except Exception as e:
                        if isinstance(e, cls.base_class):
                            response_code = cls.status_code_from_exception(e)
                            if cls.found(response_code, catch_extra_error_codes):
                                msg = "{0}: Retrying in {1} seconds...".format(str(e), delay)
                                syslog.syslog(syslog.LOG_INFO, msg)
                                time.sleep(delay)
                            else:
                                # Return original exception if exception is not a ClientError
                                raise e
                        else:
                            # Return original exception if exception is not a ClientError
                            raise e
                return f(*args, **kwargs)

            return retry_func  # true decorator

        return deco

    @classmethod
    def exponential_backoff(cls, retries=10, delay=3, backoff=2, max_delay=60, catch_extra_error_codes=None):
        """
        Retry calling the Cloud decorated function using an exponential backoff.

        Kwargs:
            retries (int): Number of times to retry a failed request before giving up
                default=10
            delay (int or float): Initial delay between retries in seconds
                default=3
            backoff (int or float): backoff multiplier e.g. value of 2 will
                double the delay each retry
                default=1.1
            max_delay (int or None): maximum amount of time to wait between retries.
                default=60
        """
        return cls._backoff(_exponential_backoff(
            retries=retries, delay=delay, backoff=backoff, max_delay=max_delay), catch_extra_error_codes)

    @classmethod
    def jittered_backoff(cls, retries=10, delay=3, max_delay=60, catch_extra_error_codes=None):
        """
        Retry calling the Cloud decorated function using a jittered backoff
        strategy. More on this strategy here:

        https://www.awsarchitectureblog.com/2015/03/backoff.html

        Kwargs:
            retries (int): Number of times to retry a failed request before giving up
                default=10
            delay (int): Initial delay between retries in seconds
                default=3
            max_delay (int): maximum amount of time to wait between retries.
                default=60
        """
        return cls._backoff(_full_jitter_backoff(
            retries=retries, delay=delay, max_delay=max_delay), catch_extra_error_codes)

    @classmethod
    def backoff(cls, tries=10, delay=3, backoff=1.1, catch_extra_error_codes=None):
        """
        Retry calling the Cloud decorated function using an exponential backoff.

        Compatibility for the original implementation of CloudRetry.backoff that
        did not provide configurable backoff strategies. Developers should use
        CloudRetry.exponential_backoff instead.

        Kwargs:
            tries (int): Number of times to try (not retry) before giving up
                default=10
            delay (int or float): Initial delay between retries in seconds
                default=3
            backoff (int or float): backoff multiplier e.g. value of 2 will
                double the delay each retry
                default=1.1
        """
        return cls.exponential_backoff(
            retries=tries - 1, delay=delay, backoff=backoff, max_delay=None, catch_extra_error_codes=catch_extra_error_codes)
