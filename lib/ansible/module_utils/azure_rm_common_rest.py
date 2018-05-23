# Copyright (c) 2018 Zim Kalinowski, <zikalino@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

try:
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.azure_configuration import AzureConfiguration
    from msrest.service_client import ServiceClient
    import json
except ImportError:
    # This is handled in azure_rm_common
    AzureConfiguration = object


class GenericRestClientConfiguration(AzureConfiguration):

    def __init__(self, credentials, subscription_id, base_url=None):

        if credentials is None:
            raise ValueError("Parameter 'credentials' must not be None.")
        if subscription_id is None:
            raise ValueError("Parameter 'subscription_id' must not be None.")
        if not base_url:
            base_url = 'https://management.azure.com'

        super(GenericRestClientConfiguration, self).__init__(base_url)

        self.add_user_agent('genericrestclient/1.0')
        self.add_user_agent('Azure-SDK-For-Python')

        self.credentials = credentials
        self.subscription_id = subscription_id


class GenericRestClient(object):

    def __init__(self, credentials, subscription_id, base_url=None):
        self.config = GenericRestClientConfiguration(credentials, subscription_id, base_url)
        self._client = ServiceClient(self.config.credentials, self.config)
        self.models = None

    def query(self, url, method, query_parameters, header_parameters, body, expected_status_codes):
        # Construct and send request
        operation_config = {}

        request = None

        if method == 'GET':
            request = self._client.get(url, query_parameters)
        elif method == 'PUT':
            request = self._client.put(url, query_parameters)
        elif method == 'POST':
            request = self._client.post(url, query_parameters)
        elif method == 'HEAD':
            request = self._client.head(url, query_parameters)
        elif method == 'PATCH':
            request = self._client.patch(url, query_parameters)
        elif method == 'DELETE':
            request = self._client.delete(url, query_parameters)
        elif method == 'MERGE':
            request = self._client.merge(url, query_parameters)

        response = self._client.send(request, header_parameters, body, **operation_config)

        if response.status_code not in expected_status_codes:
            exp = CloudError(response)
            exp.request_id = response.headers.get('x-ms-request-id')
            raise exp

        return response
