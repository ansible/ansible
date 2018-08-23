import re

INVALID_IDENTIFIER_SYMBOLS = r'[^a-zA-Z0-9_]'

IDENTITY_PROPERTIES = ['id', 'version', 'ruleId']
NON_COMPARABLE_PROPERTIES = IDENTITY_PROPERTIES + ['isSystemDefined', 'links']


class HTTPMethod:
    GET = 'get'
    POST = 'post'
    PUT = 'put'
    DELETE = 'delete'


class FtdConfigurationError(Exception):
    pass


class FtdServerError(Exception):
    def __init__(self, response, code):
        super(FtdServerError, self).__init__(response)
        self.response = response
        self.code = code


def construct_ansible_facts(response, params):
    facts = dict()
    if response:
        response_body = response['items'] if 'items' in response else response
        if params.get('register_as'):
            facts[params['register_as']] = response_body
        elif 'name' in response_body and 'type' in response_body:
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
        if type(v1) != type(v2):
            return False
        value_type = type(v1)

        if value_type == dict and is_object_ref(v1) and is_object_ref(v2):
            equal_values = equal_object_refs(v1, v2)
        else:
            equal_values = v1 == v2

        if not equal_values:
            return False

    return True


def equal_objects(d1, d2):
    """
    Checks whether two objects are equal. Ignores special object properties (e.g. 'id', 'version') and
    properties with None and empty values. In case properties contains a reference to the other object,
    only object identities (ids and types) are checked.

    :type d1: dict
    :type d2: dict
    :return: True if passed objects and their properties are equal. Otherwise, returns False.
    """
    d1 = dict((k, d1[k]) for k in d1.keys() if k not in NON_COMPARABLE_PROPERTIES and d1[k])
    d2 = dict((k, d2[k]) for k in d2.keys() if k not in NON_COMPARABLE_PROPERTIES and d2[k])

    if len(d1) != len(d2):
        return False

    for key, v1 in d1.items():
        if key not in d2:
            return False

        v2 = d2[key]

        if type(v1) != type(v2):
            return False
        value_type = type(v1)

        if value_type == list:
            equal_values = equal_lists(v1, v2)
        elif value_type == dict and is_object_ref(v1) and is_object_ref(v2):
            equal_values = equal_object_refs(v1, v2)
        else:
            equal_values = v1 == v2

        if not equal_values:
            return False

    return True
