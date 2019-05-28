# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2016 Red Hat Inc.
# (c) 2018 Cisco Systems Inc.
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
#
# Intersight REST API Module
# Author: Matthew Garrett
# Contributors: David Soper, Chris Gascoigne, John McDonough

from base64 import b64encode
from email.utils import formatdate
import re
import json
import hashlib
from ansible.module_utils.six.moves.urllib.parse import urlparse, urlencode, quote
from ansible.module_utils.urls import fetch_url

try:
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

intersight_argument_spec = dict(
    api_private_key=dict(type='path', required=True),
    api_uri=dict(type='str', default='https://intersight.com/api/v1'),
    api_key_id=dict(type='str', required=True),
    validate_certs=dict(type='bool', default=True),
    use_proxy=dict(type='bool', default=True),
)


def get_sha256_digest(data):
    """
    Generates a SHA256 digest from a String.

    :param data: data string set by user
    :return: instance of digest object
    """

    digest = hashlib.sha256()
    digest.update(data.encode())

    return digest


def prepare_str_to_sign(req_tgt, hdrs):
    """
    Concatenates Intersight headers in preparation to be RSA signed

    :param req_tgt : http method plus endpoint
    :param hdrs: dict with header keys
    :return: concatenated header authorization string
    """
    ss = ""
    ss = ss + "(request-target): " + req_tgt.lower() + "\n"

    length = len(hdrs.items())

    i = 0
    for key, value in hdrs.items():
        ss = ss + key.lower() + ": " + value
        if i < length - 1:
            ss = ss + "\n"
        i += 1

    return ss


def get_gmt_date():
    """
    Generated a GMT formatted Date

    :return: current date
    """

    return formatdate(timeval=None, localtime=False, usegmt=True)


class IntersightModule():

    def __init__(self, module):
        self.module = module
        self.result = dict(changed=False)
        if not HAS_CRYPTOGRAPHY:
            self.module.fail_json(msg='cryptography is required for this module')
        self.host = self.module.params['api_uri']
        self.public_key = self.module.params['api_key_id']
        self.private_key = open(self.module.params['api_private_key'], 'r').read()
        self.digest_algorithm = 'rsa-sha256'
        self.response_list = []

    def get_rsasig_b64encode(self, data):
        """
        Generates an RSA Signed SHA256 digest from a String

        :param digest: string to be signed & hashed
        :return: instance of digest object
        """

        rsakey = serialization.load_pem_private_key(self.private_key.encode(), None, default_backend())
        sign = rsakey.sign(data.encode(), padding.PKCS1v15(), hashes.SHA256())

        return b64encode(sign)

    def get_auth_header(self, hdrs, signed_msg):
        """
        Assmebled an Intersight formatted authorization header

        :param hdrs : object with header keys
        :param signed_msg: base64 encoded sha256 hashed body
        :return: concatenated authorization header
        """

        auth_str = "Signature"

        auth_str = auth_str + " " + "keyId=\"" + self.public_key + "\"," + "algorithm=\"" + self.digest_algorithm + "\"," + "headers=\"(request-target)"

        for key, dummy in hdrs.items():
            auth_str = auth_str + " " + key.lower()
        auth_str = auth_str + "\""

        auth_str = auth_str + "," + "signature=\"" + signed_msg.decode('ascii') + "\""

        return auth_str

    def get_moid_by_name(self, resource_path, target_name):
        """
        Retrieve an Intersight object moid by name

        :param resource_path: intersight resource path e.g. '/ntp/Policies'
        :param target_name: intersight object name
        :return: json http response object
        """
        query_params = {
            "$filter": "Name eq '{0}'".format(target_name)
        }

        options = {
            "http_method": "GET",
            "resource_path": resource_path,
            "query_params": query_params
        }

        get_moid = self.intersight_call(**options)

        if get_moid.json()['Results'] is not None:
            located_moid = get_moid.json()['Results'][0]['Moid']
        else:
            raise KeyError('Intersight object with name "{0}" not found!'.format(target_name))

        return located_moid

    def call_api(self, **options):
        """
        Call the Intersight API and check for success status
        :param options: options dict with method and other params for API call
        :return: json http response object
        """

        try:
            response, info = self.intersight_call(**options)
            if not re.match(r'2..', str(info['status'])):
                raise RuntimeError(info['status'], info['msg'], info['body'])
        except Exception as e:
            self.module.fail_json(msg="API error: %s " % str(e))

        response_data = response.read()
        if len(response_data) > 0:
            return json.loads(response_data)
        return {}

    def intersight_call(self, http_method="", resource_path="", query_params=None, body=None, moid=None, name=None):
        """
        Invoke the Intersight API

        :param resource_path: intersight resource path e.g. '/ntp/Policies'
        :param query_params: dictionary object with query string parameters as key/value pairs
        :param body: dictionary object with intersight data
        :param moid: intersight object moid
        :param name: intersight object name
        :return: json http response object
        """

        target_host = urlparse(self.host).netloc
        target_path = urlparse(self.host).path
        query_path = ""
        method = http_method.upper()
        bodyString = ""

        # Verify an accepted HTTP verb was chosen
        if(method not in ['GET', 'POST', 'PATCH', 'DELETE']):
            raise ValueError('Please select a valid HTTP verb (GET/POST/PATCH/DELETE)')

        # Verify the resource path isn't empy & is a valid <str> object
        if(resource_path != "" and not (resource_path, str)):
            raise TypeError('The *resource_path* value is required and must be of type "<str>"')

        # Verify the query parameters isn't empy & is a valid <dict> object
        if(query_params is not None and not isinstance(query_params, dict)):
            raise TypeError('The *query_params* value must be of type "<dict>"')

        # Verify the body isn't empy & is a valid <dict> object
        if(body is not None and not isinstance(body, dict)):
            raise TypeError('The *body* value must be of type "<dict>"')

        # Verify the MOID is not null & of proper length
        if(moid is not None and len(moid.encode('utf-8')) != 24):
            raise ValueError('Invalid *moid* value!')

        # Check for query_params, encode, and concatenate onto URL
        if query_params is not None:
            query_path = "?" + urlencode(query_params).replace('+', '%20')

        # Handle PATCH/DELETE by Object "name" instead of "moid"
        if(method == "PATCH" or method == "DELETE"):
            if moid is None:
                if name is not None:
                    if isinstance(name, str):
                        moid = self.get_moid_by_name(resource_path, name)
                    else:
                        raise TypeError('The *name* value must be of type "<str>"')
                else:
                    raise ValueError('Must set either *moid* or *name* with "PATCH/DELETE!"')

        # Check for moid and concatenate onto URL
        if moid is not None:
            resource_path += "/" + moid

        # Check for GET request to properly form body
        if method != "GET":
            bodyString = json.dumps(body)

        # Concatenate URLs for headers
        target_url = self.host + resource_path + query_path
        request_target = method + " " + target_path + resource_path + query_path

        # Get the current GMT Date/Time
        cdate = get_gmt_date()

        # Generate the body digest
        body_digest = get_sha256_digest(bodyString)
        b64_body_digest = b64encode(body_digest.digest())

        # Generate the authorization header
        auth_header = {
            'Date': cdate,
            'Host': target_host,
            'Digest': "SHA-256=" + b64_body_digest.decode('ascii')
        }

        string_to_sign = prepare_str_to_sign(request_target, auth_header)
        b64_signed_msg = self.get_rsasig_b64encode(string_to_sign)
        auth_header = self.get_auth_header(auth_header, b64_signed_msg)

        # Generate the HTTP requests header
        request_header = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Host': '{0}'.format(target_host),
            'Date': '{0}'.format(cdate),
            'Digest': 'SHA-256={0}'.format(b64_body_digest.decode('ascii')),
            'Authorization': '{0}'.format(auth_header),
        }

        response, info = fetch_url(self.module, target_url, data=bodyString, headers=request_header, method=method, use_proxy=self.module.params['use_proxy'])

        return response, info
