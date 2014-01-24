import os


def rax_argument_spec():
    auth_endpoint = 'https://identity.api.rackspacecloud.com/v2.0/'
    return dict(
        api_key=dict(type='str', aliases=['password'], no_log=True),
        auth_endpoint=dict(type='str', default=auth_endpoint),
        credentials=dict(type='str', aliases=['creds_file']),
        identity_type=dict(type='str', default='rackspace'),
        region=dict(type='str'),
        tenant_id=dict(type='str'),
        username=dict(type='str'),
        verify_ssl=dict(choices=BOOLEANS, default=True, type='bool'),
    )


def rax_required_together():
    return [['api_key', 'username']]


def setup_rax_module(module, rax_module):
    api_key = module.params.get('api_key')
    auth_endpoint = module.params.get('auth_endpoint')
    credentials = module.params.get('credentials')
    identity_type = module.params.get('identity_type')
    region = module.params.get('region')
    tenant_id = module.params.get('tenant_id')
    username = module.params.get('username')
    verify_ssl = module.params.get('verify_ssl')

    rax_module.set_setting('identity_type', identity_type)
    rax_module.set_setting('verify_ssl', verify_ssl)
    rax_module.set_setting('auth_endpoint', auth_endpoint)
    if tenant_id:
        rax_module.set_setting('tenant_id', tenant_id)

    try:
        username = username or os.environ.get('RAX_USERNAME')
        api_key = api_key or os.environ.get('RAX_API_KEY')
        credentials = (credentials or os.environ.get('RAX_CREDENTIALS') or
                       os.environ.get('RAX_CREDS_FILE'))
        region = region or os.environ.get('RAX_REGION')
    except KeyError, e:
        module.fail_json(msg='Unable to load %s' % e.message)

    try:
        if api_key and username:
            if api_key == 'USE_KEYRING':
                rax_module.keyring_auth(username)
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
