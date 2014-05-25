from os import *
import json
from azure.servicemanagement import *


def azure_common_argument_spec():
    return dict(
        certificate_path=dict(aliases=['CERTIFICATE_PATH'], type='str'),
        subscription_id=dict(aliases=['SUBSCRIPTION_ID'], no_log=True, type='str'),
        management_endpoint=dict(aliases=['MANAGEMENT_ENDPOINT'], type='str'),
        )
    return spec

def azure_props(x):
    return dict((key, getattr(x, key)) for key in dir(x) if key not in dir(x.__class__))

def azure_props_to_dict(x):
    return json.loads(json.dumps(x, default=lambda o: o.__dict__))

def create_azure_conform_name(name):
    if name:
      return name.lower().replace("_", "-").replace("--", "-")
    else:
      return name

class Azure():
    '''
    To use azure from ansible you need at least:
    * an azure account
    * working pem/cer pair (https://github.com/Azure/azure-sdk-for-python)
    * azure python sdk (pip install azure)
    '''
    AZURE_MANAGEMENT_ENDPOINT='https://management.core.windows.net'

    @staticmethod
    def get_sms(module):
        subscription_id, certificate_path = Azure.get_creds(module)
        return ServiceManagementService(subscription_id, certificate_path)

    @staticmethod
    def connection_info(module):
        certificate_path = module.params.get('certificate_path')
        subscription_id = module.params.get('subscription_id')
        management_endpoint = module.params.get('management_endpoint')

        if not subscription_id:
            if 'AZURE_SUBSCRIPTION_ID' in os.environ:
                subscription_id = os.environ['AZURE_SUBSCRIPTION_ID']


        if not certificate_path:
            if 'AZURE_MANAGEMENT_CERTIFICATE' in os.environ:
                certificate_path = os.environ['AZURE_MANAGEMENT_CERTIFICATE']

        if not management_endpoint:
            if 'AZURE_MANAGEMENT_ENDPOINT' in os.environ:
                management_endpoint = os.environ['AZURE_MANAGEMENT_ENDPOINT']
            else:
                management_endpoint = Azure.AZURE_MANAGEMENT_ENDPOINT


        facts = dict(certificate_path=certificate_path,
                        subscription_id=subscription_id,
                        management_endpoint=management_endpoint)

        return facts

    @staticmethod
    def get_creds(module):
        azure_env = Azure.connection_info(module)
        return azure_env['subscription_id'], azure_env['certificate_path']
