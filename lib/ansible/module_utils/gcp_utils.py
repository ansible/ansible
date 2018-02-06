# Copyright (c), Google Inc, 2017
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import google.auth
    import google.auth.compute_engine
    from google.oauth2 import service_account
    from google.auth.transport.requests import AuthorizedSession
    HAS_GOOGLE_LIBRARIES = True
except ImportError:
    HAS_GOOGLE_LIBRARIES = False

from ansible.module_utils.basic import AnsibleModule, env_fallback
import os


def navigate_hash(source, path, default=None):
    key = path[0]
    path = path[1:]
    if key not in source:
        return default
    result = source[key]
    if path:
        return navigate_hash(result, path, default)
    else:
        return result


class GcpRequestException(Exception):
    pass


# Handles all authentation and HTTP sessions for GCP API calls.
class GcpSession(object):
    def __init__(self, module, product):
        self.module = module
        self.product = product
        self._validate()

    def get(self, url, body=None):
        try:
            return self.session().get(url, json=body, headers=self._headers())
        except getattr(requests.exceptions, 'RequestException') as inst:
            raise GcpRequestException(inst.message)

    def post(self, url, body=None):
        try:
            return self.session().post(url, json=body, headers=self._headers())
        except getattr(requests.exceptions, 'RequestException') as inst:
            raise GcpRequestException(inst.message)

    def delete(self, url, body=None):
        try:
            return self.session().delete(url, json=body, headers=self._headers())
        except getattr(requests.exceptions, 'RequestException') as inst:
            raise GcpRequestException(inst.message)

    def put(self, url, body=None):
        try:
            return self.session().put(url, json=body, headers=self._headers())
        except getattr(requests.exceptions, 'RequestException') as inst:
            raise GcpRequestException(inst.message)

    def session(self):
        return AuthorizedSession(
            self._credentials().with_scopes(self.module.params['scopes']))

    def _validate(self):
        if not HAS_REQUESTS:
            self.module.fail_json(msg="Please install the requests library")

        if not HAS_GOOGLE_LIBRARIES:
            self.module.fail_json(msg="Please install the google-auth library")

        if self.module.params['service_account_email'] is not None and self.module.params['auth_kind'] != 'machineaccount':
            self.module.fail_json(
                msg="Service Acccount Email only works with Machine Account-based authentication"
            )

        if self.module.params['service_account_file'] is not None and self.module.params['auth_kind'] != 'serviceaccount':
            self.module.fail_json(
                msg="Service Acccount File only works with Service Account-based authentication"
            )

    def _credentials(self):
        cred_type = self.module.params['auth_kind']
        if cred_type == 'application':
            credentials, project_id = google.auth.default()
            return credentials
        elif cred_type == 'serviceaccount':
            return service_account.Credentials.from_service_account_file(
                self.module.params['service_account_file'])
        elif cred_type == 'machineaccount':
            return google.auth.compute_engine.Credentials(
                self.module.params['service_account_email'])
        else:
            self.module.fail_json(msg="Credential type '%s' not implmented" % cred_type)

    def _headers(self):
        return {
            'User-Agent': "Google-Ansible-MM-{0}".format(self.product)
        }


class GcpModule(AnsibleModule):
    def __init__(self, *args, **kwargs):
        arg_spec = {}
        if 'argument_spec' in kwargs:
            arg_spec = kwargs['argument_spec']

        kwargs['argument_spec'] = self._merge_dictionaries(
            arg_spec,
            dict(
                project=dict(required=True, type='str'),
                auth_kind=dict(
                    required=False,
                    fallback=(env_fallback, ['GCP_AUTH_KIND']),
                    choices=['machineaccount', 'serviceaccount', 'application'],
                    type='str'),
                service_account_email=dict(
                    required=False,
                    fallback=(env_fallback, ['GCP_SERVICE_ACCOUNT_EMAIL']),
                    type='str'),
                service_account_file=dict(
                    required=False,
                    fallback=(env_fallback, ['GCP_SERVICE_ACCOUNT_FILE']),
                    type='path'),
                scopes=dict(
                    required=False,
                    fallback=(env_fallback, ['GCP_SCOPES']),
                    type='list')
            )
        )

        mutual = []
        if 'mutually_exclusive' in kwargs:
            mutual = kwargs['mutually_exclusive']

        kwargs['mutually_exclusive'] = mutual.append(
            ['service_account_email', 'service_account_file']
        )

        AnsibleModule.__init__(self, *args, **kwargs)

    def _merge_dictionaries(self, a, b):
        new = a.copy()
        new.update(b)
        return new
