# Author Ken Celenza <ken@networktocode.com>
# Author Jason Edelman <jason@networktocode.com>

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleError, AnsibleFilterError


def cast_list_to_dict(data, key):
    new_obj = {}

    if not isinstance(data, list):
        raise AnsibleFilterError("Type is not a valid list")
    for item in data:
        if not isinstance(item, dict):
            raise AnsibleFilterError("List item is not a valid dict")
        try:
            key_elem = item.get(key)
        except Exception as e:
            raise AnsibleFilterError(str(e))
        if new_obj.get(key_elem):
            raise AnsibleFilterError("Key {0} is not unique, cannot correctly turn into dict".format(key_elem))
        elif not key_elem:
            raise AnsibleFilterError("Key {0} was not found".format(key))
        else:
            new_obj[key_elem] = item
    return new_obj


def cast_dict_to_list(data, key_name):
    new_obj = []

    if not isinstance(data, dict):
        raise AnsibleFilterError("Type is not a valid dict")
    for key, value in data.items():
        if not isinstance(value, dict):
            raise AnsibleFilterError("Type of key {0} value {1} is not a valid dict".format(key, value))
        if value.get(key_name):
            raise AnsibleFilterError("Key name {0} is already in use, cannot correctly turn into dict".format(key_name))
        value[key_name] = key
        new_obj.append(value)
    return new_obj


class FilterModule(object):
    '''Convert a list to a dictionary provided a key that exists in all dicts.
        If it does not, that dict is omitted
    '''
    def filters(self):
        return {
            'cast_list_to_dict': cast_list_to_dict,
            'cast_dict_to_list': cast_dict_to_list,
        }


if __name__ == "__main__":
    list_data = [{"proto": "eigrp", "state": "enabled"}, {"proto": "ospf", "state": "enabled"}]
    print(cast_list_to_dict(list_data, 'proto'))

    dict_data = {'eigrp': {'state': 'enabled', 'as': '1'}, 'ospf': {'state': 'enabled', 'as': '2'}}
    print(cast_dict_to_list(dict_data, 'proto'))
