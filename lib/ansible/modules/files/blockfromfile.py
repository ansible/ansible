#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Evan Kaufman <evan@digitalflophouse.com>
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: blockfromfile
author: "Evan Kaufman (@EvanK)"
version_added: "2.4"
short_description: Search file from remote node using a provided regular expression.
description:
  - This module will search a remote file for all instances of a pattern.
    Effectively the inverse of M(replace).
options:
  src:
    required: true
    aliases: [ name, srcfile ]
    description:
      - The file to search.
  regexp:
    required: true
    description:
      - The regular expression to look for in the contents of the file.
        Uses Python regular expressions; see
        U(http://docs.python.org/2/library/re.html).
        Uses multiline mode, which means C(^) and C($) match the beginning
        and end respectively of I(each line) of the file.
  fail_on_missing:
    required: false
    default: false
    description:
      - Makes it fails when the source file is missing.
notes:
   - "See also: M(replace)"
"""

EXAMPLES = r"""
# finds one named group, "priority"
- blockfromfile:
    src: /etc/keepalived/keepalived.conf
    regexp: '^[ \t\f\v]*priority[ \t\f\v]*(?P<priority>\d+)[ \t\f\v]*'

# finds two named groups, "address" and "hostnames"
- blockfromfile:
    src: /etc/hosts
    regexp: '^[ \t\f\v]*(?P<address>[\d.:]+)[ \t\f\v]*(?P<hostnames>(?:\S+[ \t\f\v]*)+)'

# finds one unnamed group
- blockfromfile:
    src: /etc/sudoers
    regexp: '^(\S+)(?:[ \t\f\v]*\s+)*NOPASSWD:ALL'
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
from ansible.module_utils.pycompat24 import get_exception
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
            src=dict(required=True, aliases=['name', 'srcfile', 'path'], type='path'),
            regexp=dict(required=True),
            fail_on_missing=dict(required=False, default=False, type='bool'),
            encoding=dict(default='utf-8', type='str'),
        ),
        supports_check_mode=True
    )

    params = module.params
    params['regexp'] = to_text(params['regexp'], errors='surrogate_or_strict', nonstring='passthru')
    src = params['src']

    if os.path.isdir(src):
        module.fail_json(rc=256, msg='Source %s is a directory !' % src)

    if not os.path.exists(src):
        if params['fail_on_missing']:
            module.fail_json(rc=255, msg='Source %s does not exist !' % src)
        else:
            module.exit_json(changed=False, msg='Source %s does not exist !' % src)
    else:
        try:
            f = open(src, 'rb')
            contents = to_text(f.read(), errors='surrogate_or_strict', encoding=params['encoding'])
            f.close()
        except IOError:
            e = get_exception()
            module.fail_json(rc=254, msg='Source %s could not be read: %s' % (src, e.strerror))

    result = find_from_content(params['regexp'], contents)

    if result:
        module.exit_json(matches=result, changed=True, msg='Found %d matches in %s' % (len(result), src))
    else:
        module.exit_json(changed=False, msg='Found no matches in %s' % src)

if __name__ == '__main__':
    main()
