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

AWS_REGIONS = ['ap-northeast-1',
               'ap-southeast-1',
               'ap-southeast-2',
               'eu-west-1',
               'sa-east-1',
               'us-east-1',
               'us-west-1',
               'us-west-2']


def ec2_argument_keys_spec():
    return dict(
        aws_secret_key=dict(aliases=['ec2_secret_key', 'secret_key'], no_log=True),
        aws_access_key=dict(aliases=['ec2_access_key', 'access_key']),
    )


def ec2_argument_spec():
    spec = ec2_argument_keys_spec()
    spec.update(
        dict(
            region=dict(aliases=['aws_region', 'ec2_region'], choices=AWS_REGIONS),
            validate_certs=dict(default=True, type='bool'),
            ec2_url=dict(),
        )
    )
    return spec


def get_ec2_creds(module):

    # Check module args for credentials, then check environment vars

    ec2_url = module.params.get('ec2_url')
    ec2_secret_key = module.params.get('aws_secret_key')
    ec2_access_key = module.params.get('aws_access_key')
    region = module.params.get('region')

    if not ec2_url:
        if 'EC2_URL' in os.environ:
            ec2_url = os.environ['EC2_URL']
        elif 'AWS_URL' in os.environ:
            ec2_url = os.environ['AWS_URL']

    if not ec2_access_key:
        if 'EC2_ACCESS_KEY' in os.environ:
            ec2_access_key = os.environ['EC2_ACCESS_KEY']
        elif 'AWS_ACCESS_KEY_ID' in os.environ:
            ec2_access_key = os.environ['AWS_ACCESS_KEY_ID']
        elif 'AWS_ACCESS_KEY' in os.environ:
            ec2_access_key = os.environ['AWS_ACCESS_KEY']

    if not ec2_secret_key:
        if 'EC2_SECRET_KEY' in os.environ:
            ec2_secret_key = os.environ['EC2_SECRET_KEY']
        elif 'AWS_SECRET_ACCESS_KEY' in os.environ:
            ec2_secret_key = os.environ['AWS_SECRET_ACCESS_KEY']
        elif 'AWS_SECRET_KEY' in os.environ:
            ec2_secret_key = os.environ['AWS_SECRET_KEY']

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

    return ec2_url, ec2_access_key, ec2_secret_key, region


def ec2_connect(module):

    """ Return an ec2 connection"""

    ec2_url, aws_access_key, aws_secret_key, region = get_ec2_creds(module)
    validate_certs = module.params.get('validate_certs', True)

    # If we have a region specified, connect to its endpoint.
    if region:
        try:
            if HAS_LOOSE_VERSION and LooseVersion(boto.Version) >= LooseVersion("2.6.0"):
                ec2 = boto.ec2.connect_to_region(region, aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key, validate_certs=validate_certs)
            else:
                ec2 = boto.ec2.connect_to_region(region, aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)
        except boto.exception.NoAuthHandlerFound, e:
            module.fail_json(msg = str(e))
    # Otherwise, no region so we fallback to the old connection method
    elif ec2_url:
        try:
            if HAS_LOOSE_VERSION and LooseVersion(boto.Version) >= LooseVersion("2.6.0"):
                ec2 = boto.connect_ec2_endpoint(ec2_url, aws_access_key, aws_secret_key, validate_certs=validate_certs)
            else:
                ec2 = boto.connect_ec2_endpoint(ec2_url, aws_access_key, aws_secret_key)
        except boto.exception.NoAuthHandlerFound, e:
            module.fail_json(msg = str(e))
    else:
        module.fail_json(msg="Either region or ec2_url must be specified")
    return ec2

