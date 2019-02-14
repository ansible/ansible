# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import re

try:
    from library.module_utils.network.f5.common import F5ModuleError
except ImportError:
    from ansible.module_utils.network.f5.common import F5ModuleError

_CLEAN_HEADER_REGEX_BYTE = re.compile(b'^\\S[^\\r\\n]*$|^$')
_CLEAN_HEADER_REGEX_STR = re.compile(r'^\S[^\r\n]*$|^$')


def check_header_validity(header):
    """Verifies that header value is a string which doesn't contain
    leading whitespace or return characters.

    NOTE: This is a slightly modified version of the original function
          taken from the requests library:
          http://docs.python-requests.org/en/master/_modules/requests/utils/

    :param header: string containing ':'.
    """
    try:
        name, value = header.split(':')
    except ValueError:
        raise F5ModuleError('Invalid header format: {0}'.format(header))
    if name == '':
        raise F5ModuleError('Invalid header format: {0}'.format(header))

    if isinstance(value, bytes):
        pat = _CLEAN_HEADER_REGEX_BYTE
    else:
        pat = _CLEAN_HEADER_REGEX_STR
    try:
        if not pat.match(value):
            raise F5ModuleError("Invalid return character or leading space in header: %s" % name)
    except TypeError:
        raise F5ModuleError("Value for header {%s: %s} must be of type str or "
                            "bytes, not %s" % (name, value, type(value)))


def build_service_uri(base_uri, partition, name):
    """Build the proper uri for a service resource.
    This follows the scheme:
        <base_uri>/~<partition>~<<name>.app>~<name>
    :param base_uri: str -- base uri of the REST endpoint
    :param partition: str -- partition for the service
    :param name: str -- name of the service
    :returns: str -- uri to access the service
    """
    name = name.replace('/', '~')
    return '%s~%s~%s.app~%s' % (base_uri, partition, name, name)


def parseStats(entry):
    if 'description' in entry:
        return entry['description']
    elif 'value' in entry:
        return entry['value']
    elif 'entries' in entry or 'nestedStats' in entry and 'entries' in entry['nestedStats']:
        if 'entries' in entry:
            entries = entry['entries']
        else:
            entries = entry['nestedStats']['entries']
        result = None

        for name in entries:
            entry = entries[name]
            if 'https://localhost' in name:
                name = name.split('/')
                name = name[-1]
                if result and isinstance(result, list):
                    result.append(parseStats(entry))
                elif result and isinstance(result, dict):
                    result[name] = parseStats(entry)
                else:
                    try:
                        int(name)
                        result = list()
                        result.append(parseStats(entry))
                    except ValueError:
                        result = dict()
                        result[name] = parseStats(entry)
            else:
                if '.' in name:
                    names = name.split('.')
                    key = names[0]
                    value = names[1]
                    if result is None:
                        # result can be None if this branch is reached first
                        #
                        # For example, the mgmt/tm/net/trunk/NAME/stats API
                        # returns counters.bitsIn before anything else.
                        result = dict()
                        result[key] = dict()
                    elif key not in result:
                        result[key] = dict()
                    elif result[key] is None:
                        result[key] = dict()
                    result[key][value] = parseStats(entry)
                else:
                    if result and isinstance(result, list):
                        result.append(parseStats(entry))
                    elif result and isinstance(result, dict):
                        result[name] = parseStats(entry)
                    else:
                        try:
                            int(name)
                            result = list()
                            result.append(parseStats(entry))
                        except ValueError:
                            result = dict()
                            result[name] = parseStats(entry)
        return result
