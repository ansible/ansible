# (c) 2019, Eric Anderson <eric.sysmin@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Usage:
#     vars:
#         encrypted_myvar: "{{ var | b64encode | gcp_kms_encrypt(auth_kind='serviceaccount',
#           service_account_file='gcp_service_account_file', projects='default',
#           key_ring='key_ring', crypto_key='crypto_key') }}"
#         decrypted_myvar: "{{ encrypted_myvar | gcp_kms_decrypt(auth_kind='serviceaccount',
#           service_account_file=gcp_service_account_file, projects='default',
#           key_ring='key_ring', crypto_key='crypto_key') }}"

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleError
from ansible.module_utils.gcp_utils import GcpSession


class GcpMockModule(object):
    def __init__(self, params):
        self.params = params

    def fail_json(self, *args, **kwargs):
        raise AnsibleError(kwargs['msg'])


class GcpKmsFilter():
    def run(self, method, **kwargs):
        params = {
            'ciphertext': kwargs.get('ciphertext', None),
            'plaintext': kwargs.get('plaintext', None),
            'additional_authenticated_data': kwargs.get('additional_authenticated_data', None),
            'key_ring': kwargs.get('key_ring', None),
            'crypto_key': kwargs.get('crypto_key', None),
            'projects': kwargs.get('projects', None),
            'scopes': kwargs.get('scopes', None),
            'locations': kwargs.get('locations', 'global'),
            'auth_kind': kwargs.get('auth_kind', None),
            'service_account_file': kwargs.get('service_account_file', None),
            'service_account_email': kwargs.get('service_account_email', None),
        }
        if not params['scopes']:
            params['scopes'] = ['https://www.googleapis.com/auth/cloudkms']
        fake_module = GcpMockModule(params)
        if method == "encrypt":
            return self.kms_encrypt(fake_module)
        elif method == "decrypt":
            return self.kms_decrypt(fake_module)

    def kms_decrypt(self, module):
        payload = {"ciphertext": module.params['ciphertext']}

        if module.params['additional_authenticated_data']:
            payload['additionalAuthenticatedData'] = module.params['additional_authenticated_data']

        auth = GcpSession(module, 'cloudkms')
        url = "https://cloudkms.googleapis.com/v1/projects/{projects}/locations/{locations}/" \
            "keyRings/{key_ring}/cryptoKeys/{crypto_key}:decrypt".format(**module.params)
        response = auth.post(url, body=payload)
        return response.json()['plaintext']

    def kms_encrypt(self, module):
        payload = {"plaintext": module.params['plaintext']}

        if module.params['additional_authenticated_data']:
            payload['additionalAuthenticatedData'] = module.params['additional_authenticated_data']

        auth = GcpSession(module, 'cloudkms')
        url = "https://cloudkms.googleapis.com/v1/projects/{projects}/locations/{locations}/" \
            "keyRings/{key_ring}/cryptoKeys/{crypto_key}:encrypt".format(**module.params)
        response = auth.post(url, body=payload)
        return response.json()['ciphertext']


def gcp_kms_encrypt(plaintext, **kwargs):
    return GcpKmsFilter().run('encrypt', plaintext=plaintext, **kwargs)


def gcp_kms_decrypt(ciphertext, **kwargs):
    return GcpKmsFilter().run('decrypt', ciphertext=ciphertext, **kwargs)


class FilterModule(object):

    def filters(self):
        return {
            'gcp_kms_encrypt': gcp_kms_encrypt,
            'gcp_kms_decrypt': gcp_kms_decrypt
        }
