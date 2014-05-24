from os import *

from azure.servicemanagement import *

class Azure():
    AZURE_MANAGEMENT_ENDPOINT='https://management.core.windows.net'

    @staticmethod
    def get_sms(module):
        subscription_id, certificate_path = Azure.get_creds(module)
        return ServiceManagementService(subscription_id, certificate_path)

    @staticmethod
    def common_argument_spec():
        return dict(
            certificate_path=dict(aliases=['CERTIFICATE_PATH'], type='str'),
            subscription_id=dict(aliases=['SUBSCRIPTION_ID'], no_log=True, type='str'),
            management_endpoint=dict(aliases=['MANAGEMENT_ENDPOINT'], type='str'),
            )
        return spec

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

