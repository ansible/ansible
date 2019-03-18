#
#  Copyright 2017 Michael De La Rue | Ansible
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


"""This module adds shared support for generic Amazon AWS modules

**This code is not yet ready for use in user modules.  As of 2017**
**and through to 2018, the interface is likely to change**
**aggressively as the exact correct interface for ansible AWS modules**
**is identified.  In particular, until this notice goes away or is**
**changed, methods may disappear from the interface.  Please don't**
**publish modules using this except directly to the main Ansible**
**development repository.**

In order to use this module, include it as part of a custom
module as shown below.

  from ansible.module_utils.aws import AnsibleAWSModule
  module = AnsibleAWSModule(argument_spec=dictionary, supports_check_mode=boolean
                            mutually_exclusive=list1, required_together=list2)

The 'AnsibleAWSModule' module provides similar, but more restricted,
interfaces to the normal Ansible module.  It also includes the
additional methods for connecting to AWS using the standard module arguments

    m.resource('lambda') # - get an AWS connection as a boto3 resource.

or

    m.client('sts') # - get an AWS connection as a boto3 client.

To make use of AWSRetry easier, it can now be wrapped around any call from a
module-created client. To add retries to a client, create a client:

    m.client('ec2', retry_decorator=AWSRetry.jittered_backoff(retries=10))

Any calls from that client can be made to use the decorator passed at call-time
using the `aws_retry` argument. By default, no retries are used.

    ec2 = m.client('ec2', retry_decorator=AWSRetry.jittered_backoff(retries=10))
    ec2.describe_instances(InstanceIds=['i-123456789'], aws_retry=True)

The call will be retried the specified number of times, so the calling functions
don't need to be wrapped in the backoff decorator.

"""

import re
import logging
import traceback
from functools import wraps
from distutils.version import LooseVersion

try:
    from cStringIO import StringIO
except ImportError:
    # Python 3
    from io import StringIO

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils._text import to_native
from ansible.module_utils.ec2 import HAS_BOTO3, camel_dict_to_snake_dict, ec2_argument_spec, boto3_conn, get_aws_connection_info

# We will also export HAS_BOTO3 so end user modules can use it.
__all__ = ('AnsibleAWSModule', 'HAS_BOTO3', 'is_boto3_error_code')


class AnsibleAWSModule(object):
    """An ansible module class for AWS modules

    AnsibleAWSModule provides an a class for building modules which
    connect to Amazon Web Services.  The interface is currently more
    restricted than the basic module class with the aim that later the
    basic module class can be reduced.  If you find that any key
    feature is missing please contact the author/Ansible AWS team
    (available on #ansible-aws on IRC) to request the additional
    features needed.
    """
    default_settings = {
        "default_args": True,
        "check_boto3": True,
        "auto_retry": True,
        "module_class": AnsibleModule
    }

    def __init__(self, **kwargs):
        local_settings = {}
        for key in AnsibleAWSModule.default_settings:
            try:
                local_settings[key] = kwargs.pop(key)
            except KeyError:
                local_settings[key] = AnsibleAWSModule.default_settings[key]
        self.settings = local_settings

        if local_settings["default_args"]:
            # ec2_argument_spec contains the region so we use that; there's a patch coming which
            # will add it to aws_argument_spec so if that's accepted then later we should change
            # over
            argument_spec_full = ec2_argument_spec()
            try:
                argument_spec_full.update(kwargs["argument_spec"])
            except (TypeError, NameError):
                pass
            kwargs["argument_spec"] = argument_spec_full

        self._module = AnsibleAWSModule.default_settings["module_class"](**kwargs)

        if local_settings["check_boto3"] and not HAS_BOTO3:
            self._module.fail_json(
                msg=missing_required_lib('botocore or boto3'))

        self.check_mode = self._module.check_mode
        self._diff = self._module._diff
        self._name = self._module._name

        self._botocore_endpoint_log_stream = StringIO()
        self.logger = None
        if self.params.get('debug_botocore_endpoint_logs'):
            self.logger = logging.getLogger('botocore.endpoint')
            self.logger.setLevel(logging.DEBUG)
            self.logger.addHandler(logging.StreamHandler(self._botocore_endpoint_log_stream))

    @property
    def params(self):
        return self._module.params

    def _get_resource_action_list(self):
        actions = []
        for ln in self._botocore_endpoint_log_stream.getvalue().split('\n'):
            ln = ln.strip()
            if not ln:
                continue
            found_operational_request = re.search(r"OperationModel\(name=.*?\)", ln)
            if found_operational_request:
                operation_request = found_operational_request.group(0)[20:-1]
                resource = re.search(r"https://.*?\.", ln).group(0)[8:-1]
                actions.append("{0}:{1}".format(resource, operation_request))
        return list(set(actions))

    def exit_json(self, *args, **kwargs):
        if self.params.get('debug_botocore_endpoint_logs'):
            kwargs['resource_actions'] = self._get_resource_action_list()
        return self._module.exit_json(*args, **kwargs)

    def fail_json(self, *args, **kwargs):
        if self.params.get('debug_botocore_endpoint_logs'):
            kwargs['resource_actions'] = self._get_resource_action_list()
        return self._module.fail_json(*args, **kwargs)

    def debug(self, *args, **kwargs):
        return self._module.debug(*args, **kwargs)

    def warn(self, *args, **kwargs):
        return self._module.warn(*args, **kwargs)

    def deprecate(self, *args, **kwargs):
        return self._module.deprecate(*args, **kwargs)

    def boolean(self, *args, **kwargs):
        return self._module.boolean(*args, **kwargs)

    def md5(self, *args, **kwargs):
        return self._module.md5(*args, **kwargs)

    def client(self, service, retry_decorator=None):
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(self, boto3=True)
        conn = boto3_conn(self, conn_type='client', resource=service,
                          region=region, endpoint=ec2_url, **aws_connect_kwargs)
        return conn if retry_decorator is None else _RetryingBotoClientWrapper(conn, retry_decorator)

    def resource(self, service):
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(self, boto3=True)
        return boto3_conn(self, conn_type='resource', resource=service,
                          region=region, endpoint=ec2_url, **aws_connect_kwargs)

    def fail_json_aws(self, exception, msg=None):
        """call fail_json with processed exception

        function for converting exceptions thrown by AWS SDK modules,
        botocore, boto3 and boto, into nice error messages.
        """
        last_traceback = traceback.format_exc()

        # to_native is trusted to handle exceptions that str() could
        # convert to text.
        try:
            except_msg = to_native(exception.message)
        except AttributeError:
            except_msg = to_native(exception)

        if msg is not None:
            message = '{0}: {1}'.format(msg, except_msg)
        else:
            message = except_msg

        try:
            response = exception.response
        except AttributeError:
            response = None

        failure = dict(
            msg=message,
            exception=last_traceback,
            **self._gather_versions()
        )

        if response is not None:
            failure.update(**camel_dict_to_snake_dict(response))

        self.fail_json(**failure)

    def _gather_versions(self):
        """Gather AWS SDK (boto3 and botocore) dependency versions

        Returns {'boto3_version': str, 'botocore_version': str}
        Returns {} if neither are installed
        """
        if not HAS_BOTO3:
            return {}
        import boto3
        import botocore
        return dict(boto3_version=boto3.__version__,
                    botocore_version=botocore.__version__)

    def boto3_at_least(self, desired):
        """Check if the available boto3 version is greater than or equal to a desired version.

        Usage:
            if module.params.get('assign_ipv6_address') and not module.boto3_at_least('1.4.4'):
                # conditionally fail on old boto3 versions if a specific feature is not supported
                module.fail_json(msg="Boto3 can't deal with EC2 IPv6 addresses before version 1.4.4.")
        """
        existing = self._gather_versions()
        return LooseVersion(existing['boto3_version']) >= LooseVersion(desired)

    def botocore_at_least(self, desired):
        """Check if the available botocore version is greater than or equal to a desired version.

        Usage:
            if not module.botocore_at_least('1.2.3'):
                module.fail_json(msg='The Serverless Elastic Load Compute Service is not in botocore before v1.2.3')
            if not module.botocore_at_least('1.5.3'):
                module.warn('Botocore did not include waiters for Service X before 1.5.3. '
                            'To wait until Service X resources are fully available, update botocore.')
        """
        existing = self._gather_versions()
        return LooseVersion(existing['botocore_version']) >= LooseVersion(desired)


class _RetryingBotoClientWrapper(object):
    __never_wait = (
        'get_paginator', 'can_paginate',
        'get_waiter', 'generate_presigned_url',
    )

    def __init__(self, client, retry):
        self.client = client
        self.retry = retry

    def _create_optional_retry_wrapper_function(self, unwrapped):
        retrying_wrapper = self.retry(unwrapped)

        @wraps(unwrapped)
        def deciding_wrapper(aws_retry=False, *args, **kwargs):
            if aws_retry:
                return retrying_wrapper(*args, **kwargs)
            else:
                return unwrapped(*args, **kwargs)
        return deciding_wrapper

    def __getattr__(self, name):
        unwrapped = getattr(self.client, name)
        if name in self.__never_wait:
            return unwrapped
        elif callable(unwrapped):
            wrapped = self._create_optional_retry_wrapper_function(unwrapped)
            setattr(self, name, wrapped)
            return wrapped
        else:
            return unwrapped


def is_boto3_error_code(code, e=None):
    """Check if the botocore exception is raised by a specific error code.

    Returns ClientError if the error code matches, a dummy exception if it does not have an error code or does not match

    Example:
    try:
        ec2.describe_instances(InstanceIds=['potato'])
    except is_boto3_error_code('InvalidInstanceID.Malformed'):
        # handle the error for that code case
    except botocore.exceptions.ClientError as e:
        # handle the generic error case for all other codes
    """
    from botocore.exceptions import ClientError
    if e is None:
        import sys
        dummy, e, dummy = sys.exc_info()
    if isinstance(e, ClientError) and e.response['Error']['Code'] == code:
        return ClientError
    return type('NeverEverRaisedException', (Exception,), {})


def get_boto3_client_method_parameters(client, method_name, required=False):
    op = client.meta.method_to_api_mapping.get(method_name)
    input_shape = client._service_model.operation_model(op).input_shape
    if not input_shape:
        parameters = []
    elif required:
        parameters = list(input_shape.required_members)
    else:
        parameters = list(input_shape.members.keys())
    return parameters
