#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
module: github_issue
short_description: View GitHub issue
description:
    - View GitHub issue for a given repository.
version_added: "2.4"
options:
  repo:
    description:
      - Name of repository from which issue needs to be retrieved.
    type: str
    required: true
  organization:
    description:
      - Name of the GitHub organization in which the repository is hosted.
    type: str
    required: true
  issue:
    description:
      - Issue number for which information is required.
    type: str
    required: true
  action:
    description:
        - Get various details about issue depending upon action specified.
    type: str
    choices: [ get_status ]
    default: get_status
author:
    - Abhijeet Kasurde (@Akasurde)
requirements:
    - github3.py >= 1.0.0a4
'''

RETURN = r'''
issue_status:
    description: State of the GitHub issue
    type: str
    returned: success
    sample: open, closed
'''

EXAMPLES = r'''
- name: Check if GitHub issue is closed or not
  github_issue:
    organization: ansible
    repo: ansible
    issue: 23642
    action: get_status
  register: r

- name: Take action depending upon issue status
  debug:
    msg: Do something when issue 23642 is open
  when: r.issue_status == 'open'
'''

import traceback

GITHUB_IMP_ERR = None
try:
    import github3
    HAS_GITHUB_PACKAGE = True
except ImportError:
    GITHUB_IMP_ERR = traceback.format_exc()
    HAS_GITHUB_PACKAGE = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib


def main():
    module = AnsibleModule(
        argument_spec=dict(
            organization=dict(type='str', required=True),
            repo=dict(type='str', required=True),
            issue=dict(type='str', required=True),
            action=dict(type='str', default='get_status', choices=['get_status']),
        ),
        supports_check_mode=True,
    )

    if not HAS_GITHUB_PACKAGE:
        module.fail_json(msg=missing_required_lib('github3.py >= 1.0.0a4'),
                         exception=GITHUB_IMP_ERR)

    organization = module.params['organization']
    repo = module.params['repo']
    issue = module.params['issue']
    action = module.params['action']

    result = dict(
        changed=False,
    )

    gh_obj = github3.issue(organization, repo, issue)
    if gh_obj is None:
        module.fail_json(msg="Failed to get details about issue specified. "
                             "Please check organization, repo and issue "
                             "details and try again.")

    if action == 'get_status':
        result['issue_status'] = gh_obj.state

    module.exit_json(**result)


if __name__ == '__main__':
    main()
