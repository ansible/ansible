# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 Willem van Ketwich
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.
#
# Author:
#   - Willem van Ketwich <willem@vanketwich.com.au>
#
# Common functionality to be used by the modules:
#   - cloudfront_distribution
#   - cloudfront_invalidation
#   - cloudfront_origin_access_identity


class CloudFrontHelpers:
    """
    Miscellaneous helpers for processing cloudfront data
    """

    def change_dict_key_name(self, dictionary, old_key, new_key):
        if old_key in dictionary:
            dictionary[new_key] = dictionary.get(old_key)
            dictionary.pop(old_key, None)
        return dictionary

    def snake_dict_to_pascal_dict(self, snake_dict):
        def pascalize(complex_type):
            if complex_type is None:
                return
            new_type = type(complex_type)()
            if isinstance(complex_type, dict):
                for key in complex_type:
                    new_type[pascal(key)] = pascalize(complex_type[key])
            elif isinstance(complex_type, list):
                for i in range(len(complex_type)):
                    new_type.append(pascalize(complex_type[i]))
            else:
                return complex_type
            return new_type

        def pascal(words):
            return words.capitalize().split('_')[0] + ''.join(x.capitalize() or '_' for x in words.split('_')[1:])
        return pascalize(snake_dict)

    def pascal_dict_to_snake_dict(self, pascal_dict, split_caps=False):
        def pascal_to_snake(name):
            import re
            first_cap_re = re.compile('(.)([A-Z][a-z]+)')
            all_cap_re = re.compile('([a-z0-9])([A-Z]+)')
            split_cap_re = re.compile('([A-Z])')
            s1 = first_cap_re.sub(r'\1\2', name)
            if split_caps:
                s2 = split_cap_re.sub(r'_\1', s1).lower()
                s2 = s2[1:] if s2[0] == '_' else s2
            else:
                s2 = all_cap_re.sub(r'\1_\2', s1).lower()
            return s2

        def value_is_list(pascal_list):
            checked_list = []
            for item in pascal_list:
                if isinstance(item, dict):
                    checked_list.append(self.pascal_dict_to_snake_dict(item, split_caps))
                elif isinstance(item, list):
                    checked_list.append(value_is_list(item))
                else:
                    checked_list.append(item)
            return checked_list
        snake_dict = {}
        for k, v in pascal_dict.items():
            if isinstance(v, dict):
                snake_dict[pascal_to_snake(k)] = self.pascal_dict_to_snake_dict(v, split_caps)
            elif isinstance(v, list):
                snake_dict[pascal_to_snake(k)] = value_is_list(v)
            else:
                snake_dict[pascal_to_snake(k)] = v
        return snake_dict

    def merge_validation_into_config(self, config, validated_node, node_name):
        if validated_node is not None:
            if isinstance(validated_node, dict):
                config_node = config.get(node_name)
                if config_node is not None:
                    config_node_items = config_node.items()
                else:
                    config_node_items = []
                config[node_name] = dict(config_node_items + validated_node.items())
            if isinstance(validated_node, list):
                config[node_name] = list(set(config.get(node_name) + validated_node))
        return config

    def python_list_to_aws_list(self, list_items=None, include_quantity=True):
        if list_items is None:
            list_items = []
        if not isinstance(list_items, list):
            self.module.fail_json(
                msg='expected a python list, got a python {0} with value {1}'.format(
                    type(list_items).__name__, str(list_items)))
        result = {}
        if include_quantity:
            result['quantity'] = len(list_items)
        result['items'] = list_items
        return result
