import json
import sys

try:
    import azure
    from azure.servicemanagement import ServiceManagementService
    from azure import WindowsAzureError
    from azure import _USER_AGENT_STRING, _update_request_uri_query
    from azure.http import HTTPResponse
    from azure.http import HTTPError
except ImportError:
    print("failed=True msg='azure required for this module. Please install with [pip install azure]'")
    sys.exit(1)


import os, sys


if sys.version_info < (3,):
    from urlparse import urlparse
else:
    from urllib.parse import urlparse

def azure_common_argument_spec():
    return dict(
        certificate_path=dict(aliases=['CERTIFICATE_PATH'], type='str'),
        subscription_id=dict(aliases=['SUBSCRIPTION_ID'], no_log=True, type='str'),
        cert_thumbprint=dict(aliases=['CERT_THUMBPRINT'], no_log=True, type='str'),
        cloud_service_cert=dict(aliases=['CLOUD_SERVICE_CERT'], type='str'))


def azure_props(x):
    return dict((key, getattr(x, key)) for key in dir(x) if key not in dir(x.__class__))


def azure_props_to_dict(x):
    return json.loads(json.dumps(x, default=lambda o: o.__dict__))


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
        config_filename = "azureProfile.json"
        tmp_filename = os.path.join(os.getcwd(), config_filename)
        if not os.path.exists(tmp_filename):
            if "USERPROFILE" in os.environ:
                tmp_filename = os.path.join(os.environ["USERPROFILE"], ".azure",
                                            config_filename)
            elif "HOME" in os.environ:
                tmp_filename = os.path.join(os.environ["HOME"], ".azure",
                                            config_filename)
        if os.path.exists(tmp_filename):
            with open(tmp_filename, "r") as f:
                self.ns = json.load(f)

        self.subscription_id = self._set_field(module, 'subscription_id', u'subscription_id', 'AZURE_SUBSCRIPTION_ID', True)
        self.certificate_path = self._set_field(module, 'certificate_path', u'certificate_path', 'AZURE_MANAGEMENT_CERTIFICATE', True)
        self.cert_thumbprint = self._set_field(module, 'cert_thumbprint', u'cert_thumbprint', 'AZURE_CERT_THUMBPRINT')
        self.cloud_service_cert = self._set_field(module, 'cloud_service_cert', u'cloud_service_cert', 'AZURE_CLOUD_SERVICE_CERT')

    def _set_field(self, module, arg_name, file_prop_name, env_name, required=False):
        arg_value = module.params[arg_name]
        if not arg_value:
            if self.ns and file_prop_name in self.ns:
                arg_value = str(self.ns[file_prop_name], 'utf-8')

        if not arg_value:
            if env_name in os.environ:
                arg_value = os.environ[env_name]
            else:
                arg_value = None

        if required and not arg_value:
            module.fail_json(msg=arg_name + " must be provided by config file ("+file_prop_name+"), param ("+arg_name+") or env var ("+env_name+").")

        return arg_value


# monkey patch for temporary redirects until https://github.com/Azure/azure-sdk-for-python/issues/129 is fixed
def perform_request_new(self, request):
    connection = self.get_connection(request)
    try:
        connection.putrequest(request.method, request.path)

        if not self.use_httplib:
            if self.proxy_host and self.proxy_user:
                connection.set_proxy_credentials(
                    self.proxy_user, self.proxy_password)

        self.send_request_headers(connection, request.headers)
        self.send_request_body(connection, request.body)

        resp = connection.getresponse()
        self.status = int(resp.status)
        self.message = resp.reason
        self.respheader = headers = resp.getheaders()

        # for consistency across platforms, make header names lowercase
        for i, value in enumerate(headers):
            headers[i] = (value[0].lower(), value[1])

        respbody = None
        if resp.length is None:
            respbody = resp.read()
        elif resp.length > 0:
            respbody = resp.read(resp.length)
        response = HTTPResponse(
            int(resp.status), resp.reason, headers, respbody)
        if self.status == 307:
            print("Temporary redirect detected...")
            new_url = urlparse(dict(headers)['location'])
            request.host = new_url.hostname
            request.path = new_url.path
            if new_url.query:
                request.path += '?' + new_url.query
            request.path, request.query = _update_request_uri_query(request)
            return self.perform_request(request)
        if self.status >= 300:
            raise HTTPError(self.status, self.message,
                            self.respheader, respbody)

        return response
    finally:
        connection.close()


azure.http.httpclient._HTTPClient.perform_request = perform_request_new

