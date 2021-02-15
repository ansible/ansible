# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c) 2017, Sumit Kumar <sumit4@netapp.com>
# Copyright (c) 2017, Michael Price <michael.price@netapp.com>
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

import json
import os
import random
import mimetypes

from pprint import pformat
from ansible.module_utils import six
from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.six.moves.urllib.error import HTTPError, URLError
from ansible.module_utils.urls import open_url
from ansible.module_utils.api import basic_auth_argument_spec
from ansible.module_utils._text import to_native

try:
    from ansible.module_utils.ansible_release import __version__ as ansible_version
except ImportError:
    ansible_version = 'unknown'

try:
    from netapp_lib.api.zapi import zapi
    HAS_NETAPP_LIB = True
except ImportError:
    HAS_NETAPP_LIB = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

import ssl
try:
    from urlparse import urlparse, urlunparse
except ImportError:
    from urllib.parse import urlparse, urlunparse


HAS_SF_SDK = False
SF_BYTE_MAP = dict(
    # Management GUI displays 1024 ** 3 as 1.1 GB, thus use 1000.
    bytes=1,
    b=1,
    kb=1000,
    mb=1000 ** 2,
    gb=1000 ** 3,
    tb=1000 ** 4,
    pb=1000 ** 5,
    eb=1000 ** 6,
    zb=1000 ** 7,
    yb=1000 ** 8
)

POW2_BYTE_MAP = dict(
    # Here, 1 kb = 1024
    bytes=1,
    b=1,
    kb=1024,
    mb=1024 ** 2,
    gb=1024 ** 3,
    tb=1024 ** 4,
    pb=1024 ** 5,
    eb=1024 ** 6,
    zb=1024 ** 7,
    yb=1024 ** 8
)

try:
    from solidfire.factory import ElementFactory
    from solidfire.custom.models import TimeIntervalFrequency
    from solidfire.models import Schedule, ScheduleInfo

    HAS_SF_SDK = True
except Exception:
    HAS_SF_SDK = False


def has_netapp_lib():
    return HAS_NETAPP_LIB


def has_sf_sdk():
    return HAS_SF_SDK


def na_ontap_host_argument_spec():

    return dict(
        hostname=dict(required=True, type='str'),
        username=dict(required=True, type='str', aliases=['user']),
        password=dict(required=True, type='str', aliases=['pass'], no_log=True),
        https=dict(required=False, type='bool', default=False),
        validate_certs=dict(required=False, type='bool', default=True),
        http_port=dict(required=False, type='int'),
        ontapi=dict(required=False, type='int'),
        use_rest=dict(required=False, type='str', default='Auto', choices=['Never', 'Always', 'Auto'])
    )


def ontap_sf_host_argument_spec():

    return dict(
        hostname=dict(required=True, type='str'),
        username=dict(required=True, type='str', aliases=['user']),
        password=dict(required=True, type='str', aliases=['pass'], no_log=True)
    )


def aws_cvs_host_argument_spec():

    return dict(
        api_url=dict(required=True, type='str'),
        validate_certs=dict(required=False, type='bool', default=True),
        api_key=dict(required=True, type='str', no_log=True),
        secret_key=dict(required=True, type='str', no_log=True)
    )


def create_sf_connection(module, port=None):
    hostname = module.params['hostname']
    username = module.params['username']
    password = module.params['password']

    if HAS_SF_SDK and hostname and username and password:
        try:
            return_val = ElementFactory.create(hostname, username, password, port=port)
            return return_val
        except Exception:
            raise Exception("Unable to create SF connection")
    else:
        module.fail_json(msg="the python SolidFire SDK module is required")


def setup_na_ontap_zapi(module, vserver=None):
    hostname = module.params['hostname']
    username = module.params['username']
    password = module.params['password']
    https = module.params['https']
    validate_certs = module.params['validate_certs']
    port = module.params['http_port']
    version = module.params['ontapi']

    if HAS_NETAPP_LIB:
        # set up zapi
        server = zapi.NaServer(hostname)
        server.set_username(username)
        server.set_password(password)
        if vserver:
            server.set_vserver(vserver)
        if version:
            minor = version
        else:
            minor = 110
        server.set_api_version(major=1, minor=minor)
        # default is HTTP
        if https:
            if port is None:
                port = 443
            transport_type = 'HTTPS'
            # HACK to bypass certificate verification
            if validate_certs is False:
                if not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
                    ssl._create_default_https_context = ssl._create_unverified_context
        else:
            if port is None:
                port = 80
            transport_type = 'HTTP'
        server.set_transport_type(transport_type)
        server.set_port(port)
        server.set_server_type('FILER')
        return server
    else:
        module.fail_json(msg="the python NetApp-Lib module is required")


def setup_ontap_zapi(module, vserver=None):
    hostname = module.params['hostname']
    username = module.params['username']
    password = module.params['password']

    if HAS_NETAPP_LIB:
        # set up zapi
        server = zapi.NaServer(hostname)
        server.set_username(username)
        server.set_password(password)
        if vserver:
            server.set_vserver(vserver)
        # Todo : Replace hard-coded values with configurable parameters.
        server.set_api_version(major=1, minor=110)
        server.set_port(80)
        server.set_server_type('FILER')
        server.set_transport_type('HTTP')
        return server
    else:
        module.fail_json(msg="the python NetApp-Lib module is required")


def eseries_host_argument_spec():
    """Retrieve a base argument specification common to all NetApp E-Series modules"""
    argument_spec = basic_auth_argument_spec()
    argument_spec.update(dict(
        api_username=dict(type='str', required=True),
        api_password=dict(type='str', required=True, no_log=True),
        api_url=dict(type='str', required=True),
        ssid=dict(type='str', required=False, default='1'),
        validate_certs=dict(type='bool', required=False, default=True)
    ))
    return argument_spec


class NetAppESeriesModule(object):
    """Base class for all NetApp E-Series modules.

    Provides a set of common methods for NetApp E-Series modules, including version checking, mode (proxy, embedded)
    verification, http requests, secure http redirection for embedded web services, and logging setup.

    Be sure to add the following lines in the module's documentation section:
    extends_documentation_fragment:
        - netapp.eseries

    :param dict(dict) ansible_options: dictionary of ansible option definitions
    :param str web_services_version: minimally required web services rest api version (default value: "02.00.0000.0000")
    :param bool supports_check_mode: whether the module will support the check_mode capabilities (default=False)
    :param list(list) mutually_exclusive: list containing list(s) of mutually exclusive options (optional)
    :param list(list) required_if: list containing list(s) containing the option, the option value, and then
    a list of required options. (optional)
    :param list(list) required_one_of: list containing list(s) of options for which at least one is required. (optional)
    :param list(list) required_together: list containing list(s) of options that are required together. (optional)
    :param bool log_requests: controls whether to log each request (default: True)
    """
    DEFAULT_TIMEOUT = 60
    DEFAULT_SECURE_PORT = "8443"
    DEFAULT_REST_API_PATH = "devmgr/v2/"
    DEFAULT_REST_API_ABOUT_PATH = "devmgr/utils/about"
    DEFAULT_HEADERS = {"Content-Type": "application/json", "Accept": "application/json",
                       "netapp-client-type": "Ansible-%s" % ansible_version}
    HTTP_AGENT = "Ansible / %s" % ansible_version
    SIZE_UNIT_MAP = dict(bytes=1, b=1, kb=1024, mb=1024**2, gb=1024**3, tb=1024**4,
                         pb=1024**5, eb=1024**6, zb=1024**7, yb=1024**8)

    def __init__(self, ansible_options, web_services_version=None, supports_check_mode=False,
                 mutually_exclusive=None, required_if=None, required_one_of=None, required_together=None,
                 log_requests=True):
        argument_spec = eseries_host_argument_spec()
        argument_spec.update(ansible_options)

        self.module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=supports_check_mode,
                                    mutually_exclusive=mutually_exclusive, required_if=required_if,
                                    required_one_of=required_one_of, required_together=required_together)

        args = self.module.params
        self.web_services_version = web_services_version if web_services_version else "02.00.0000.0000"
        self.ssid = args["ssid"]
        self.url = args["api_url"]
        self.log_requests = log_requests
        self.creds = dict(url_username=args["api_username"],
                          url_password=args["api_password"],
                          validate_certs=args["validate_certs"])

        if not self.url.endswith("/"):
            self.url += "/"

        self.is_embedded_mode = None
        self.is_web_services_valid_cache = None

    def _check_web_services_version(self):
        """Verify proxy or embedded web services meets minimum version required for module.

        The minimum required web services version is evaluated against version supplied through the web services rest
        api. AnsibleFailJson exception will be raised when the minimum is not met or exceeded.

        This helper function will update the supplied api url if secure http is not used for embedded web services

        :raise AnsibleFailJson: raised when the contacted api service does not meet the minimum required version.
        """
        if not self.is_web_services_valid_cache:

            url_parts = urlparse(self.url)
            if not url_parts.scheme or not url_parts.netloc:
                self.module.fail_json(msg="Failed to provide valid API URL. Example: https://192.168.1.100:8443/devmgr/v2. URL [%s]." % self.url)

            if url_parts.scheme not in ["http", "https"]:
                self.module.fail_json(msg="Protocol must be http or https. URL [%s]." % self.url)

            self.url = "%s://%s/" % (url_parts.scheme, url_parts.netloc)
            about_url = self.url + self.DEFAULT_REST_API_ABOUT_PATH
            rc, data = request(about_url, timeout=self.DEFAULT_TIMEOUT, headers=self.DEFAULT_HEADERS, ignore_errors=True, **self.creds)

            if rc != 200:
                self.module.warn("Failed to retrieve web services about information! Retrying with secure ports. Array Id [%s]." % self.ssid)
                self.url = "https://%s:8443/" % url_parts.netloc.split(":")[0]
                about_url = self.url + self.DEFAULT_REST_API_ABOUT_PATH
                try:
                    rc, data = request(about_url, timeout=self.DEFAULT_TIMEOUT, headers=self.DEFAULT_HEADERS, **self.creds)
                except Exception as error:
                    self.module.fail_json(msg="Failed to retrieve the webservices about information! Array Id [%s]. Error [%s]."
                                              % (self.ssid, to_native(error)))

            major, minor, other, revision = data["version"].split(".")
            minimum_major, minimum_minor, other, minimum_revision = self.web_services_version.split(".")

            if not (major > minimum_major or
                    (major == minimum_major and minor > minimum_minor) or
                    (major == minimum_major and minor == minimum_minor and revision >= minimum_revision)):
                self.module.fail_json(msg="Web services version does not meet minimum version required. Current version: [%s]."
                                          " Version required: [%s]." % (data["version"], self.web_services_version))

            self.module.log("Web services rest api version met the minimum required version.")
            self.is_web_services_valid_cache = True

    def is_embedded(self):
        """Determine whether web services server is the embedded web services.

        If web services about endpoint fails based on an URLError then the request will be attempted again using
        secure http.

        :raise AnsibleFailJson: raised when web services about endpoint failed to be contacted.
        :return bool: whether contacted web services is running from storage array (embedded) or from a proxy.
        """
        self._check_web_services_version()

        if self.is_embedded_mode is None:
            about_url = self.url + self.DEFAULT_REST_API_ABOUT_PATH
            try:
                rc, data = request(about_url, timeout=self.DEFAULT_TIMEOUT, headers=self.DEFAULT_HEADERS, **self.creds)
                self.is_embedded_mode = not data["runningAsProxy"]
            except Exception as error:
                self.module.fail_json(msg="Failed to retrieve the webservices about information! Array Id [%s]. Error [%s]."
                                          % (self.ssid, to_native(error)))

        return self.is_embedded_mode

    def request(self, path, data=None, method='GET', headers=None, ignore_errors=False):
        """Issue an HTTP request to a url, retrieving an optional JSON response.

        :param str path: web services rest api endpoint path (Example: storage-systems/1/graph). Note that when the
        full url path is specified then that will be used without supplying the protocol, hostname, port and rest path.
        :param data: data required for the request (data may be json or any python structured data)
        :param str method: request method such as GET, POST, DELETE.
        :param dict headers: dictionary containing request headers.
        :param bool ignore_errors: forces the request to ignore any raised exceptions.
        """
        self._check_web_services_version()

        if headers is None:
            headers = self.DEFAULT_HEADERS

        if not isinstance(data, str) and headers["Content-Type"] == "application/json":
            data = json.dumps(data)

        if path.startswith("/"):
            path = path[1:]
        request_url = self.url + self.DEFAULT_REST_API_PATH + path

        if self.log_requests or True:
            self.module.log(pformat(dict(url=request_url, data=data, method=method)))

        return request(url=request_url, data=data, method=method, headers=headers, use_proxy=True, force=False, last_mod_time=None,
                       timeout=self.DEFAULT_TIMEOUT, http_agent=self.HTTP_AGENT, force_basic_auth=True, ignore_errors=ignore_errors, **self.creds)


def create_multipart_formdata(files, fields=None, send_8kb=False):
    """Create the data for a multipart/form request.

    :param list(list) files: list of lists each containing (name, filename, path).
    :param list(list) fields: list of lists each containing (key, value).
    :param bool send_8kb: only sends the first 8kb of the files (default: False).
    """
    boundary = "---------------------------" + "".join([str(random.randint(0, 9)) for x in range(27)])
    data_parts = list()
    data = None

    if six.PY2:  # Generate payload for Python 2
        newline = "\r\n"
        if fields is not None:
            for key, value in fields:
                data_parts.extend(["--%s" % boundary,
                                   'Content-Disposition: form-data; name="%s"' % key,
                                   "",
                                   value])

        for name, filename, path in files:
            with open(path, "rb") as fh:
                value = fh.read(8192) if send_8kb else fh.read()

                data_parts.extend(["--%s" % boundary,
                                   'Content-Disposition: form-data; name="%s"; filename="%s"' % (name, filename),
                                   "Content-Type: %s" % (mimetypes.guess_type(path)[0] or "application/octet-stream"),
                                   "",
                                   value])
        data_parts.extend(["--%s--" % boundary, ""])
        data = newline.join(data_parts)

    else:
        newline = six.b("\r\n")
        if fields is not None:
            for key, value in fields:
                data_parts.extend([six.b("--%s" % boundary),
                                   six.b('Content-Disposition: form-data; name="%s"' % key),
                                   six.b(""),
                                   six.b(value)])

        for name, filename, path in files:
            with open(path, "rb") as fh:
                value = fh.read(8192) if send_8kb else fh.read()

                data_parts.extend([six.b("--%s" % boundary),
                                   six.b('Content-Disposition: form-data; name="%s"; filename="%s"' % (name, filename)),
                                   six.b("Content-Type: %s" % (mimetypes.guess_type(path)[0] or "application/octet-stream")),
                                   six.b(""),
                                   value])
        data_parts.extend([six.b("--%s--" % boundary), b""])
        data = newline.join(data_parts)

    headers = {
        "Content-Type": "multipart/form-data; boundary=%s" % boundary,
        "Content-Length": str(len(data))}

    return headers, data


def request(url, data=None, headers=None, method='GET', use_proxy=True,
            force=False, last_mod_time=None, timeout=10, validate_certs=True,
            url_username=None, url_password=None, http_agent=None, force_basic_auth=True, ignore_errors=False):
    """Issue an HTTP request to a url, retrieving an optional JSON response."""

    if headers is None:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
    headers.update({"netapp-client-type": "Ansible-%s" % ansible_version})

    if not http_agent:
        http_agent = "Ansible / %s" % ansible_version

    try:
        r = open_url(url=url, data=data, headers=headers, method=method, use_proxy=use_proxy,
                     force=force, last_mod_time=last_mod_time, timeout=timeout, validate_certs=validate_certs,
                     url_username=url_username, url_password=url_password, http_agent=http_agent,
                     force_basic_auth=force_basic_auth)
    except HTTPError as err:
        r = err.fp

    try:
        raw_data = r.read()
        if raw_data:
            data = json.loads(raw_data)
        else:
            raw_data = None
    except Exception:
        if ignore_errors:
            pass
        else:
            raise Exception(raw_data)

    resp_code = r.getcode()

    if resp_code >= 400 and not ignore_errors:
        raise Exception(resp_code, data)
    else:
        return resp_code, data


def ems_log_event(source, server, name="Ansible", id="12345", version=ansible_version,
                  category="Information", event="setup", autosupport="false"):
    ems_log = zapi.NaElement('ems-autosupport-log')
    # Host name invoking the API.
    ems_log.add_new_child("computer-name", name)
    # ID of event. A user defined event-id, range [0..2^32-2].
    ems_log.add_new_child("event-id", id)
    # Name of the application invoking the API.
    ems_log.add_new_child("event-source", source)
    # Version of application invoking the API.
    ems_log.add_new_child("app-version", version)
    # Application defined category of the event.
    ems_log.add_new_child("category", category)
    # Description of event to log. An application defined message to log.
    ems_log.add_new_child("event-description", event)
    ems_log.add_new_child("log-level", "6")
    ems_log.add_new_child("auto-support", autosupport)
    server.invoke_successfully(ems_log, True)


def get_cserver_zapi(server):
    vserver_info = zapi.NaElement('vserver-get-iter')
    query_details = zapi.NaElement.create_node_with_children('vserver-info', **{'vserver-type': 'admin'})
    query = zapi.NaElement('query')
    query.add_child_elem(query_details)
    vserver_info.add_child_elem(query)
    result = server.invoke_successfully(vserver_info,
                                        enable_tunneling=False)
    attribute_list = result.get_child_by_name('attributes-list')
    vserver_list = attribute_list.get_child_by_name('vserver-info')
    return vserver_list.get_child_content('vserver-name')


def get_cserver(connection, is_rest=False):
    if not is_rest:
        return get_cserver_zapi(connection)

    params = {'fields': 'type'}
    api = "private/cli/vserver"
    json, error = connection.get(api, params)
    if json is None or error is not None:
        # exit if there is an error or no data
        return None
    vservers = json.get('records')
    if vservers is not None:
        for vserver in vservers:
            if vserver['type'] == 'admin':     # cluster admin
                return vserver['vserver']
        if len(vservers) == 1:                  # assume vserver admin
            return vservers[0]['vserver']

    return None


class OntapRestAPI(object):
    def __init__(self, module, timeout=60):
        self.module = module
        self.username = self.module.params['username']
        self.password = self.module.params['password']
        self.hostname = self.module.params['hostname']
        self.use_rest = self.module.params['use_rest']
        self.verify = self.module.params['validate_certs']
        self.timeout = timeout
        self.url = 'https://' + self.hostname + '/api/'
        self.errors = list()
        self.debug_logs = list()
        self.check_required_library()

    def check_required_library(self):
        if not HAS_REQUESTS:
            self.module.fail_json(msg=missing_required_lib('requests'))

    def send_request(self, method, api, params, json=None, return_status_code=False):
        ''' send http request and process reponse, including error conditions '''
        url = self.url + api
        status_code = None
        content = None
        json_dict = None
        json_error = None
        error_details = None

        def get_json(response):
            ''' extract json, and error message if present '''
            try:
                json = response.json()
            except ValueError:
                return None, None
            error = json.get('error')
            return json, error

        try:
            response = requests.request(method, url, verify=self.verify, auth=(self.username, self.password), params=params, timeout=self.timeout, json=json)
            content = response.content  # for debug purposes
            status_code = response.status_code
            # If the response was successful, no Exception will be raised
            response.raise_for_status()
            json_dict, json_error = get_json(response)
        except requests.exceptions.HTTPError as err:
            __, json_error = get_json(response)
            if json_error is None:
                self.log_error(status_code, 'HTTP error: %s' % err)
                error_details = str(err)
            # If an error was reported in the json payload, it is handled below
        except requests.exceptions.ConnectionError as err:
            self.log_error(status_code, 'Connection error: %s' % err)
            error_details = str(err)
        except Exception as err:
            self.log_error(status_code, 'Other error: %s' % err)
            error_details = str(err)
        if json_error is not None:
            self.log_error(status_code, 'Endpoint error: %d: %s' % (status_code, json_error))
            error_details = json_error
        self.log_debug(status_code, content)
        if return_status_code:
            return status_code, error_details
        return json_dict, error_details

    def get(self, api, params):
        method = 'GET'
        return self.send_request(method, api, params)

    def post(self, api, data, params=None):
        method = 'POST'
        return self.send_request(method, api, params, json=data)

    def patch(self, api, data, params=None):
        method = 'PATCH'
        return self.send_request(method, api, params, json=data)

    def delete(self, api, data, params=None):
        method = 'DELETE'
        return self.send_request(method, api, params, json=data)

    def _is_rest(self, used_unsupported_rest_properties=None):
        if self.use_rest == "Always":
            if used_unsupported_rest_properties:
                error = "REST API currently does not support '%s'" % \
                        ', '.join(used_unsupported_rest_properties)
                return True, error
            else:
                return True, None
        if self.use_rest == 'Never' or used_unsupported_rest_properties:
            # force ZAPI if requested or if some parameter requires it
            return False, None
        method = 'HEAD'
        api = 'cluster/software'
        status_code, __ = self.send_request(method, api, params=None, return_status_code=True)
        if status_code == 200:
            return True, None
        return False, None

    def is_rest(self, used_unsupported_rest_properties=None):
        ''' only return error if there is a reason to '''
        use_rest, error = self._is_rest(used_unsupported_rest_properties)
        if used_unsupported_rest_properties is None:
            return use_rest
        return use_rest, error

    def log_error(self, status_code, message):
        self.errors.append(message)
        self.debug_logs.append((status_code, message))

    def log_debug(self, status_code, content):
        self.debug_logs.append((status_code, content))


class AwsCvsRestAPI(object):
    def __init__(self, module, timeout=60):
        self.module = module
        self.api_key = self.module.params['api_key']
        self.secret_key = self.module.params['secret_key']
        self.api_url = self.module.params['api_url']
        self.verify = self.module.params['validate_certs']
        self.timeout = timeout
        self.url = 'https://' + self.api_url + '/v1/'
        self.check_required_library()

    def check_required_library(self):
        if not HAS_REQUESTS:
            self.module.fail_json(msg=missing_required_lib('requests'))

    def send_request(self, method, api, params, json=None):
        ''' send http request and process reponse, including error conditions '''
        url = self.url + api
        status_code = None
        content = None
        json_dict = None
        json_error = None
        error_details = None
        headers = {
            'Content-type': "application/json",
            'api-key': self.api_key,
            'secret-key': self.secret_key,
            'Cache-Control': "no-cache",
        }

        def get_json(response):
            ''' extract json, and error message if present '''
            try:
                json = response.json()

            except ValueError:
                return None, None
            success_code = [200, 201, 202]
            if response.status_code not in success_code:
                error = json.get('message')
            else:
                error = None
            return json, error
        try:
            response = requests.request(method, url, headers=headers, timeout=self.timeout, json=json)
            status_code = response.status_code
            # If the response was successful, no Exception will be raised
            json_dict, json_error = get_json(response)
        except requests.exceptions.HTTPError as err:
            __, json_error = get_json(response)
            if json_error is None:
                error_details = str(err)
        except requests.exceptions.ConnectionError as err:
            error_details = str(err)
        except Exception as err:
            error_details = str(err)
        if json_error is not None:
            error_details = json_error

        return json_dict, error_details

    # If an error was reported in the json payload, it is handled below
    def get(self, api, params=None):
        method = 'GET'
        return self.send_request(method, api, params)

    def post(self, api, data, params=None):
        method = 'POST'
        return self.send_request(method, api, params, json=data)

    def patch(self, api, data, params=None):
        method = 'PATCH'
        return self.send_request(method, api, params, json=data)

    def put(self, api, data, params=None):
        method = 'PUT'
        return self.send_request(method, api, params, json=data)

    def delete(self, api, data, params=None):
        method = 'DELETE'
        return self.send_request(method, api, params, json=data)

    def get_state(self, jobId):
        """ Method to get the state of the job """
        method = 'GET'
        response, status_code = self.get('Jobs/%s' % jobId)
        while str(response['state']) not in 'done':
            response, status_code = self.get('Jobs/%s' % jobId)
        return 'done'
