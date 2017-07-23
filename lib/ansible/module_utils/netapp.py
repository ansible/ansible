#
# (c) 2016, Sumit Kumar <sumit4@netapp.com>
# (c) 2016, Michael Price <michael.price@netapp.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

try:
    import json
except ImportError:
    import simplejson as json

from ansible.module_utils.six.moves.urllib.error import HTTPError

from ansible.module_utils.api import basic_auth_argument_spec
from ansible.module_utils.urls import open_url
from ansible.module_utils.api import basic_auth_argument_spec

HAS_NETAPP_LIB = False
try:
    from netapp_lib.api.zapi import zapi
    from netapp_lib.api.zapi import errors as zapi_errors
    HAS_NETAPP_LIB = True
except:
    HAS_NETAPP_LIB = False


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

try:
    from solidfire.factory import ElementFactory
    from solidfire.custom.models import TimeIntervalFrequency
    from solidfire.models import Schedule, ScheduleInfo

    HAS_SF_SDK = True
except:
    HAS_SF_SDK = False


def has_netapp_lib():
    return HAS_NETAPP_LIB


def has_sf_sdk():
    return HAS_SF_SDK


def ontap_sf_host_argument_spec():

    return dict(
        hostname=dict(required=True, type='str'),
        username=dict(required=True, type='str', aliases=['user']),
        password=dict(required=True, type='str', aliases=['pass'], no_log=True),
    )


def create_sf_connection(module, port=None):
    hostname = module.params['hostname']
    username = module.params['username']
    password = module.params['password']

    if HAS_SF_SDK and hostname and username and password:
        try:
            return_val = ElementFactory.create(hostname, username, password, port=port)
            return return_val
        except:
            raise Exception("Unable to create SF connection")
    else:
        module.fail_json(msg="the python SolidFire SDK module is required")


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
        server.set_api_version(major=1, minor=21)
        server.set_port(80)
        server.set_server_type('FILER')
        server.set_transport_type('HTTP')
        return server
    else:
        module.fail_json(msg="the python NetApp-Lib module is required")


def eseries_host_argument_spec():
    """Retrieve a base argument specifiation common to all NetApp E-Series modules"""
    argument_spec = basic_auth_argument_spec()
    argument_spec.update(dict(
        api_username=dict(type='str', required=True),
        api_password=dict(type='str', required=True, no_log=True),
        api_url=dict(type='str', required=True),
        ssid=dict(type='str', required=True),
        validate_certs=dict(required=False, default=True),
    ))
    return argument_spec


def request(url, data=None, headers=None, method='GET', use_proxy=True,
            force=False, last_mod_time=None, timeout=10, validate_certs=True,
            url_username=None, url_password=None, http_agent=None, force_basic_auth=True, ignore_errors=False):
    """Issue an HTTP request to a url, retrieving an optional JSON response."""

    if headers is None:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

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
    except:
        if ignore_errors:
            pass
        else:
            raise Exception(raw_data)

    resp_code = r.getcode()

    if resp_code >= 400 and not ignore_errors:
        raise Exception(resp_code, data)
    else:
        return resp_code, data
