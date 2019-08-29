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
import traceback
import string

from xml.etree.ElementTree import fromstring

from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.network.common.utils import Template
from ansible.module_utils.six import iteritems, string_types
from ansible.module_utils.common._collections_compat import Mapping
from ansible.errors import AnsibleError, AnsibleFilterError
from ansible.utils.display import Display
from ansible.utils.encrypt import passlib_or_crypt, random_password

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
        raise AnsibleError(to_native(exc))

    with open(tmpl) as tmpl_fh:
        tmpl_content = tmpl_fh.read()

    spec = yaml.safe_load(tmpl_content)
    obj = {}

    for name, attrs in iteritems(spec['keys']):
        value = attrs['value']

        try:
            variables = spec.get('vars', {})
            value = template(value, variables)
        except Exception:
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
                        except Exception:
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
        raise AnsibleError(to_native(exc))

    re_table = textfsm.TextFSM(template)
    fsm_results = re_table.ParseText(value)

    results = list()
    for item in fsm_results:
        results.append(dict(zip(re_table.header, item)))

    return results


def _extract_param(template, root, attrs, value):

    key = None
    when = attrs.get('when')
    conditional = "{%% if %s %%}True{%% else %%}False{%% endif %%}" % when
    param_to_xpath_map = attrs['items']

    if isinstance(value, Mapping):
        key = value.get('key', None)
        if key:
            value = value['values']

    entries = dict() if key else list()

    for element in root.findall(attrs['top']):
        entry = dict()
        item_dict = dict()
        for param, param_xpath in iteritems(param_to_xpath_map):
            fields = None
            try:
                fields = element.findall(param_xpath)
            except Exception:
                display.warning("Failed to evaluate value of '%s' with XPath '%s'.\nUnexpected error: %s." % (param, param_xpath, traceback.format_exc()))

            tags = param_xpath.split('/')

            # check if xpath ends with attribute.
            # If yes set attribute key/value dict to param value in case attribute matches
            # else if it is a normal xpath assign matched element text value.
            if len(tags) and tags[-1].endswith(']'):
                if fields:
                    if len(fields) > 1:
                        item_dict[param] = [field.attrib for field in fields]
                    else:
                        item_dict[param] = fields[0].attrib
                else:
                    item_dict[param] = {}
            else:
                if fields:
                    if len(fields) > 1:
                        item_dict[param] = [field.text for field in fields]
                    else:
                        item_dict[param] = fields[0].text
                else:
                    item_dict[param] = None

        if isinstance(value, Mapping):
            for item_key, item_value in iteritems(value):
                entry[item_key] = template(item_value, {'item': item_dict})
        else:
            entry = template(value, {'item': item_dict})

        if key:
            expanded_key = template(key, {'item': item_dict})
            if when:
                if template(conditional, {'item': {'key': expanded_key, 'value': entry}}):
                    entries[expanded_key] = entry
            else:
                entries[expanded_key] = entry
        else:
            if when:
                if template(conditional, {'item': entry}):
                    entries.append(entry)
            else:
                entries.append(entry)

    return entries


def parse_xml(output, tmpl):
    if not os.path.exists(tmpl):
        raise AnsibleError('unable to locate parse_xml template: %s' % tmpl)

    if not isinstance(output, string_types):
        raise AnsibleError('parse_xml works on string input, but given input of : %s' % type(output))

    root = fromstring(output)
    try:
        template = Template()
    except ImportError as exc:
        raise AnsibleError(to_native(exc))

    with open(tmpl) as tmpl_fh:
        tmpl_content = tmpl_fh.read()

    spec = yaml.safe_load(tmpl_content)
    obj = {}

    for name, attrs in iteritems(spec['keys']):
        value = attrs['value']

        try:
            variables = spec.get('vars', {})
            value = template(value, variables)
        except Exception:
            pass

        if 'items' in attrs:
            obj[name] = _extract_param(template, root, attrs, value)
        else:
            obj[name] = value

    return obj


def type5_pw(password, salt=None):
    if not isinstance(password, string_types):
        raise AnsibleFilterError("type5_pw password input should be a string, but was given a input of %s" % (type(password).__name__))

    salt_chars = u''.join((
        to_text(string.ascii_letters),
        to_text(string.digits),
        u'./'
    ))
    if salt is not None and not isinstance(salt, string_types):
        raise AnsibleFilterError("type5_pw salt input should be a string, but was given a input of %s" % (type(salt).__name__))
    elif not salt:
        salt = random_password(length=4, chars=salt_chars)
    elif not set(salt) <= set(salt_chars):
        raise AnsibleFilterError("type5_pw salt used inproper characters, must be one of %s" % (salt_chars))

    encrypted_password = passlib_or_crypt(password, "md5_crypt", salt=salt)

    return encrypted_password


def hash_salt(password):

    split_password = password.split("$")
    if len(split_password) != 4:
        raise AnsibleFilterError('Could not parse salt out password correctly from {0}'.format(password))
    else:
        return split_password[2]


def comp_type5(unencrypted_password, encrypted_password, return_original=False):

    salt = hash_salt(encrypted_password)
    if type5_pw(unencrypted_password, salt) == encrypted_password:
        if return_original is True:
            return encrypted_password
        else:
            return True
    return False


def vlan_parser(vlan_list, first_line_len=48, other_line_len=44):

    '''
        Input: Unsorted list of vlan integers
        Output: Sorted string list of integers according to IOS-like vlan list rules

        1. Vlans are listed in ascending order
        2. Runs of 3 or more consecutive vlans are listed with a dash
        3. The first line of the list can be first_line_len characters long
        4. Subsequent list lines can be other_line_len characters
    '''

    # Sort and remove duplicates
    sorted_list = sorted(set(vlan_list))

    if sorted_list[0] < 1 or sorted_list[-1] > 4094:
        raise AnsibleFilterError('Valid VLAN range is 1-4094')

    parse_list = []
    idx = 0
    while idx < len(sorted_list):
        start = idx
        end = start
        while end < len(sorted_list) - 1:
            if sorted_list[end + 1] - sorted_list[end] == 1:
                end += 1
            else:
                break

        if start == end:
            # Single VLAN
            parse_list.append(str(sorted_list[idx]))
        elif start + 1 == end:
            # Run of 2 VLANs
            parse_list.append(str(sorted_list[start]))
            parse_list.append(str(sorted_list[end]))
        else:
            # Run of 3 or more VLANs
            parse_list.append(str(sorted_list[start]) + '-' + str(sorted_list[end]))
        idx = end + 1

    line_count = 0
    result = ['']
    for vlans in parse_list:
        # First line (" switchport trunk allowed vlan ")
        if line_count == 0:
            if len(result[line_count] + vlans) > first_line_len:
                result.append('')
                line_count += 1
                result[line_count] += vlans + ','
            else:
                result[line_count] += vlans + ','

        # Subsequent lines (" switchport trunk allowed vlan add ")
        else:
            if len(result[line_count] + vlans) > other_line_len:
                result.append('')
                line_count += 1
                result[line_count] += vlans + ','
            else:
                result[line_count] += vlans + ','

    # Remove trailing orphan commas
    for idx in range(0, len(result)):
        result[idx] = result[idx].rstrip(',')

    # Sometimes text wraps to next line, but there are no remaining VLANs
    if '' in result:
        result.remove('')

    return result


class FilterModule(object):
    """Filters for working with output from network devices"""

    filter_map = {
        'parse_cli': parse_cli,
        'parse_cli_textfsm': parse_cli_textfsm,
        'parse_xml': parse_xml,
        'type5_pw': type5_pw,
        'hash_salt': hash_salt,
        'comp_type5': comp_type5,
        'vlan_parser': vlan_parser
    }

    def filters(self):
        return self.filter_map
