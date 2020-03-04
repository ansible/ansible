# (c) 2019, Eric Anderson <eric.sysmin@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
lookup: gcp_storage_file
description:
  - This lookup returns the contents from a file residing on Google Cloud Storage
short_description: Return GC Storage content
version_added: 2.8
author: Eric Anderson <eanderson@avinetworks.com>
requirements:
  - python >= 2.6
  - requests >= 2.18.4
  - google-auth >= 1.3.0
options:
  src:
    description:
      - Source location of file (may be local machine or cloud depending on action).
    required: false
  bucket:
    description:
      - The name of the bucket.
    required: false
extends_documentation_fragment: gcp
'''

EXAMPLES = '''
- debug: msg="the value of foo.txt is {{ lookup('gcp_storage_file',
    bucket='gcp-bucket', src='mydir/foo.txt', project='project-name',
    auth_kind='serviceaccount', service_account_file='/tmp/myserviceaccountfile.json') }}"
'''

RETURN = '''
_raw:
    description:
        - base64 encoded file content
'''

import base64
import json
import mimetypes
import os
import requests
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display
from ansible.module_utils.gcp_utils import navigate_hash, GcpSession


display = Display()


class GcpMockModule(object):
    def __init__(self, params):
        self.params = params

    def fail_json(self, *args, **kwargs):
        raise AnsibleError(kwargs['msg'])

    def raise_for_status(self, response):
        try:
            response.raise_for_status()
        except getattr(requests.exceptions, 'RequestException'):
            self.fail_json(msg="GCP returned error: %s" % response.json())


class GcpFileLookup():
    def get_file_contents(self, module):
        auth = GcpSession(module, 'storage')
        data = auth.get(self.media_link(module))
        return base64.b64encode(data.content.rstrip())

    def fetch_resource(self, module, link, allow_not_found=True):
        auth = GcpSession(module, 'storage')
        return self.return_if_object(module, auth.get(link), allow_not_found)

    def self_link(self, module):
        return "https://www.googleapis.com/storage/v1/b/{bucket}/o/{src}".format(**module.params)

    def media_link(self, module):
        return "https://www.googleapis.com/storage/v1/b/{bucket}/o/{src}?alt=media".format(**module.params)

    def return_if_object(self, module, response, allow_not_found=False):
        # If not found, return nothing.
        if allow_not_found and response.status_code == 404:
            return None
        # If no content, return nothing.
        if response.status_code == 204:
            return None
        try:
            module.raise_for_status(response)
            result = response.json()
        except getattr(json.decoder, 'JSONDecodeError', ValueError) as inst:
            raise AnsibleError("Invalid JSON response with error: %s" % inst)
        if navigate_hash(result, ['error', 'errors']):
            raise AnsibleError(navigate_hash(result, ['error', 'errors']))
        return result

    def object_headers(self, module):
        return {
            "name": module.params['src'],
            "Content-Type": mimetypes.guess_type(module.params['src'])[0],
            "Content-Length": str(os.path.getsize(module.params['src'])),
        }

    def run(self, terms, variables=None, **kwargs):
        params = {
            'bucket': kwargs.get('bucket', None),
            'src': kwargs.get('src', None),
            'projects': kwargs.get('projects', None),
            'scopes': kwargs.get('scopes', None),
            'zones': kwargs.get('zones', None),
            'auth_kind': kwargs.get('auth_kind', None),
            'service_account_file': kwargs.get('service_account_file', None),
            'service_account_email': kwargs.get('service_account_email', None),
        }

        if not params['scopes']:
            params['scopes'] = ['https://www.googleapis.com/auth/devstorage.full_control']

        fake_module = GcpMockModule(params)

        # Check if files exist.
        remote_object = self.fetch_resource(fake_module, self.self_link(fake_module))
        if not remote_object:
            raise AnsibleError("File does not exist in bucket")

        result = self.get_file_contents(fake_module)
        return [result]


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        return GcpFileLookup().run(terms, variables=variables, **kwargs)
