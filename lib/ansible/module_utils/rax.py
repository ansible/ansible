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

def rax_argument_spec():
    return dict(
        api_key=dict(type='str', aliases=['password'], no_log=True),
        auth_endpoint=dict(type='str'),
        credentials=dict(type='str', aliases=['creds_file']),
        env=dict(type='str'),
        identity_type=dict(type='str', default='rackspace'),
        region=dict(type='str'),
        tenant_id=dict(type='str'),
        tenant_name=dict(type='str'),
        username=dict(type='str'),
        verify_ssl=dict(choices=BOOLEANS, type='bool'),
    )


def rax_required_together():
    return [['api_key', 'username']]


def setup_rax_module(module, rax_module):
    api_key = module.params.get('api_key')
    auth_endpoint = module.params.get('auth_endpoint')
    credentials = module.params.get('credentials')
    env = module.params.get('env')
    identity_type = module.params.get('identity_type')
    region = module.params.get('region')
    tenant_id = module.params.get('tenant_id')
    tenant_name = module.params.get('tenant_name')
    username = module.params.get('username')
    verify_ssl = module.params.get('verify_ssl')

    if env is not None:
        rax_module.set_environment(env)

    rax_module.set_setting('identity_type', identity_type)
    if verify_ssl is not None:
        rax_module.set_setting('verify_ssl', verify_ssl)
    if auth_endpoint is not None:
        rax_module.set_setting('auth_endpoint', auth_endpoint)
    if tenant_id is not None:
        rax_module.set_setting('tenant_id', tenant_id)
    if tenant_name is not None:
        rax_module.set_setting('tenant_name', tenant_name)

    try:
        username = username or os.environ.get('RAX_USERNAME')
        if not username:
            username = rax_module.get_setting('keyring_username')
            if username:
                api_key = 'USE_KEYRING'
        if not api_key:
            api_key = os.environ.get('RAX_API_KEY')
        credentials = (credentials or os.environ.get('RAX_CREDENTIALS') or
                       os.environ.get('RAX_CREDS_FILE'))
        region = (region or os.environ.get('RAX_REGION') or
                  rax_module.get_setting('region'))
    except KeyError, e:
        module.fail_json(msg='Unable to load %s' % e.message)

    try:
        if api_key and username:
            if api_key == 'USE_KEYRING':
                rax_module.keyring_auth(username, region=region)
            else:
                rax_module.set_credentials(username, api_key=api_key,
                                           region=region)
        elif credentials:
            credentials = os.path.expanduser(credentials)
            rax_module.set_credential_file(credentials, region=region)
        else:
            raise Exception('No credentials supplied!')
    except Exception, e:
        module.fail_json(msg='%s' % e.message)

    return rax_module
