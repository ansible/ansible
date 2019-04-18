# Copyright (c) 2018 Cisco and/or its affiliates.
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
#
import re

from ansible.module_utils._text import to_text
from ansible.module_utils.common.collections import is_string
from ansible.module_utils.six import iteritems

INVALID_IDENTIFIER_SYMBOLS = r'[^a-zA-Z0-9_]'

IDENTITY_PROPERTIES = ['id', 'version', 'ruleId']
NON_COMPARABLE_PROPERTIES = IDENTITY_PROPERTIES + ['isSystemDefined', 'links']


class HTTPMethod:
    GET = 'get'
    POST = 'post'
    PUT = 'put'
    DELETE = 'delete'


class ResponseParams:
    SUCCESS = 'success'
    STATUS_CODE = 'status_code'
    RESPONSE = 'response'


class FtdConfigurationError(Exception):
    def __init__(self, msg, obj=None):
        super(FtdConfigurationError, self).__init__(msg)
        self.msg = msg
        self.obj = obj


class FtdServerError(Exception):
    def __init__(self, response, code):
        super(FtdServerError, self).__init__(response)
        self.response = response
        self.code = code


class FtdUnexpectedResponse(Exception):
    """The exception to be raised in case of unexpected responses from 3d parties."""
    pass


def construct_ansible_facts(response, params):
    facts = dict()
    if response:
        response_body = response['items'] if 'items' in response else response
        if params.get('register_as'):
            facts[params['register_as']] = response_body
        elif response_body.get('name') and response_body.get('type'):
            object_name = re.sub(INVALID_IDENTIFIER_SYMBOLS, '_', response_body['name'].lower())
            fact_name = '%s_%s' % (response_body['type'], object_name)
            facts[fact_name] = response_body
    return facts


def copy_identity_properties(source_obj, dest_obj):
    for property_name in IDENTITY_PROPERTIES:
        if property_name in source_obj:
            dest_obj[property_name] = source_obj[property_name]
    return dest_obj


def is_object_ref(d):
    """
    Checks if a dictionary is a reference object. The dictionary is considered to be a
    reference object when it contains non-empty 'id' and 'type' fields.

    :type d: dict
    :return: True if passed dictionary is a reference object, otherwise False
    """
    has_id = 'id' in d.keys() and d['id']
    has_type = 'type' in d.keys() and d['type']
    return has_id and has_type


def equal_object_refs(d1, d2):
    """
    Checks whether two references point to the same object.

    :type d1: dict
    :type d2: dict
    :return: True if passed references point to the same object, otherwise False
    """
    have_equal_ids = d1['id'] == d2['id']
    have_equal_types = d1['type'] == d2['type']
    return have_equal_ids and have_equal_types


def equal_lists(l1, l2):
    """
    Checks whether two lists are equal. The order of elements in the arrays is important.

    :type l1: list
    :type l2: list
    :return: True if passed lists, their elements and order of elements are equal. Otherwise, returns False.
    """
    if len(l1) != len(l2):
        return False

    for v1, v2 in zip(l1, l2):
        if not equal_values(v1, v2):
            return False

    return True


def equal_dicts(d1, d2, compare_by_reference=True):
    """
    Checks whether two dictionaries are equal. If `compare_by_reference` is set to True, dictionaries referencing
    objects are compared using `equal_object_refs` method. Otherwise, every key and value is checked.

    :type d1: dict
    :type d2: dict
    :param compare_by_reference: if True, dictionaries referencing objects are compared using `equal_object_refs` method
    :return: True if passed dicts are equal. Otherwise, returns False.
    """
    if compare_by_reference and is_object_ref(d1) and is_object_ref(d2):
        return equal_object_refs(d1, d2)

    if len(d1) != len(d2):
        return False

    for key, v1 in d1.items():
        if key not in d2:
            return False

        v2 = d2[key]
        if not equal_values(v1, v2):
            return False

    return True


def equal_values(v1, v2):
    """
    Checks whether types and content of two values are the same. In case of complex objects, the method might be
    called recursively.

    :param v1: first value
    :param v2: second value
    :return: True if types and content of passed values are equal. Otherwise, returns False.
    :rtype: bool
    """

    # string-like values might have same text but different types, so checking them separately
    if is_string(v1) and is_string(v2):
        return to_text(v1) == to_text(v2)

    if type(v1) != type(v2):
        return False
    value_type = type(v1)

    if value_type == list:
        return equal_lists(v1, v2)
    elif value_type == dict:
        return equal_dicts(v1, v2)
    else:
        return v1 == v2


def equal_objects(d1, d2):
    """
    Checks whether two objects are equal. Ignores special object properties (e.g. 'id', 'version') and
    properties with None and empty values. In case properties contains a reference to the other object,
    only object identities (ids and types) are checked. Also, if an array field contains multiple references
    to the same object, duplicates are ignored when comparing objects.

    :type d1: dict
    :type d2: dict
    :return: True if passed objects and their properties are equal. Otherwise, returns False.
    """

    def prepare_data_for_comparison(d):
        d = dict((k, d[k]) for k in d.keys() if k not in NON_COMPARABLE_PROPERTIES and d[k])
        d = delete_ref_duplicates(d)
        return d

    d1 = prepare_data_for_comparison(d1)
    d2 = prepare_data_for_comparison(d2)
    return equal_dicts(d1, d2, compare_by_reference=False)


def delete_ref_duplicates(d):
    """
    Removes reference duplicates from array fields: if an array contains multiple items and some of
    them refer to the same object, only unique references are preserved (duplicates are removed).

    :param d: dict with data
    :type d: dict
    :return: dict without reference duplicates
    """

    def delete_ref_duplicates_from_list(refs):
        if all(type(i) == dict and is_object_ref(i) for i in refs):
            unique_refs = set()
            unique_list = list()
            for i in refs:
                key = (i['id'], i['type'])
                if key not in unique_refs:
                    unique_refs.add(key)
                    unique_list.append(i)

            return list(unique_list)

        else:
            return refs

    if not d:
        return d

    modified_d = {}
    for k, v in iteritems(d):
        if type(v) == list:
            modified_d[k] = delete_ref_duplicates_from_list(v)
        elif type(v) == dict:
            modified_d[k] = delete_ref_duplicates(v)
        else:
            modified_d[k] = v
    return modified_d
