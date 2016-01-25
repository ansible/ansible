# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Michael DeHaan <michael.dehaan@gmail.com>, 2012-2013
# All rights reserved.
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
import os

try:
    import boto3
    HAS_BOTO3 = True
except:
    HAS_BOTO3 = False

try:
    from distutils.version import LooseVersion
    HAS_LOOSE_VERSION = True
except:
    HAS_LOOSE_VERSION = False


class AnsibleAWSError(Exception):
    pass


def boto3_conn(module, conn_type=None, resource=None, region=None, endpoint=None, **params):
    profile = params.pop('profile_name', None)
    params['aws_session_token'] = params.pop('security_token', None)
    params['verify'] = params.pop('validate_certs', None)

    if conn_type not in ['both', 'resource', 'client']:
        module.fail_json(msg='There is an issue in the code of the module. You must specify either both, resource or client to the conn_type parameter in the boto3_conn function call')

    if conn_type == 'resource':
        resource = boto3.session.Session(profile_name=profile).resource(resource, region_name=region, endpoint_url=endpoint, **params)
        return resource
    elif conn_type == 'client':
        client = boto3.session.Session(profile_name=profile).client(resource, region_name=region, endpoint_url=endpoint, **params)
        return client
    else:
        resource = boto3.session.Session(profile_name=profile).resource(resource, region_name=region, endpoint_url=endpoint, **params)
        client = boto3.session.Session(profile_name=profile).client(resource, region_name=region, endpoint_url=endpoint, **params)
        return client, resource


def aws_common_argument_spec():
    return dict(
        ec2_url=dict(),
        aws_secret_key=dict(aliases=['ec2_secret_key', 'secret_key'], no_log=True),
        aws_access_key=dict(aliases=['ec2_access_key', 'access_key']),
        validate_certs=dict(default=True, type='bool'),
        security_token=dict(aliases=['access_token'], no_log=True),
        profile=dict(),
    )


def ec2_argument_spec():
    spec = aws_common_argument_spec()
    spec.update(
        dict(
            region=dict(aliases=['aws_region', 'ec2_region']),
        )
    )
    return spec


def boto_supports_profile_name():
    return hasattr(boto.ec2.EC2Connection, 'profile_name')


def get_aws_connection_info(module, boto3=False):

    # Check module args for credentials, then check environment vars
    # access_key

    ec2_url = (module.params.get('ec2_url') or
               os.environ.get('AWS_URL') or
               os.environ.get('EC2_URL'))

    access_key = (module.params.get('aws_access_key') or
                  os.environ.get('AWS_ACCESS_KEY_ID') or
                  os.environ.get('AWS_ACCESS_KEY') or
                  os.environ.get('EC2_ACCESS_KEY'))

    secret_key = (module.params.get('aws_secret_key') or
                  os.environ.get('AWS_SECRET_ACCESS_KEY') or
                  os.environ.get('AWS_SECRET_KEY') or
                  os.environ.get('EC2_SECRET_KEY'))

    security_token = (module.params.get('security_token') or
                      os.environ.get('AWS_SECURITY_TOKEN') or
                      os.environ.get('EC2_SECURITY_TOKEN'))

    region = (module.params.get('region') or
              os.environ.get('AWS_REGION') or
              os.environ.get('AWS_DEFAULT_REGION') or
              os.environ.get('EC2_REGION') or
              boto.config.get('Boto', 'aws_region') or
              boto.config.get('Boto', 'ec2_region'))

    profile_name = module.params.get('profile')
    validate_certs = module.params.get('validate_certs')

    if HAS_BOTO3 and boto3:
        boto_params = dict(aws_access_key_id=access_key,
                           aws_secret_access_key=secret_key,
                           aws_session_token=security_token)
        if validate_certs:
            boto_params['verify'] = validate_certs

        if profile_name:
            boto_params['profile_name'] = profile_name

    else:
        boto_params = dict(aws_access_key_id=access_key,
                           aws_secret_access_key=secret_key,
                           security_token=security_token)

        # profile_name only works as a key in boto >= 2.24
        # so only set profile_name if passed as an argument
        if profile_name:
            if not boto_supports_profile_name():
                module.fail_json("boto does not support profile_name before 2.24")
            boto_params['profile_name'] = profile_name

        if validate_certs and HAS_LOOSE_VERSION and LooseVersion(boto.Version) >= LooseVersion("2.6.0"):
            boto_params['validate_certs'] = validate_certs

    for param, value in boto_params.items():
        if isinstance(value, str):
            boto_params[param] = unicode(value, 'utf-8', 'strict')

    return region, ec2_url, boto_params


def get_ec2_creds(module):
    ''' for compatibility mode with old modules that don't/can't yet
        use ec2_connect method '''
    region, ec2_url, boto_params = get_aws_connection_info(module)
    return ec2_url, boto_params['aws_access_key_id'], boto_params['aws_secret_access_key'], region


def boto_fix_security_token_in_profile(conn, profile_name):
    ''' monkey patch for boto issue boto/boto#2100 '''
    profile = 'profile ' + profile_name
    if boto.config.has_option(profile, 'aws_security_token'):
        conn.provider.set_security_token(boto.config.get(profile, 'aws_security_token'))
    return conn


def connect_to_aws(aws_module, region, **params):
    conn = aws_module.connect_to_region(region, **params)
    if not conn:
        if region not in [aws_module_region.name for aws_module_region in aws_module.regions()]:
            raise AnsibleAWSError("Region %s does not seem to be available for aws module %s. If the region definitely exists, you may need to upgrade boto or extend with endpoints_path" % (region, aws_module.__name__))
        else:
            raise AnsibleAWSError("Unknown problem connecting to region %s for aws module %s." % (region, aws_module.__name__))
    if params.get('profile_name'):
        conn = boto_fix_security_token_in_profile(conn, params['profile_name'])
    return conn


def ec2_connect(module):

    """ Return an ec2 connection"""

    region, ec2_url, boto_params = get_aws_connection_info(module)

    # If we have a region specified, connect to its endpoint.
    if region:
        try:
            ec2 = connect_to_aws(boto.ec2, region, **boto_params)
        except (boto.exception.NoAuthHandlerFound, AnsibleAWSError), e:
            module.fail_json(msg=str(e))
    # Otherwise, no region so we fallback to the old connection method
    elif ec2_url:
        try:
            ec2 = boto.connect_ec2_endpoint(ec2_url, **boto_params)
        except (boto.exception.NoAuthHandlerFound, AnsibleAWSError), e:
            module.fail_json(msg=str(e))
    else:
        module.fail_json(msg="Either region or ec2_url must be specified")

    return ec2
