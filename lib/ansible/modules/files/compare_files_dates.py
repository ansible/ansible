#!/usr/bin/python
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or # https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: compare_files_dates
version_added: "2.8"
short_description: compare make-alike source and target files by their date
description:
     - Source and target files are compared based on their modification time.
     - This results in differently structured list containing files where the
       target is older than the source.
     - Missing targets are handled like older, missing sources lead to a
       failed task.
options:
  sources:
    description:
      - a list of source files to be compared with the target files
    type: list
    required: true
  targets:
    description:
      - a list of target files to be compared with the source files
    type: list
    required: true
  follow:
    description:
      - Whether to follow symlinks.
    type: bool
    default: 'no'
author: Eric Lavarde (@ericzolf)
'''

EXAMPLES = '''
# We first compare all sources with all targets files:

- name: compare sources with targets
  compare_files_dates:
    sources:
    - source.local.A
    - source.local.B
    targets:
    - target.local.A
    - target.local.B
  register: res

# The result contains a list of all pairs of source/target files where the
# target is older than the source, which can loop through:

- name: add one by one sources to targets (we could also compile them)
  shell: cat "{{ item.0 }}" >> {{ item.1 }}
  loop: "{{ res.pairs }}"

# Another approach is to go through the dict of target files, which have as
# value a list of the newer sources:

- name: add at once sources to targets (we could also compile them)
  shell: "cat {{ item.value | map('quote') | join(' ') }} > {{ item.key }}"
  loop: "{{ res.by_target | dict2items }}"

# Taking a more complex but also more flexible approach, we define first
# a dependency tree of target and sources files, e.g. like this:

- set_fact:
    dependencies:
      target.local.1:
      - source.local.1
      - source.local.2
      target.local.2:
      - source.local.2
      target.local.3:
      - source.local.2
      - source.local.3

# Then we go through the tree using a loop, capturing the result in a quite
# complex structure for further use (we'll try to make this easier in a
# future version):

- name: compare sources with targets
  compare_files_dates:
    targets: "{{ item.key }}"
    sources: "{{ item.value }}"
  loop: "{{ dependencies | dict2items }}"
  register: res

# Using the json_query filter, we can then grab the information we need, either
# one by one:

- name: add one by one sources to targets (we could also compile them)
  shell: cat "{{ item.0 }}" >> "{{ item.1 }}"
  loop: "{{ res | json_query('results[*].pairs[]') }}"

# or similarly to the simpler example, all at once:

- name: add at once sources to targets (we could also compile them)
  shell: "cat {{ item.value | map('quote') | join(' ') }} > {{ item.key }}"
  loop: "{{ res | json_query('results[*].by_target') | combine() | dict2items }}"
'''

RETURN = r'''
pairs:
    description: list of pairs of source and target files where the target is older than the source
    returned: success
    type: list
    sample: [ [ 'source1', 'target1' ], [ 'source1', 'target2' ] ]
by_target:
    description: a dictionary with target files as keys and a list of newer source files as value
    returned: success
    type: complex
    sample: { 'target1': [ 'source1', 'source2' ], 'target2': [ 'source1'] }
by_source:
    description: a dictionary with source files as keys and a list of older target files as value
    returned: success
    type: complex
    sample: { 'source1': [ 'target1', 'target3' ], 'source2': [ 'target2'] }
count:
    description: number of pairs of source/target files
    returned: success
    type: int
'''

import errno
import os
import stat

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes


def main():
    module = AnsibleModule(
        argument_spec=dict(
            sources=dict(required=True, type='list'),
            targets=dict(required=True, type='list'),
            follow=dict(type='bool', default='no')
        ),
        supports_check_mode=True,
    )

    sources = module.params.get('sources')
    targets = module.params.get('targets')
    follow = module.params.get('follow')

    files_pairs = []
    files_by_target = {}
    files_by_source = {}
    files_count = 0

    # main stat data
    for target in targets:
        b_target = to_bytes(target, errors='surrogate_or_strict')
        try:
            if follow:
                st_target = os.stat(b_target)
            else:
                st_target = os.lstat(b_target)
            mtime_target = st_target.st_mtime
        except OSError as e:
            if e.errno == errno.ENOENT:
                mtime_target = 0  # if the file doesn't exist
            else:
                module.fail_json(msg=target + ": " + e.strerror)

        for source in sources:
            b_source = to_bytes(source, errors='surrogate_or_strict')
            try:
                if follow:
                    st_source = os.stat(b_source)
                else:
                    st_source = os.lstat(b_source)
                mtime_source = st_source.st_mtime
            except OSError as e:
                module.fail_json(msg=source + ": " + e.strerror)
            if mtime_target < mtime_source:
                files_count += 1
                files_pairs.append((source, target))
                if target in files_by_target:
                    files_by_target[target].append(source)
                else:
                    files_by_target[target] = [source]
                if source in files_by_source:
                    files_by_source[source].append(target)
                else:
                    files_by_source[source] = [target]

    module.exit_json(changed=False,
                     pairs=files_pairs,
                     by_target=files_by_target,
                     by_source=files_by_source,
                     count=files_count)


if __name__ == '__main__':
    main()
