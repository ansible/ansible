import os, sys


def azure_common_argument_spec():
    return dict(
        certificate_path=dict(aliases=['CERTIFICATE_PATH'], type='str'),
        subscription_id=dict(aliases=['SUBSCRIPTION_ID'], no_log=True, type='str'),
        cert_thumbprint=dict(aliases=['CERT_THUMBPRINT'], no_log=True, type='str'),
        cloud_service_cert=dict(aliases=['CLOUD_SERVICE_CERT'], type='str'))


def azure_props(x):
    return dict((key, getattr(x, key)) for key in dir(x) if key not in dir(x.__class__))


def create_azure_conform_name(name):
    if name:
        return name.lower().replace("_", "-").replace("--", "-")
    else:
        return name


class AzureConfig(object):
    '''
    To use azure from ansible you need at least:
    * an azure account
    * working pem/cer pair (https://github.com/Azure/azure-sdk-for-python)
    * azure python sdk (pip install azure)
    '''

    def __init__(self, module):
        self.subscription_id = self._set_field(module, 'subscription_id', 'AZURE_SUBSCRIPTION_ID', True)
        self.certificate_path = self._set_field(module, 'certificate_path', 'AZURE_MANAGEMENT_CERTIFICATE', True)
        self.cert_thumbprint = self._set_field(module, 'cert_thumbprint', 'AZURE_CERT_THUMBPRINT')
        self.cloud_service_cert = self._set_field(module, 'cloud_service_cert', 'AZURE_CLOUD_SERVICE_CERT')

    def _set_field(self, module, arg_name, env_name, required=False):
        arg_value = module.params[arg_name]
        if not arg_value:
            if env_name in os.environ:
                arg_value = os.environ[env_name]
            else:
                arg_value = None

        if required and not arg_value:
            module.fail_json(msg=arg_name + " must be provided param ("+arg_name+") or env var ("+env_name+").")

        return arg_value

