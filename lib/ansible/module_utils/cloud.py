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

from ansible.module_utils.cloud import *

The 'cloud' module provides the following common classes:

    * CloudRetry
        - The base class to be used by other cloud providers, in order to
          provide a backoff/retry decorator based on status codes.

        - Example using the AWSRetry class which inherits from CloudRetry.
          @AWSRetry.retry(tries=20, delay=2, backoff=2)
          get_ec2_security_group_ids_from_names()

"""
from functools import wraps
import syslog
import time

from ansible.module_utils.pycompat24 import get_exception


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
    def found(response_code):
        """ Return True if the Response Code to retry on was found.
        Args:
            response_code (str): This is the Response Code that is being matched against.
        """
        pass

    @classmethod
    def backoff(cls, tries=10, delay=3, backoff=1.1):
        """ Retry calling the Cloud decorated function using an exponential backoff.
        Kwargs:
            tries (int): Number of times to try (not retry) before giving up
                default=10
            delay (int): Initial delay between retries in seconds
                default=3
            backoff (int): backoff multiplier e.g. value of 2 will double the delay each retry
                default=2

        """
        def deco(f):
            @wraps(f)
            def retry_func(*args, **kwargs):
                max_tries, max_delay = tries, delay
                while max_tries > 1:
                    try:
                        return f(*args, **kwargs)
                    except Exception:
                        e = get_exception()
                        if isinstance(e, cls.base_class):
                            response_code = cls.status_code_from_exception(e)
                            if cls.found(response_code):
                                msg = "{0}: Retrying in {1} seconds...".format(str(e), max_delay)
                                syslog.syslog(syslog.LOG_INFO, msg)
                                time.sleep(max_delay)
                                max_tries -= 1
                                max_delay *= backoff
                            else:
                                # Return original exception if exception is not a ClientError
                                raise e
                        else:
                            # Return original exception if exception is not a ClientError
                            raise e
                return f(*args, **kwargs)

            return retry_func  # true decorator

        return deco
