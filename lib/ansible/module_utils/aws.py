# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Ted Timmons <ted@timmons.me>, 2017.
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

# boto3-only AWS modules live here.

# don't duplicate code; bring this in from the old ec2.py util.
from ansible.module_utils.ec2 import AWSRetry,AnsibleAWSError

try:
    import boto3
    import botocore
    HAS_BOTO3 = True
except:
    HAS_BOTO3 = False

def boto_exception(err):
    '''generic error message handler'''
    if hasattr(err, 'error_message'):
        error = err.error_message
    elif hasattr(err, 'message'):
        error = str(err.message) + ' ' + str(err) + ' - ' + str(type(err))
    else:
        error = '%s: %s' % (Exception, err)

    return error

def common_argument_spec():
    return dict(
        ec2_url=dict(),
        aws_secret_key=dict(aliases=['ec2_secret_key', 'secret_key'], no_log=True),
        aws_access_key=dict(aliases=['ec2_access_key', 'access_key']),
        validate_certs=dict(default=True, type='bool'),
        security_token=dict(aliases=['access_token'], no_log=True),
        profile=dict(),
        region=dict(aliases=['aws_region', 'ec2_region']),
    )

def connection(conn_type=None, resource=None, region=None, endpoint_url=None, profile_name=None, validate_certs=True):
    # not taking generic **args, we want to know precisely what we're passing on to boto3.
    # this will expose poorly-named params very easily, and lets us map their key names.

    # note endpoint_url, verify are not valid parameters of a session.
    session = boto3.session.Session(profile_name=profile_name, region_name=region)
    if conn_type == 'session':
        # a session is all that was requested.
        return session

    if conn_type == 'resource':
        return session.resource(resource, endpoint_url=endpoint_url, verify=validate_certs)
    elif conn_type == 'client':
        return session.client(resource, endpoint_url=endpoint_url, verify=validate_certs)

    # we fell out of the 'if' cases above, because they all return.
    raise ValueError('There is an issue in the calling code. You must specify either session, resource, '
                     'or client to the conn_type parameter in the connection function call')

def get_module_aws_arguments(module):
    args = {}

    for k in common_argument_spec().keys():
        if module.params.get(k):
            args[k] = module.params.get(k)

    return args
