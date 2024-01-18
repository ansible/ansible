#!/usr/bin/env python

# (c) 2017, Will Thames <will@thames.id.au>
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

# return_skeleton_generator.py takes JSON output from a module and
# and creates a starting point for the RETURNS section of a module.
# This can be provided as stdin or a file argument
#
# The easiest way to obtain the JSON output is to use hacking/test-module.py
#
# You will likely want to adjust this to remove sensitive data or
# ensure the `returns` value is correct, and to write a useful description

from __future__ import annotations

from collections import OrderedDict
import json
import sys
import yaml


# Allow OrderedDicts to be used when dumping YAML
# https://stackoverflow.com/a/16782282/3538079
def represent_ordereddict(dumper, data):
    value = []

    for item_key, item_value in data.items():
        node_key = dumper.represent_data(item_key)
        node_value = dumper.represent_data(item_value)

        value.append((node_key, node_value))

    return yaml.nodes.MappingNode(u'tag:yaml.org,2002:map', value)


def get_return_data(key, value):
    # The OrderedDict here is so that, for complex objects, the
    # summary data is at the top before the contains information
    returns_info = {key: OrderedDict()}
    returns_info[key]['description'] = "FIXME *** add description for %s" % key
    returns_info[key]['returned'] = "always"
    if isinstance(value, dict):
        returns_info[key]['type'] = 'complex'
        returns_info[key]['contains'] = get_all_items(value)
    elif isinstance(value, list) and value and isinstance(value[0], dict):
        returns_info[key]['type'] = 'complex'
        returns_info[key]['contains'] = get_all_items(value[0])
    else:
        returns_info[key]['type'] = type(value).__name__
        returns_info[key]['sample'] = value
        # override python unicode type to set to string for docs
        if returns_info[key]['type'] == 'unicode':
            returns_info[key]['type'] = 'str'
    return returns_info


def get_all_items(data):
    items = sorted([get_return_data(key, value) for key, value in data.items()])
    result = OrderedDict()
    for item in items:
        key, value = item.items()[0]
        result[key] = value
    return result


def main(args):
    yaml.representer.SafeRepresenter.add_representer(OrderedDict, represent_ordereddict)

    if args:
        src = open(args[0])
    else:
        src = sys.stdin

    data = json.load(src, strict=False)
    docs = get_all_items(data)
    if 'invocation' in docs:
        del docs['invocation']
    print(yaml.safe_dump(docs, default_flow_style=False))


if __name__ == '__main__':
    main(sys.argv[1:])
