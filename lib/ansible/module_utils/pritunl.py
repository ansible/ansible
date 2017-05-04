#!/usr/bin/env python

# (c) 2016, Florian Dambrine <android.florian@gmail.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.


import time
import uuid
import hmac
import hashlib
import base64

from ansible.module_utils.urls import open_url


# Taken from https://pritunl.com/api and adaped work with Ansible open_url util
def pritunl_auth_request(module, method, path, headers=None, data=None):
    api_token = module.params.get('pritunl_api_token')
    api_secret = module.params.get('pritunl_api_secret')
    base_url = module.params.get('pritunl_url')
    validate_certs = module.params.get('validate_certs')

    auth_timestamp = str(int(time.time()))
    auth_nonce = uuid.uuid4().hex

    auth_string = '&'.join([api_token, auth_timestamp, auth_nonce,
                           method.upper(), path] + ([data] if data else []))

    auth_signature = base64.b64encode(hmac.new(api_secret,
                                               auth_string, hashlib.sha256).digest())

    auth_headers = {
        'Auth-Token': api_token,
        'Auth-Timestamp': auth_timestamp,
        'Auth-Nonce': auth_nonce,
        'Auth-Signature': auth_signature
    }

    if headers:
        auth_headers.update(headers)

    try:
        uri = "%s%s" % (base_url, path)

        return open_url(uri, method=method.upper(),
                        headers=auth_headers,
                        data=data)
    except Exception as e:
        module.fail_json(msg='Could not connect to %s: %s' % (base_url, e))
