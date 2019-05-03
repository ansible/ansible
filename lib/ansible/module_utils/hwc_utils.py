# Copyright (c), Google Inc, 2017
# Simplified BSD License (see licenses/simplified_bsd.txt or
# https://opensource.org/licenses/BSD-2-Clause)

import re
import traceback

THIRD_LIBRARIES_IMP_ERR = None
try:
    from keystoneauth1.adapter import Adapter
    from keystoneauth1.identity import v3
    from keystoneauth1 import session
    HAS_THIRD_LIBRARIES = True
except ImportError:
    THIRD_LIBRARIES_IMP_ERR = traceback.format_exc()
    HAS_THIRD_LIBRARIES = False

from ansible.module_utils.basic import (AnsibleModule, env_fallback,
                                        missing_required_lib)
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


def remove_empty_from_dict(obj):
    return _DictClean(
        obj,
        lambda v: v is not None and v != {} and v != []
    )()


def remove_nones_from_dict(obj):
    return _DictClean(obj, lambda v: v is not None)()


def replace_resource_dict(item, value):
    """ Handles the replacement of dicts with values ->
    the needed value for HWC API"""
    if isinstance(item, list):
        items = []
        for i in item:
            items.append(replace_resource_dict(i, value))
        return items
    else:
        if not item:
            return item
        return item.get(value)


def are_dicts_different(expect, actual):
    """Remove all output-only from actual."""
    actual_vals = {}
    for k, v in actual.items():
        if k in expect:
            actual_vals[k] = v

    expect_vals = {}
    for k, v in expect.items():
        if k in actual:
            expect_vals[k] = v

    return DictComparison(expect_vals) != DictComparison(actual_vals)


class HwcClientException(Exception):
    def __init__(self, code, message):
        super(HwcClientException, self).__init__()

        self._code = code
        self._message = message

    def __str__(self):
        msg = " code=%s," % str(self._code) if self._code != 0 else ""
        return "[HwcClientException]%s message=%s" % (
            msg, self._message)


class HwcClientException404(HwcClientException):
    def __init__(self, message):
        super(HwcClientException404, self).__init__(404, message)

    def __str__(self):
        return "[HwcClientException404] message=%s" % self._message


def session_method_wrapper(f):
    def _wrap(self, url, *args, **kwargs):
        try:
            url = self.endpoint + url
            r = f(self, url, *args, **kwargs)
        except Exception as ex:
            raise HwcClientException(
                0, "Sending request failed, error=%s" % ex)

        result = None
        if r.content:
            try:
                result = r.json()
            except Exception as ex:
                raise HwcClientException(
                    0, "Parsing response to json failed, error: %s" % ex)

        code = r.status_code
        if code not in [200, 201, 202, 203, 204, 205, 206, 207, 208, 226]:
            msg = ""
            for i in [['message'], ['error', 'message']]:
                try:
                    msg = navigate_hash(result, i)
                    break
                except Exception:
                    pass
            else:
                msg = str(result)

            if code == 404:
                raise HwcClientException404(msg)

            raise HwcClientException(code, msg)

        return result

    return _wrap


class _ServiceClient(object):
    def __init__(self, client, endpoint, product):
        self._client = client
        self._endpoint = endpoint
        self._default_header = {
            'User-Agent': "Huawei-Ansible-MM-%s" % product,
            'Accept': 'application/json',
        }

    @property
    def endpoint(self):
        return self._endpoint

    @session_method_wrapper
    def get(self, url, body=None, header=None, timeout=None):
        return self._client.get(url, json=body, timeout=timeout,
                                headers=self._header(header))

    @session_method_wrapper
    def post(self, url, body=None, header=None, timeout=None):
        return self._client.post(url, json=body, timeout=timeout,
                                 headers=self._header(header))

    @session_method_wrapper
    def delete(self, url, body=None, header=None, timeout=None):
        return self._client.delete(url, json=body, timeout=timeout,
                                   headers=self._header(header))

    @session_method_wrapper
    def put(self, url, body=None, header=None, timeout=None):
        return self._client.put(url, json=body, timeout=timeout,
                                headers=self._header(header))

    def _header(self, header):
        if header and isinstance(header, dict):
            for k, v in self._default_header.items():
                if k not in header:
                    header[k] = v
        else:
            header = self._default_header

        return header


class Config(object):
    def __init__(self, module, product):
        self._project_client = None
        self._domain_client = None
        self._module = module
        self._product = product
        self._endpoints = {}

        self._validate()
        self._gen_provider_client()

    @property
    def module(self):
        return self._module

    def client(self, region, service_type, service_level):
        c = self._project_client
        if service_level == "domain":
            c = self._domain_client

        e = self._get_service_endpoint(c, service_type, region)

        return _ServiceClient(c, e, self._product)

    def _gen_provider_client(self):
        m = self._module
        p = {
            "auth_url": m.params['identity_endpoint'],
            "password": m.params['password'],
            "username": m.params['user'],
            "project_name": m.params['project'],
            "user_domain_name": m.params['domain'],
            "reauthenticate": True
        }

        self._project_client = Adapter(
            session.Session(auth=v3.Password(**p)),
            raise_exc=False)

        p.pop("project_name")
        self._domain_client = Adapter(
            session.Session(auth=v3.Password(**p)),
            raise_exc=False)

    def _get_service_endpoint(self, client, service_type, region):
        k = "%s.%s" % (service_type, region if region else "")

        if k in self._endpoints:
            return self._endpoints.get(k)

        url = None
        try:
            url = client.get_endpoint(service_type=service_type,
                                      region_name=region, interface="public")
        except Exception as ex:
            raise HwcClientException(
                0, "Getting endpoint failed, error=%s" % ex)

        if url == "":
            raise HwcClientException(
                0, "Can not find the enpoint for %s" % service_type)

        if url[-1] != "/":
            url += "/"

        self._endpoints[k] = url
        return url

    def _validate(self):
        if not HAS_THIRD_LIBRARIES:
            self.module.fail_json(
                msg=missing_required_lib('keystoneauth1'),
                exception=THIRD_LIBRARIES_IMP_ERR)


class HwcModule(AnsibleModule):
    def __init__(self, *args, **kwargs):
        arg_spec = kwargs.setdefault('argument_spec', {})

        arg_spec.update(
            dict(
                identity_endpoint=dict(
                    required=True, type='str',
                    fallback=(env_fallback, ['ANSIBLE_HWC_IDENTITY_ENDPOINT']),
                ),
                user=dict(
                    required=True, type='str',
                    fallback=(env_fallback, ['ANSIBLE_HWC_USER']),
                ),
                password=dict(
                    required=True, type='str', no_log=True,
                    fallback=(env_fallback, ['ANSIBLE_HWC_PASSWORD']),
                ),
                domain=dict(
                    required=True, type='str',
                    fallback=(env_fallback, ['ANSIBLE_HWC_DOMAIN']),
                ),
                project=dict(
                    required=True, type='str',
                    fallback=(env_fallback, ['ANSIBLE_HWC_PROJECT']),
                ),
                region=dict(
                    required=True, type='str',
                    fallback=(env_fallback, ['ANSIBLE_HWC_REGION']),
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


class DictComparison(object):
    ''' This class takes in two dictionaries `a` and `b`.
        These are dictionaries of arbitrary depth, but made up of standard
        Python types only.
        This differ will compare all values in `a` to those in `b`.
        Note: Only keys in `a` will be compared. Extra keys in `b` will be ignored.
        Note: On all lists, order does matter.
    '''

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

    def _compare_lists(self, list1, list2):
        """Takes in two lists and compares them."""
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
        if isinstance(value1, list):
            return self._compare_lists(value1, value2)
        elif isinstance(value1, dict):
            return self._compare_dicts(value1, value2)
        # Always use to_text values to avoid unicode issues.
        else:
            return (to_text(value1, errors='surrogate_or_strict')
                    == to_text(value2, errors='surrogate_or_strict'))


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


def build_path(module, path, kv=None):
    if kv is None:
        kv = dict()

    v = {}
    for p in re.findall(r"{[^/]*}", path):
        n = p[1:][:-1]

        if n in kv:
            v[n] = str(kv[n])

        else:
            if n in module.params:
                v[n] = str(module.params.get(n))
            else:
                v[n] = ""

    return path.format(**v)


def get_region(module):
    if module.params['region']:
        return module.params['region']

    return module.params['project_name'].split("_")[0]
