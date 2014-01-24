import os


def rax_argument_spec():
    return dict(
        api_key=dict(type='str', no_log=True),
        credentials=dict(type='str', aliases=['creds_file']),
        region=dict(type='str'),
        username=dict(type='str'),
    )


def rax_required_together():
    return [['api_key', 'username']]


def setup_rax_module(module, rax_module):
    api_key = module.params.get('api_key')
    credentials = module.params.get('credentials')
    region = module.params.get('region')
    username = module.params.get('username')

    try:
        username = username or os.environ.get('RAX_USERNAME')
        api_key = api_key or os.environ.get('RAX_API_KEY')
        credentials = (credentials or os.environ.get('RAX_CREDENTIALS') or
                       os.environ.get('RAX_CREDS_FILE'))
        region = region or os.environ.get('RAX_REGION')
    except KeyError, e:
        module.fail_json(msg='Unable to load %s' % e.message)

    try:
        rax_module.set_setting('identity_type', 'rackspace')

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
