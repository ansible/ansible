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

from pprint import pformat
from ansible.module_utils.basic import AnsibleModule
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
        ontapi=dict(required=False, type='int')
    )


def ontap_sf_host_argument_spec():

    return dict(
        hostname=dict(required=True, type='str'),
        username=dict(required=True, type='str', aliases=['user']),
        password=dict(required=True, type='str', aliases=['pass'], no_log=True)
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
    DEFAULT_REST_API_PATH = "devmgr/v2"
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
        self.url = args["api_url"]
        self.ssid = args["ssid"]
        self.creds = dict(url_username=args["api_username"],
                          url_password=args["api_password"],
                          validate_certs=args["validate_certs"])
        self.log_requests = log_requests

        self.is_embedded_mode = None
        self.web_services_validate = None

        self._tweak_url()

    @property
    def _about_url(self):
        """Generates the about url based on the supplied web services rest api url.

        :raise AnsibleFailJson: raised when supplied web services rest api is an invalid url.
        :return: proxy or embedded about url.
        """
        about = list(urlparse(self.url))
        about[2] = "devmgr/utils/about"
        return urlunparse(about)

    def _force_secure_url(self):
        """Modifies supplied web services rest api to use secure https.

        raise: AnsibleFailJson: raised when the url already utilizes the secure protocol
        """
        url_parts = list(urlparse(self.url))
        if "https://" in self.url and ":8443" in self.url:
            self.module.fail_json(msg="Secure HTTP protocol already used. URL path [%s]" % self.url)

        url_parts[0] = "https"
        url_parts[1] = "%s:8443" % url_parts[1].split(":")[0]

        self.url = urlunparse(url_parts)
        if not self.url.endswith("/"):
            self.url += "/"

        self.module.warn("forced use of the secure protocol: %s" % self.url)

    def _tweak_url(self):
        """Adjust the rest api url is necessary.

        :raise AnsibleFailJson: raised when self.url fails to have a hostname or ipv4 address.
        """
        # ensure the protocol is either http or https
        if self.url.split("://")[0] not in ["https", "http"]:

            self.url = self.url.split("://")[1] if "://" in self.url else self.url

            if ":8080" in self.url:
                self.url = "http://%s" % self.url
            else:
                self.url = "https://%s" % self.url

        # parse url and verify protocol, port and path are consistent with required web services rest api url.
        url_parts = list(urlparse(self.url))
        if url_parts[1] == "":
            self.module.fail_json(msg="Failed to provide a valid hostname or IP address. URL [%s]." % self.url)

        split_hostname = url_parts[1].split(":")
        if url_parts[0] not in ["https", "http"] or (len(split_hostname) == 2 and split_hostname[1] != "8080"):
            if len(split_hostname) == 2 and split_hostname[1] == "8080":
                url_parts[0] = "http"
                url_parts[1] = "%s:8080" % split_hostname[0]
            else:
                url_parts[0] = "https"
                url_parts[1] = "%s:8443" % split_hostname[0]
        elif len(split_hostname) == 1:
            if url_parts[0] == "https":
                url_parts[1] = "%s:8443" % split_hostname[0]
            elif url_parts[0] == "http":
                url_parts[1] = "%s:8080" % split_hostname[0]

        if url_parts[2] == "" or url_parts[2] != self.DEFAULT_REST_API_PATH:
            url_parts[2] = self.DEFAULT_REST_API_PATH

        self.url = urlunparse(url_parts)
        if not self.url.endswith("/"):
            self.url += "/"

        self.module.log("valid url: %s" % self.url)

    def _is_web_services_valid(self):
        """Verify proxy or embedded web services meets minimum version required for module.

        The minimum required web services version is evaluated against version supplied through the web services rest
        api. AnsibleFailJson exception will be raised when the minimum is not met or exceeded.

        :raise AnsibleFailJson: raised when the contacted api service does not meet the minimum required version.
        """
        if not self.web_services_validate:
            self.is_embedded()
            try:
                rc, data = request(self._about_url, timeout=self.DEFAULT_TIMEOUT,
                                   headers=self.DEFAULT_HEADERS, **self.creds)
                major, minor, other, revision = data["version"].split(".")
                minimum_major, minimum_minor, other, minimum_revision = self.web_services_version.split(".")

                if not (major > minimum_major or
                        (major == minimum_major and minor > minimum_minor) or
                        (major == minimum_major and minor == minimum_minor and revision >= minimum_revision)):
                    self.module.fail_json(
                        msg="Web services version does not meet minimum version required. Current version: [%s]."
                            " Version required: [%s]." % (data["version"], self.web_services_version))
            except Exception as error:
                self.module.fail_json(msg="Failed to retrieve the webservices about information! Array Id [%s]."
                                          " Error [%s]." % (self.ssid, to_native(error)))

            self.module.warn("Web services rest api version met the minimum required version.")
            self.web_services_validate = True

        return self.web_services_validate

    def is_embedded(self, retry=True):
        """Determine whether web services server is the embedded web services.

        If web services about endpoint fails based on an URLError then the request will be attempted again using
        secure http.

        :raise AnsibleFailJson: raised when web services about endpoint failed to be contacted.
        :return bool: whether contacted web services is running from storage array (embedded) or from a proxy.
        """
        if self.is_embedded_mode is None:
            try:
                rc, data = request(self._about_url, timeout=self.DEFAULT_TIMEOUT,
                                   headers=self.DEFAULT_HEADERS, **self.creds)
                self.is_embedded_mode = not data["runningAsProxy"]
            except URLError as error:
                if not retry:
                    self.module.fail_json(msg="Failed to retrieve the webservices about information! Array Id [%s]."
                                              " Error [%s]." % (self.ssid, to_native(error)))
                self.module.warn("Failed to retrieve the webservices about information! Will retry using secure"
                                 " http. Array Id [%s]." % self.ssid)
                self._force_secure_url()
                return self.is_embedded(retry=False)
            except Exception as error:
                self.module.fail_json(msg="Failed to retrieve the webservices about information! Array Id [%s]."
                                          " Error [%s]." % (self.ssid, to_native(error)))

        return self.is_embedded_mode

    def request(self, path, data=None, method='GET', ignore_errors=False):
        """Issue an HTTP request to a url, retrieving an optional JSON response.

        :param str path: web services rest api endpoint path (Example: storage-systems/1/graph). Note that when the
        full url path is specified then that will be used without supplying the protocol, hostname, port and rest path.
        :param data: data required for the request (data may be json or any python structured data)
        :param str method: request method such as GET, POST, DELETE.
        :param bool ignore_errors: forces the request to ignore any raised exceptions.
        """
        if self._is_web_services_valid():
            url = list(urlparse(path.strip("/")))
            if url[2] == "":
                self.module.fail_json(msg="Web services rest api endpoint path must be specified. Path [%s]." % path)

            # if either the protocol or hostname/port are missing then add them.
            if url[0] == "" or url[1] == "":
                url[0], url[1] = list(urlparse(self.url))[:2]

            # add rest api path if the supplied path does not begin with it.
            if not all([word in url[2].split("/")[:2] for word in self.DEFAULT_REST_API_PATH.split("/")]):
                if not url[2].startswith("/"):
                    url[2] = "/" + url[2]
                url[2] = self.DEFAULT_REST_API_PATH + url[2]

            # ensure data is json formatted
            if not isinstance(data, str):
                data = json.dumps(data)

            if self.log_requests:
                self.module.log(pformat(dict(url=urlunparse(url), data=data, method=method)))

            return request(url=urlunparse(url), data=data, method=method, headers=self.DEFAULT_HEADERS, use_proxy=True,
                           force=False, last_mod_time=None, timeout=self.DEFAULT_TIMEOUT, http_agent=self.HTTP_AGENT,
                           force_basic_auth=True, ignore_errors=ignore_errors, **self.creds)


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


def get_cserver(server):
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
