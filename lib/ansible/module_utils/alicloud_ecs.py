# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c) 2017-present Alibaba Group Holding Limited. He Guimin <heguimin36@163.com>
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

import os
import json
from ansible.module_utils.basic import env_fallback

try:
    import footmark
    import footmark.ecs
    import footmark.slb
    import footmark.vpc
    import footmark.rds
    import footmark.ess
    import footmark.sts
    import footmark.dns
    import footmark.ram
    import footmark.market
    HAS_FOOTMARK = True
except ImportError:
    HAS_FOOTMARK = False


class AnsibleACSError(Exception):
    pass


def acs_common_argument_spec():
    return dict(
        alicloud_access_key=dict(aliases=['access_key_id', 'access_key'], no_log=True,
                                 fallback=(env_fallback, ['ALICLOUD_ACCESS_KEY', 'ALICLOUD_ACCESS_KEY_ID'])),
        alicloud_secret_key=dict(aliases=['secret_access_key', 'secret_key'], no_log=True,
                                 fallback=(env_fallback, ['ALICLOUD_SECRET_KEY', 'ALICLOUD_SECRET_ACCESS_KEY'])),
        alicloud_security_token=dict(aliases=['security_token'], no_log=True,
                                     fallback=(env_fallback, ['ALICLOUD_SECURITY_TOKEN'])),
        ecs_role_name=dict(aliases=['role_name'], fallback=(env_fallback, ['ALICLOUD_ECS_ROLE_NAME']))
    )


def ecs_argument_spec():
    spec = acs_common_argument_spec()
    spec.update(
        dict(
            alicloud_region=dict(required=True, aliases=['region', 'region_id'],
                                 fallback=(env_fallback, ['ALICLOUD_REGION', 'ALICLOUD_REGION_ID'])),
            alicloud_assume_role_arn=dict(fallback=(env_fallback, ['ALICLOUD_ASSUME_ROLE_ARN']), aliases=['assume_role_arn']),
            alicloud_assume_role_session_name=dict(fallback=(env_fallback, ['ALICLOUD_ASSUME_ROLE_SESSION_NAME']), aliases=['assume_role_session_name']),
            alicloud_assume_role_session_expiration=dict(type='int', fallback=(env_fallback, ['ALICLOUD_ASSUME_ROLE_SESSION_EXPIRATION']), aliases=['assume_role_session_expiration']),
            alicloud_assume_role=dict(type='dict', aliases=['assume_role']),
            profile=dict(fallback=(env_fallback, ['ALICLOUD_PROFILE'])),
            shared_credentials_file=dict(fallback=(env_fallback, ['ALICLOUD_SHARED_CREDENTIALS_FILE']))
        )
    )
    return spec


def get_acs_connection_info(params):

    ecs_params = dict(acs_access_key_id=params.get('alicloud_access_key'),
                      acs_secret_access_key=params.get('alicloud_secret_key'),
                      security_token=params.get('alicloud_security_token'),
                      ecs_role_name=params.get('ecs_role_name'),
                      user_agent='Ansible-Provider-Alicloud')
    return ecs_params


def connect_to_acs(acs_module, region, **params):
    conn = acs_module.connect_to_region(region, **params)
    if not conn:
        if region not in [acs_module_region.id for acs_module_region in acs_module.regions()]:
            raise AnsibleACSError(
                "Region %s does not seem to be available for acs module %s." % (region, acs_module.__name__))
        else:
            raise AnsibleACSError(
                "Unknown problem connecting to region %s for acs module %s." % (region, acs_module.__name__))
    return conn


def get_assume_role(params):
    """ Return new params """
    sts_params = get_acs_connection_info(params)
    assume_role = {}
    if params.get('assume_role'):
        assume_role['alicloud_assume_role_arn'] = params['assume_role'].get('role_arn')
        assume_role['alicloud_assume_role_session_name'] = params['assume_role'].get('session_name')
        assume_role['alicloud_assume_role_session_expiration'] = params['assume_role'].get('session_expiration')
        assume_role['alicloud_assume_role_policy'] = params['assume_role'].get('policy')

    assume_role_params = {
        'role_arn': params.get('alicloud_assume_role_arn') if params.get('alicloud_assume_role_arn') else assume_role.get('alicloud_assume_role_arn'),
        'role_session_name': params.get('alicloud_assume_role_session_name') if params.get('alicloud_assume_role_session_name') else assume_role.get('alicloud_assume_role_session_name'),
        'duration_seconds': params.get('alicloud_assume_role_session_expiration') if params.get('alicloud_assume_role_session_expiration') else assume_role.get('alicloud_assume_role_session_expiration', 3600),
        'policy': assume_role.get('alicloud_assume_role_policy', {})
    }

    try:
        sts = connect_to_acs(footmark.sts, params.get('alicloud_region'), **sts_params).assume_role(**assume_role_params).read()
        sts_params['acs_access_key_id'], sts_params['acs_secret_access_key'], sts_params['security_token'] \
            = sts['access_key_id'], sts['access_key_secret'], sts['security_token']
    except AnsibleACSError as e:
        params.fail_json(msg=str(e))
    return sts_params


def get_profile(params):
    if not params['alicloud_access_key'] and not params['ecs_role_name'] and params['profile']:
        path = params['shared_credentials_file'] if params['shared_credentials_file'] else os.getenv('HOME')+'/.aliyun/config.json'
        auth = {}
        with open(path, 'r') as f:
            for pro in json.load(f)['profiles']:
                if params['profile'] == pro['name']:
                    auth = pro
        if auth:
            if auth['mode'] == 'AK' and auth.get('access_key_id') and auth.get('access_key_secret'):
                params['alicloud_access_key'] = auth.get('access_key_id')
                params['alicloud_secret_key'] = auth.get('access_key_secret')
                params['alicloud_region'] = auth.get('region_id')
                params = get_acs_connection_info(params)
            elif auth['mode'] == 'StsToken' and auth.get('access_key_id') and auth.get('access_key_secret') and auth.get('sts_token'):
                params['alicloud_access_key'] = auth.get('access_key_id')
                params['alicloud_secret_key'] = auth.get('access_key_secret')
                params['security_token'] = auth.get('sts_token')
                params['alicloud_region'] = auth.get('region_id')
                params = get_acs_connection_info(params)
            elif auth['mode'] == 'EcsRamRole':
                params['ecs_role_name'] = auth.get('ram_role_name')
                params['alicloud_region'] = auth.get('region_id')
                params = get_acs_connection_info(params)
            elif auth['mode'] == 'RamRoleArn' and auth.get('ram_role_arn'):
                params['alicloud_access_key'] = auth.get('access_key_id')
                params['alicloud_secret_key'] = auth.get('access_key_secret')
                params['security_token'] = auth.get('sts_token')
                params['ecs_role_name'] = auth.get('ram_role_name')
                params['alicloud_assume_role_arn'] = auth.get('ram_role_arn')
                params['alicloud_assume_role_session_name'] = auth.get('ram_session_name')
                params['alicloud_assume_role_session_expiration'] = auth.get('expired_seconds')
                params['alicloud_region'] = auth.get('region_id')
                params = get_assume_role(params)
    elif params.get('alicloud_assume_role_arn') or params.get('assume_role'):
        params = get_assume_role(params)
    else:
        params = get_acs_connection_info(params)
    return params


def ecs_connect(module):
    """ Return an ecs connection"""
    ecs_params = get_profile(module.params)
    # If we have a region specified, connect to its endpoint.
    region = module.params.get('alicloud_region')
    if region:
        try:
            ecs = connect_to_acs(footmark.ecs, region, **ecs_params)
        except AnsibleACSError as e:
            module.fail_json(msg=str(e))
    # Otherwise, no region so we fallback to the old connection method
    return ecs


def slb_connect(module):
    """ Return an slb connection"""
    slb_params = get_profile(module.params)
    # If we have a region specified, connect to its endpoint.
    region = module.params.get('alicloud_region')
    if region:
        try:
            slb = connect_to_acs(footmark.slb, region, **slb_params)
        except AnsibleACSError as e:
            module.fail_json(msg=str(e))
    # Otherwise, no region so we fallback to the old connection method
    return slb


def dns_connect(module):
    """ Return an dns connection"""
    dns_params = get_profile(module.params)
    # If we have a region specified, connect to its endpoint.
    region = module.params.get('alicloud_region')
    if region:
        try:
            dns = connect_to_acs(footmark.dns, region, **dns_params)
        except AnsibleACSError as e:
            module.fail_json(msg=str(e))
    # Otherwise, no region so we fallback to the old connection method
    return dns


def vpc_connect(module):
    """ Return an vpc connection"""
    vpc_params = get_profile(module.params)
    # If we have a region specified, connect to its endpoint.
    region = module.params.get('alicloud_region')
    if region:
        try:
            vpc = connect_to_acs(footmark.vpc, region, **vpc_params)
        except AnsibleACSError as e:
            module.fail_json(msg=str(e))
    # Otherwise, no region so we fallback to the old connection method
    return vpc


def rds_connect(module):
    """ Return an rds connection"""
    rds_params = get_profile(module.params)
    # If we have a region specified, connect to its endpoint.
    region = module.params.get('alicloud_region')
    if region:
        try:
            rds = connect_to_acs(footmark.rds, region, **rds_params)
        except AnsibleACSError as e:
            module.fail_json(msg=str(e))
    # Otherwise, no region so we fallback to the old connection method
    return rds


def ess_connect(module):
    """ Return an ess connection"""
    ess_params = get_profile(module.params)
    # If we have a region specified, connect to its endpoint.
    region = module.params.get('alicloud_region')
    if region:
        try:
            ess = connect_to_acs(footmark.ess, region, **ess_params)
        except AnsibleACSError as e:
            module.fail_json(msg=str(e))
    # Otherwise, no region so we fallback to the old connection method
    return ess


def sts_connect(module):
    """ Return an sts connection"""
    sts_params = get_profile(module.params)
    # If we have a region specified, connect to its endpoint.
    region = module.params.get('alicloud_region')
    if region:
        try:
            sts = connect_to_acs(footmark.sts, region, **sts_params)
        except AnsibleACSError as e:
            module.fail_json(msg=str(e))
    # Otherwise, no region so we fallback to the old connection method
    return sts


def ram_connect(module):
    """ Return an ram connection"""
    ram_params = get_profile(module.params)
    # If we have a region specified, connect to its endpoint.
    region = module.params.get('alicloud_region')
    if region:
        try:
            ram = connect_to_acs(footmark.ram, region, **ram_params)
        except AnsibleACSError as e:
            module.fail_json(msg=str(e))
    # Otherwise, no region so we fallback to the old connection method
    return ram


def market_connect(module):
    """ Return an market connection"""
    market_params = get_profile(module.params)
    # If we have a region specified, connect to its endpoint.
    region = module.params.get('alicloud_region')
    if region:
        try:
            market = connect_to_acs(footmark.market, region, **market_params)
        except AnsibleACSError as e:
            module.fail_json(msg=str(e))
    # Otherwise, no region so we fallback to the old connection method
    return market
