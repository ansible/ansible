#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Evan Kaufman <evan@digitalflophouse.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: blockfromfile
author:
  - Evan Kaufman (@EvanK)
version_added: "2.5"
short_description: Find instances of pattern in a file
description:
  - This module will search the contents of a file for all instances of a
    regular expression pattern.
  - Effectively the inverse of M(replace).
options:
  path:
    required: true
    aliases: [ src ]
    description:
      - The file to search.
  regexp:
    required: true
    description:
      - The regular expression to look for in the contents of the file.
      - Uses Python regular expressions; see
        U(http://docs.python.org/2/library/re.html).
      - Uses multiline mode, which means C(^) and C($) match the beginning
        and end respectively of I(each line) of the file.
  fail_on_missing:
    description:
      - When set to C(yes), fail when the file is missing.
    type: bool
    default: 'no'

notes:
   - See also M(replace)
"""

EXAMPLES = r"""
# finds one named group, "priority"
- blockfromfile:
    path: /etc/keepalived/keepalived.conf
    regexp: '^[ \t\f\v]*priority[ \t\f\v]*(?P<priority>\d+)[ \t\f\v]*'

# finds two named groups, "address" and "hostnames"
- blockfromfile:
    path: /etc/hosts
    regexp: '^[ \t\f\v]*(?P<address>[a-f\d.:]+)[ \t\f\v]*(?P<hostnames>(?:\S+[ \t\f\v]*)+)'

# finds one unnamed group
- blockfromfile:
    path: /etc/sudoers
    regexp: '^[ \t\f\v]*(\S+)(?:[ \t\f\v]+\S*)+NOPASSWD:ALL'
"""

RETURN = """
matches:
    description: numbered or named regular expression groups
    returned: changed
    type: list
    sample: [ { "groups": [ "VALUE" ], "named_groups": { "NAME": "VALUE" } } ]
"""

import re
import os

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule


def find_from_content(regexp, content):
    result = []
    found = re.finditer(regexp, content, re.MULTILINE)

    for match in found:
        result.append({
            'groups': match.groups(),
            'named_groups': match.groupdict(),
        })

    return result


def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type='path', required=True, aliases=['src']),
            regexp=dict(type='str', required=True),
            fail_on_missing=dict(type='bool', default=False),
            encoding=dict(type='str', default='utf-8'),
        ),
        supports_check_mode=True
    )

    params = module.params
    params['regexp'] = to_text(params['regexp'], errors='surrogate_or_strict', nonstring='passthru')
    src = params['path']

    if os.path.isdir(src):
        module.fail_json(msg="File '%s' is a directory !" % src)

    if not os.path.exists(src):
        if params['fail_on_missing']:
            module.fail_json(msg="File '%s' does not exist !" % src)
        else:
            module.exit_json(changed=False, msg="File '%s' does not exist !" % src)
    else:
        try:
            with open(src, 'rb') as f:
                contents = to_text(f.read(), errors='surrogate_or_strict', encoding=params['encoding'])
        except IOError as e:
            module.fail_json(msg="File '%s' could not be read: %s" % (src, e.strerror))

    result = find_from_content(params['regexp'], contents)
    module.exit_json(matches=result, changed=bool(result), msg="Found %d matches in '%s'" % (len(result), src))

if __name__ == '__main__':
    main()
