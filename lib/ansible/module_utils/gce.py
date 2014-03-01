USER_AGENT_PRODUCT="Ansible-gce"
USER_AGENT_VERSION="v1"

def gce_connect(module):
    """Return a Google Cloud Engine connection."""
    service_account_email = module.params.get('service_account_email', None)
    pem_file = module.params.get('pem_file', None)
    project_id = module.params.get('project_id', None)

    if service_account_email is None or pem_file is None:
        # Load in the libcloud secrets file
        try:
            import secrets
        except ImportError:
            secrets = None

        service_account_email, pem_file = getattr(secrets, 'GCE_PARAMS', (None, None))
        keyword_params = getattr(secrets, 'GCE_KEYWORD_PARAMS', {})
        project_id = keyword_params.get('project', None)

    if service_account_email is None or pem_file is None or project_id is None:
        module.fail_json(msg='Missing GCE connection parameters in libcloud secrets file.')
        return None

    try:
        gce = get_driver(Provider.GCE)(service_account_email, pem_file, datacenter=module.params.get('zone'), project=project_id)
        gce.connection.user_agent_append("%s/%s" % (
            USER_AGENT_PRODUCT, USER_AGENT_VERSION))
    except (RuntimeError, ValueError), e:
        module.fail_json(msg=str(e), changed=False)
    except Exception, e:
        module.fail_json(msg=unexpected_error_msg(e), changed=False)

    return gce

def unexpected_error_msg(error):
    """Create an error string based on passed in error."""
    msg='Unexpected response: HTTP return_code['
    msg+='%s], API error code[%s] and message: %s' % (
        error.http_code, error.code, str(error.value))
    return msg
