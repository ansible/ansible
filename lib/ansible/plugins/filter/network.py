#
# {c) 2017 Red Hat, Inc.
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
import os
import json

from collections import Mapping

from ansible.module_utils.network_common import Template
from ansible.module_utils.six import iteritems, string_types
from ansible.errors import AnsibleError

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    import textfsm
    HAS_TEXTFSM = True
except ImportError:
    HAS_TEXTFSM = False


try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


def re_matchall(regex, value):
    objects = list()
    for match in re.findall(regex.pattern, value, re.M):
        obj = {}
        if regex.groupindex:
            for name, index in iteritems(regex.groupindex):
                if len(regex.groupindex) == 1:
                    obj[name] = match
                else:
                    obj[name] = match[index - 1]
            objects.append(obj)
    return objects


def re_search(regex, value):
    obj = {}
    match = regex.search(value, re.M)
    if match:
        items = list(match.groups())
        if regex.groupindex:
            for name, index in iteritems(regex.groupindex):
                obj[name] = items[index - 1]
    return obj


def parse_cli(output, tmpl):
    if not isinstance(output, string_types):
        raise AnsibleError("parse_cli input should be a string, but was given a input of %s" % (type(output)))

    if not os.path.exists(tmpl):
        raise AnsibleError('unable to locate parse_cli template: %s' % tmpl)

    try:
        template = Template()
    except ImportError as exc:
        raise AnsibleError(str(exc))

    spec = yaml.safe_load(open(tmpl).read())
    obj = {}

    for name, attrs in iteritems(spec['keys']):
        value = attrs['value']

        try:
            variables = spec.get('vars', {})
            value = template(value, variables)
        except:
            pass

        if 'start_block' in attrs and 'end_block' in attrs:
            start_block = re.compile(attrs['start_block'])
            end_block = re.compile(attrs['end_block'])

            blocks = list()
            lines = None
            block_started = False

            for line in output.split('\n'):
                match_start = start_block.match(line)
                match_end = end_block.match(line)

                if match_start:
                    lines = list()
                    lines.append(line)
                    block_started = True

                elif match_end:
                    if lines:
                        lines.append(line)
                        blocks.append('\n'.join(lines))
                    block_started = False

                elif block_started:
                    if lines:
                        lines.append(line)

            regex_items = [re.compile(r) for r in attrs['items']]
            objects = list()

            for block in blocks:
                if isinstance(value, Mapping) and 'key' not in value:
                    items = list()
                    for regex in regex_items:
                        match = regex.search(block)
                        if match:
                            item_values = match.groupdict()
                            item_values['match'] = list(match.groups())
                            items.append(item_values)
                        else:
                            items.append(None)

                    obj = {}
                    for k, v in iteritems(value):
                        try:
                            obj[k] = template(v, {'item': items}, fail_on_undefined=False)
                        except:
                            obj[k] = None
                    objects.append(obj)

                elif isinstance(value, Mapping):
                    items = list()
                    for regex in regex_items:
                        match = regex.search(block)
                        if match:
                            item_values = match.groupdict()
                            item_values['match'] = list(match.groups())
                            items.append(item_values)
                        else:
                            items.append(None)

                    key = template(value['key'], {'item': items})
                    values = dict([(k, template(v, {'item': items})) for k, v in iteritems(value['values'])])
                    objects.append({key: values})

            return objects

        elif 'items' in attrs:
            regexp = re.compile(attrs['items'])
            when = attrs.get('when')
            conditional = "{%% if %s %%}True{%% else %%}False{%% endif %%}" % when

            if isinstance(value, Mapping) and 'key' not in value:
                values = list()

                for item in re_matchall(regexp, output):
                    entry = {}

                    for item_key, item_value in iteritems(value):
                        entry[item_key] = template(item_value, {'item': item})

                    if when:
                        if template(conditional, {'item': entry}):
                            values.append(entry)
                    else:
                        values.append(entry)

                obj[name] = values

            elif isinstance(value, Mapping):
                values = dict()

                for item in re_matchall(regexp, output):
                    entry = {}

                    for item_key, item_value in iteritems(value['values']):
                        entry[item_key] = template(item_value, {'item': item})

                    key = template(value['key'], {'item': item})

                    if when:
                        if template(conditional, {'item': {'key': key, 'value': entry}}):
                            values[key] = entry
                    else:
                        values[key] = entry

                obj[name] = values

            else:
                item = re_search(regexp, output)
                obj[name] = template(value, {'item': item})

        else:
            obj[name] = value

    return obj


def parse_cli_textfsm(value, template):
    if not HAS_TEXTFSM:
        raise AnsibleError('parse_cli_textfsm filter requires TextFSM library to be installed')

    if not isinstance(value, string_types):
        raise AnsibleError("parse_cli_textfsm input should be a string, but was given a input of %s" % (type(value)))

    if not os.path.exists(template):
        raise AnsibleError('unable to locate parse_cli_textfsm template: %s' % template)

    try:
        template = open(template)
    except IOError as exc:
        raise AnsibleError(str(exc))

    re_table = textfsm.TextFSM(template)
    fsm_results = re_table.ParseText(value)

    results = list()
    for item in fsm_results:
        results.append(dict(zip(re_table.header, item)))

    return results


class FilterModule(object):
    """Filters for working with output from network devices"""

    filter_map = {
        'parse_cli': parse_cli,
        'parse_cli_textfsm': parse_cli_textfsm
    }

    def filters(self):
        return self.filter_map
