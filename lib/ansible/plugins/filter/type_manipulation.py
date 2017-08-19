#! /usr/bin/env python

from ansible import errors


def list_to_dict(data, key):
    new_obj = {}
    
    if not isinstance(data, list):
        raise errors.AnsibleFilterError("Type is not a valid list")
    for item in data:
        if not isinstance(item, dict):
            raise errors.AnsibleFilterError("List item is not a valid dict")
        try:
            key_elem = item.get(key)
        except Exception, e:
            raise errors.AnsibleFilterError(str(e))
        if new_obj.get(key_elem):
            raise errors.AnsibleFilterError("Key {} is not unique, cannot correctly turn into dict".format(key_elem))
        elif not key_elem:
            raise errors.AnsibleFilterError("Key {} was not found".format(key_elem))
        else:
            new_obj[key_elem] = item
    return new_obj


def dict_to_list(data, key_name):
    new_obj = []

    if not isinstance(data, dict):
        raise errors.AnsibleFilterError("Type is not a valid dict")
    for key, value in data.items():
        if not isinstance(value, dict):
            raise errors.AnsibleFilterError("Type of key {} value {} is not a valid dict".format(key, value))
        if value.get(key):
            raise errors.AnsibleFilterError("Key name {} is already in use, cannot correctly turn into dict".format(key_name))
        value[key_name] = key
        new_obj.append(value)
    return new_obj


class FilterModule(object):
    '''Convert a list to a dictionary provided a key that exists in all dicts.
        If it does not, that dict is omitted
    '''
    def filters(self):
        return {
            'list_to_dict': list_to_dict,
            'dict_to_list': dict_to_list,
        }


if __name__ == "__main__":
    list_data = [{'proto':'eigrp', 'state':'enabled'}, {'proto':'ospf', 'state':'enabled'}]
    print list_to_dict(list_data, 'proto')
    dict_data = {'eigrp': {'state': 'enabled', 'as': '1'}, 'ospf': {'state': 'enabled', 'as': '2'}}
    print dict_to_list(dict_data, 'proto')
