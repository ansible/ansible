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

try:
    from distutils.version import LooseVersion
    HAS_LOOSE_VERSION = True
except:
    HAS_LOOSE_VERSION = False

AWS_REGIONS = [
    'ap-northeast-1',
    'ap-southeast-1',
    'ap-southeast-2',
    'cn-north-1',
    'eu-central-1',
    'eu-west-1',
    'eu-central-1',
    'sa-east-1',
    'us-east-1',
    'us-west-1',
    'us-west-2',
    'us-gov-west-1',
]


def aws_common_argument_spec():
    return dict(
        ec2_url=dict(),
        aws_secret_key=dict(aliases=['ec2_secret_key', 'secret_key'], no_log=True),
        aws_access_key=dict(aliases=['ec2_access_key', 'access_key']),
        validate_certs=dict(default=True, type='bool'),
        security_token=dict(no_log=True),
        profile=dict(),
    )


def ec2_argument_spec():
    spec = aws_common_argument_spec()
    spec.update(
        dict(
            region=dict(aliases=['aws_region', 'ec2_region'], choices=AWS_REGIONS),
        )
    )
    return spec


def boto_supports_profile_name():
    return hasattr(boto.ec2.EC2Connection, 'profile_name')


def get_aws_connection_info(module):

    # Check module args for credentials, then check environment vars
    # access_key

    ec2_url = module.params.get('ec2_url')
    access_key = module.params.get('aws_access_key')
    secret_key = module.params.get('aws_secret_key')
    security_token = module.params.get('security_token')
    region = module.params.get('region')
    profile_name = module.params.get('profile')
    validate_certs = module.params.get('validate_certs')

    if not ec2_url:
        if 'EC2_URL' in os.environ:
            ec2_url = os.environ['EC2_URL']
        elif 'AWS_URL' in os.environ:
            ec2_url = os.environ['AWS_URL']

    if not access_key:
        if 'EC2_ACCESS_KEY' in os.environ:
            access_key = os.environ['EC2_ACCESS_KEY']
        elif 'AWS_ACCESS_KEY_ID' in os.environ:
            access_key = os.environ['AWS_ACCESS_KEY_ID']
        elif 'AWS_ACCESS_KEY' in os.environ:
            access_key = os.environ['AWS_ACCESS_KEY']
        else:
            # in case access_key came in as empty string
            access_key = None

    if not secret_key:
        if 'EC2_SECRET_KEY' in os.environ:
            secret_key = os.environ['EC2_SECRET_KEY']
        elif 'AWS_SECRET_ACCESS_KEY' in os.environ:
            secret_key = os.environ['AWS_SECRET_ACCESS_KEY']
        elif 'AWS_SECRET_KEY' in os.environ:
            secret_key = os.environ['AWS_SECRET_KEY']
        else:
            # in case secret_key came in as empty string
            secret_key = None

    if not region:
        if 'EC2_REGION' in os.environ:
            region = os.environ['EC2_REGION']
        elif 'AWS_REGION' in os.environ:
            region = os.environ['AWS_REGION']
        else:
            # boto.config.get returns None if config not found
            region = boto.config.get('Boto', 'aws_region')
            if not region:
                region = boto.config.get('Boto', 'ec2_region')

    if not security_token:
        if 'AWS_SECURITY_TOKEN' in os.environ:
            security_token = os.environ['AWS_SECURITY_TOKEN']
        else:
            # in case security_token came in as empty string
            security_token = None

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
            raise StandardError("Region %s does not seem to be available for aws module %s. If the region definitely exists, you may need to upgrade boto" % (region, aws_module.__name__))
        else:
            raise StandardError("Unknown problem connecting to region %s for aws module %s." % (region, aws_module.__name__))
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
        except (boto.exception.NoAuthHandlerFound, StandardError), e:
            module.fail_json(msg=str(e))
    # Otherwise, no region so we fallback to the old connection method
    elif ec2_url:
        try:
            ec2 = boto.connect_ec2_endpoint(ec2_url, **boto_params)
        except (boto.exception.NoAuthHandlerFound, StandardError), e:
            module.fail_json(msg=str(e))
    else:
        module.fail_json(msg="Either region or ec2_url must be specified")

    return ec2
