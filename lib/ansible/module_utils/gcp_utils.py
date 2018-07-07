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
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_text
import os


def navigate_hash(source, path, default=None):
    if not source:
        return None

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


def remove_nones_from_dict(obj):
    new_obj = {}
    for key in obj:
        value = obj[key]
        if value is not None and value != {} and value != []:
            new_obj[key] = value
    return new_obj


# Handles the replacement of dicts with values -> the needed value for GCP API
def replace_resource_dict(item, value):
    if isinstance(item, list):
        items = []
        for i in item:
            items.append(replace_resource_dict(i, value))
        return items
    else:
        if not item:
            return item
        return item.get(value)


# Handles all authentation and HTTP sessions for GCP API calls.
class GcpSession(object):
    def __init__(self, module, product):
        self.module = module
        self.product = product
        self._validate()

    def get(self, url, body=None, **kwargs):
        kwargs.update({'json': body, 'headers': self._headers()})
        try:
            return self.session().get(url, **kwargs)
        except getattr(requests.exceptions, 'RequestException') as inst:
            self.module.fail_json(msg=inst.message)

    def post(self, url, body=None):
        try:
            return self.session().post(url, json=body, headers=self._headers())
        except getattr(requests.exceptions, 'RequestException') as inst:
            self.module.fail_json(msg=inst.message)

    def delete(self, url, body=None):
        try:
            return self.session().delete(url, json=body, headers=self._headers())
        except getattr(requests.exceptions, 'RequestException') as inst:
            self.module.fail_json(msg=inst.message)

    def put(self, url, body=None):
        try:
            return self.session().put(url, json=body, headers=self._headers())
        except getattr(requests.exceptions, 'RequestException') as inst:
            self.module.fail_json(msg=inst.message)

    def session(self):
        return AuthorizedSession(
            self._credentials().with_scopes(self.module.params['scopes']))

    def _validate(self):
        if not HAS_REQUESTS:
            self.module.fail_json(msg="Please install the requests library")

        if not HAS_GOOGLE_LIBRARIES:
            self.module.fail_json(msg="Please install the google-auth library")

        if 'auth_kind' not in self.module.params:
            self.module.fail_json(msg="Auth kind parameter is missing")

        if self.module.params.get('service_account_email') is not None and self.module.params['auth_kind'] != 'machineaccount':
            self.module.fail_json(
                msg="Service Acccount Email only works with Machine Account-based authentication"
            )

        if self.module.params.get('service_account_file') is not None and self.module.params['auth_kind'] != 'serviceaccount':
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

    def raise_for_status(self, response):
        try:
            response.raise_for_status()
        except getattr(requests.exceptions, 'RequestException') as inst:
            self.fail_json(msg="GCP returned error: %s" % response.json())

    def _merge_dictionaries(self, a, b):
        new = a.copy()
        new.update(b)
        return new


# This class takes in two dictionaries `a` and `b`.
# These are dictionaries of arbitrary depth, but made up of standard Python
# types only.
# This differ will compare all values in `a` to those in `b`.
# Note: Only keys in `a` will be compared. Extra keys in `b` will be ignored.
# Note: On all lists, order does matter.
class GcpRequest(object):
    def __init__(self, request):
        self.request = request

    def __eq__(self, other):
        return not self.difference(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    # Returns the difference between `self.request` and `b`
    def difference(self, b):
        return self._compare_dicts(self.request, b.request)

    def _compare_dicts(self, dict1, dict2):
        difference = {}
        for key in dict1:
            difference[key] = self._compare_value(dict1.get(key), dict2.get(key))

        # Remove all empty values from difference.
        difference2 = {}
        for key in difference:
            if difference[key]:
                difference2[key] = difference[key]

        return difference2

    # Takes in two lists and compares them.
    def _compare_lists(self, list1, list2):
        difference = []
        for index in range(len(list1)):
            value1 = list1[index]
            if index < len(list2):
                value2 = list2[index]
                difference.append(self._compare_value(value1, value2))

        difference2 = []
        for value in difference:
            if value:
                difference2.append(value)

        return difference2

    def _compare_value(self, value1, value2):
        diff = None
        # If a None is found, a difference does not exist.
        # Only differing values matter.
        if not value2:
            return None

        # Can assume non-None types at this point.
        try:
            if isinstance(value1, list):
                diff = self._compare_lists(value1, value2)
            elif isinstance(value2, dict):
                diff = self._compare_dicts(value1, value2)
            # Always use to_text values to avoid unicode issues.
            elif to_text(value1) != to_text(value2):
                diff = value1
        # to_text may throw UnicodeErrors.
        # These errors shouldn't crash Ansible and should be hidden.
        except UnicodeError:
            pass

        return diff
