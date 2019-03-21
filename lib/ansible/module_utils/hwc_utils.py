# Copyright (c), Google Inc, 2017
# Simplified BSD License (see licenses/simplified_bsd.txt or
# https://opensource.org/licenses/BSD-2-Clause)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from keystoneauth1.adapter import Adapter
    from keystoneauth1.identity import v3
    from keystoneauth1 import session
    HAS_THIRD_LIBRARIES = True
except ImportError:
    HAS_THIRD_LIBRARIES = False

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils._text import to_text


def navigate_hash(source, path, default=None):
    if not (source and path):
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


class HwcRequestException(Exception):
    pass


def remove_empty_from_dict(obj):
    return _DictClean(
        obj,
        lambda v: v is not None and v != {} and v != []
    )()


def remove_nones_from_dict(obj):
    return _DictClean(obj, lambda v: v is not None)()


# Handles the replacement of dicts with values -> the needed value for HWC API
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


# Handles all authentation and HTTP sessions for HWC API calls.
class HwcSession(object):
    def __init__(self, module, product):
        self.module = module
        self.product = product
        self._validate()
        self._session = self._credentials()
        self._adapter = Adapter(self._session)
        self._endpoints = {}
        self._project_id = ""

    def get(self, url, body=None):
        try:
            return self._adapter.get(
                url, json=body,
                headers=self._headers(), raise_exc=False)
        except getattr(requests.exceptions, 'RequestException') as inst:
            self.module.fail_json(msg=inst.message)

    def post(self, url, body=None):
        try:
            return self._adapter.post(
                url, json=body,
                headers=self._headers(), raise_exc=False)
        except getattr(requests.exceptions, 'RequestException') as inst:
            self.module.fail_json(msg=inst.message)

    def delete(self, url, body=None):
        try:
            return self._adapter.delete(
                url, json=body,
                headers=self._headers(), raise_exc=False)
        except getattr(requests.exceptions, 'RequestException') as inst:
            self.module.fail_json(msg=inst.message)

    def put(self, url, body=None):
        try:
            return self._adapter.put(
                url, json=body,
                headers=self._headers(), raise_exc=False)
        except getattr(requests.exceptions, 'RequestException') as inst:
            self.module.fail_json(msg=inst.message)

    def get_service_endpoint(self, service_type):
        if self._endpoints.get(service_type):
            return self._endpoints.get(service_type)

        e = None
        try:
            e = self._session.get_endpoint_data(
                service_type=service_type,
                region_name=self.module.params['region']
            )
        except getattr(requests.exceptions, 'RequestException') as inst:
            self.module.fail_json(msg=inst.message)

        if not e or e.url == "":
            self.module.fail_json(
                msg="Can not find the enpoint for %s" % service_type)

        url = e.url
        if url[-1] != "/":
            url += "/"

        self._endpoints[service_type] = url
        return url

    def get_project_id(self):
        if self._project_id:
            return self._project_id
        try:
            pid = self._session.get_project_id()
            self._project_id = pid
            return pid
        except getattr(requests.exceptions, 'RequestException') as inst:
            self.module.fail_json(msg=inst.message)

    def _validate(self):
        if not HAS_REQUESTS:
            self.module.fail_json(msg="Please install the requests library")

        if not HAS_THIRD_LIBRARIES:
            self.module.fail_json(
                msg="Please install the keystoneauth1 library")

    def _credentials(self):
        auth = v3.Password(
            auth_url=self.module.params['identity_endpoint'],
            password=self.module.params['password'],
            username=self.module.params['user_name'],
            user_domain_name=self.module.params['domain_name'],
            project_name=self.module.params['project_name'],
            reauthenticate=True
        )

        return session.Session(auth=auth)

    def _headers(self):
        return {
            'User-Agent': "Huawei-Ansible-MM-%s" % self.product,
            'Accept': 'application/json',
        }


class HwcModule(AnsibleModule):
    def __init__(self, *args, **kwargs):
        arg_spec = kwargs.setdefault('argument_spec', {})

        arg_spec.update(
            dict(
                identity_endpoint=dict(
                    required=True, type='str',
                    fallback=(env_fallback, ['IDENTITY_ENDPOINT']),
                ),
                user_name=dict(
                    required=True, type='str',
                    fallback=(env_fallback, ['USER_NAME']),
                ),
                password=dict(
                    required=True, type='str', no_log=True,
                    fallback=(env_fallback, ['PASSWORD']),
                ),
                domain_name=dict(
                    required=True, type='str',
                    fallback=(env_fallback, ['DOMAIN_NAME']),
                ),
                project_name=dict(
                    required=True, type='str',
                    fallback=(env_fallback, ['PROJECT_NAME']),
                ),
                region=dict(
                    required=True, type='str',
                    fallback=(env_fallback, ['REGION']),
                ),
                timeouts=dict(type='dict', options=dict(
                    create=dict(default='10m', type='str'),
                    update=dict(default='10m', type='str'),
                    delete=dict(default='10m', type='str'),
                ), default={}),
                id=dict(type='str')
            )
        )

        super(HwcModule, self).__init__(*args, **kwargs)


# This class takes in two dictionaries `a` and `b`.
# These are dictionaries of arbitrary depth, but made up of standard Python
# types only.
# This differ will compare all values in `a` to those in `b`.
# Note: Only keys in `a` will be compared. Extra keys in `b` will be ignored.
# Note: On all lists, order does matter.
class DictComparison(object):
    def __init__(self, request):
        self.request = request

    def __eq__(self, other):
        return self._compare_dicts(self.request, other.request)

    def __ne__(self, other):
        return not self.__eq__(other)

    def _compare_dicts(self, dict1, dict2):
        if len(dict1.keys()) != len(dict2.keys()):
            return False

        return all([
            self._compare_value(dict1.get(k), dict2.get(k)) for k in dict1
        ])

    # Takes in two lists and compares them.
    def _compare_lists(self, list1, list2):
        if len(list1) != len(list2):
            return False

        difference = []
        for index in range(len(list1)):
            value1 = list1[index]
            if index < len(list2):
                value2 = list2[index]
                difference.append(self._compare_value(value1, value2))

        return all(difference)

    def _compare_value(self, value1, value2):
        """
        return: True: value1 is same as value2, otherwise False.
        """
        if not (value1 and value2):
            return (not value1) and (not value2)

        # Can assume non-None types at this point.
        try:
            if isinstance(value1, list):
                return self._compare_lists(value1, value2)
            elif isinstance(value1, dict):
                return self._compare_dicts(value1, value2)
            # Always use to_text values to avoid unicode issues.
            else:
                return to_text(value1) == to_text(value2)
        # to_text may throw UnicodeErrors.
        # These errors shouldn't crash Ansible and return False as default.
        except UnicodeError:
            return False


class _DictClean(object):
    def __init__(self, obj, func):
        self.obj = obj
        self.keep_it = func

    def __call__(self):
        return self._clean_dict(self.obj)

    def _clean_dict(self, obj):
        r = {}
        for k, v in obj.items():
            v1 = v
            if isinstance(v, dict):
                v1 = self._clean_dict(v)
            elif isinstance(v, list):
                v1 = self._clean_list(v)
            if self.keep_it(v1):
                r[k] = v1
        return r

    def _clean_list(self, obj):
        r = []
        for v in obj:
            v1 = v
            if isinstance(v, dict):
                v1 = self._clean_dict(v)
            elif isinstance(v, list):
                v1 = self._clean_list(v)
            if self.keep_it(v1):
                r.append(v1)
        return r
