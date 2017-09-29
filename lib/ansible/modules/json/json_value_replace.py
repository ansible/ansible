#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import *

DOCUMENTATION = '''
---
module: json_value_replace
short_description: Replace values in json that fulfil a condition. Values must be type-hinted.
description:
  - This module allows the value of a field in JSON to be replaced.
  - Value can only be changed if the conditions is true.
  - It can operate on up to 1 level of nesting in the JSON. For example
    - In pizza JSON similar to '{name = Chocoholic, toppings = {id = 5001, type = Chocolate}}' you'd be able to change the fields
      on the same level on "name" and "type".
  - This module requires the values to be hinted so it can be converted accordingly.
    - Supported hints are "b -> boolean, i -> integer, f -> float and s -> string"
version_added: "2.4.0"
author: "Fabio Serragnoli (@serragnoli)"
options:
  json_string:
    description:
      - Json string representation of the file to be processed, it cannot be escaped.
    required: true
  condition_field:
    description:
      - The path (dot-separated) to the field which the condition will be evaluated for. Example
        For the pizza representation above "toppings.id".
    required: true
  condition_value:
    description:
      - The evaluation criterion for the field above.
      - Note that hints of the type of the value need to be passed here "b -> boolean, i -> integer, f- float and s -> string".
    required: true
  changing_field:
    description:
      - The field which the value is to be changed. It doesn't need to be the same field of the condition.
      - It can 'condition_field' itself. If not, it must be sibling of the 'condition_field'.
      - The first matching condition will be changes when more than one matches
    required: true
  changing_field_new_value:
    description:
      - The new value of the field 'changing_field'.
      - This value also need to be hinted "b -> boolean, i -> integer, f- float and s -> string".
    required: true
'''

EXAMPLES = '''
# Replace the text (hint ':s') that matches 'Chocoholic' by the text (hint 's' again) 'Bananaholic' on the parent level
- json_value_replace:
    json_string: "{{contents|to_json}}"
    condition_field: name
    condition_value: Chocoholic:s
    changing_field: name
    changing_field_new_value: Bananaholic:s
    
# Replace the topping id (hint ':i') that matches '5001' by the float (hint 'f') '123'
- json_value_replace:
    json_string: "{{contents|to_json}}"
    condition_field: toppings.id
    condition_value: 5001:i
    changing_field: id
    changing_field_new_value: 123:f

# Replace the topping type to 'Chocolate' if the topping id matches (hint ':i') '5001'
- json_value_replace:
    json_string: "{{contents|to_json}}"
    condition_field: toppings.id
    condition_value: 5001:i
    changing_field: type
    changing_field_new_value: Chocolate:s
 
# Add id '123' to the topping that has id null (just don't add anything before the hint, any hint must still be present)
- json_value_replace:
    json_string: "{{contents|to_json}}"
    condition_field: toppings.id
    condition_value: :i
    changing_field: id
    changing_field_new_value: 123:i
'''


def main():
    params = {
        "json_string": {"required": True, "type": "str"},
        "condition_field": {"required": True, "type": "str"},
        "condition_value": {"required": True, "type": "str"},
        "changing_field": {"required": True, "type": "str"},
        "changing_field_new_value": {"required": True, "type": "str"}
    }
    slt_module = AnsibleModule(argument_spec=params)

    loaded_info = feed_loaded_info(slt_module)
    validate_condition_and_update(loaded_info['loaded_json'], loaded_info['condition_field_split'],
                                  loaded_info['condition_value_parsed'],
                                  loaded_info['changing_field'],
                                  loaded_info['changing_field_new_value_parsed'],
                                  slt_module)

    # print_output(loaded_info['loaded_json'])
    slt_module.exit_json(changed=True, json=loaded_info['loaded_json'])


def feed_loaded_info(slt_module):
    return {'loaded_json': json.loads(slt_module.params['json_string']),
            'condition_field_split': parse_condition_field(slt_module.params['condition_field']),
            'condition_value_parsed': parse_condition_value(slt_module.params['condition_value'], slt_module),
            'changing_field': slt_module.params['changing_field'],
            'changing_field_new_value_parsed': parse_condition_value(slt_module.params['changing_field_new_value'],
                                                                     slt_module)}


def validate_condition_and_update(orig_json, cond_field_split, cond_value, changing_field,
                                  changing_field_new_value_parsed, slt_module):
    if is_leaf(cond_field_split):
        if cond_field_split[0] in orig_json:
            orig_json[changing_field] = changing_field_new_value_parsed
        else:
            traverse_to_match(cond_field_split, cond_value, changing_field, changing_field_new_value_parsed, orig_json)
    else:
        try:
            validate_condition_and_update(orig_json[cond_field_split.pop(0)], cond_field_split, cond_value,
                                          changing_field,
                                          changing_field_new_value_parsed, slt_module)
        except TypeError:
            slt_module.fail_json(msg="Only 2 levels of nesting is supported")


def is_leaf(cond_field_split):
    return len(cond_field_split) == 1


def traverse_to_match(cond_field_split, cond_value, changing_field, changing_field_new_value_parsed, orig_json):
    for oj in orig_json:
        if oj[cond_field_split[0]] == cond_value:
            oj[changing_field] = changing_field_new_value_parsed
            break


def parse_condition_field(unsplit_fields):
    return unsplit_fields.split(".")


def parse_condition_value(cond_value, slt_module):
    split_cond_value = cond_value.split(":")
    the_type = None
    the_value = None

    try:
        the_type = split_cond_value[1]
        the_value = split_cond_value[0]
    except IndexError:
        slt_module.fail_json(msg="You probably forgot to add the type hint. Ex.: \'1111:i\'")

    try:
        if the_value is None or len(the_value) == 0:
            return None
        if the_type == "s":
            return str(the_value)
        elif the_type == "b":
            return bool(the_value)
        elif the_type == "i":
            return int(the_value)
        elif the_type == "f":
            return float(the_value)
        else:
            slt_module.fail_json(msg="Unsupported type hint. Accepted b, i, f and s")
    except ValueError:
        slt_module.fail_json(msg="Could not convert the data to the type specified in the type hint")


def print_output(loaded_json):
    with open('printed_output.json', 'w') as outfile:
        json.dump(loaded_json, outfile)


if __name__ == '__main__':
    main()
