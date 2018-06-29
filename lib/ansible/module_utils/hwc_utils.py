# 2018.05.11 - changed the implementation for classes of GcpSession and
#              GcpModule
#            - changed the name of some variables
#
# Copyright (c), Google Inc, 2017
# Simplified BSD License (see licenses/simplified_bsd.txt or
# https://opensource.org/licenses/BSD-2-Clause)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from keystoneauth1 import adapter
    from keystoneauth1.identity import v3
    from keystoneauth1 import session
    HAS_THIRD_LIBRARIES = True
except ImportError:
    HAS_THIRD_LIBRARIES = False

from ansible.module_utils.basic import AnsibleModule
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


def remove_nones_from_dict(obj):
    new_obj = {}
    for key in obj:
        value = obj[key]
        if value is not None and value != {} and value != []:
            new_obj[key] = value
    return new_obj


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


class _LegacyJsonAdapter(adapter.Adapter):
    """Make something that looks like an old HTTPClient.

    This class references adapter.LegacyJsonAdapter
    """

    def request(self, *args, **kwargs):
        headers = kwargs.setdefault('headers', {})
        headers.setdefault('Accept', 'application/json')

        try:
            kwargs['json'] = kwargs.pop('body')
        except KeyError:
            pass

        return super(_LegacyJsonAdapter, self).request(*args, **kwargs)


# Handles all authentation and HTTP sessions for HWC API calls.
class HwcSession(object):
    def __init__(self, module, product):
        self.module = module
        self.product = product
        self._validate()
        self._session = self._credentials()
        self._adapter = _LegacyJsonAdapter(self._session)

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
        return url

    def get_project_id(self):
        try:
            return self._session.get_project_id()
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
            'User-Agent': "Huawei-Ansible-MM-%s" % self.product
        }


class HwcModule(AnsibleModule):
    def __init__(self, *args, **kwargs):
        arg_spec = kwargs.setdefault('argument_spec', {})

        arg_spec.update(
            dict(
                identity_endpoint=dict(required=True, type='str'),
                user_name=dict(required=True, type='str'),
                password=dict(required=True, type='str'),
                domain_name=dict(required=True, type='str'),
                project_name=dict(required=True, type='str'),
                region=dict(required=True, type='str'),
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
        return all([
            self._compare_value(dict1.get(k), dict2.get(k)) for k in dict1
        ])

    # Takes in two lists and compares them.
    def _compare_lists(self, list1, list2):
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
