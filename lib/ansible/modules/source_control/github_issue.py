#!/usr/bin/python

# Copyright: (c) 2017-18, Abhijeet Kasurde <akasurde@redhat.com>
#
#  GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
module: github_issue
short_description: View GitHub issue.
description:
    - View GitHub issue for a given repository and organization.
version_added: "2.4"
options:
  repo:
    description:
      - Name of repository from which issue needs to be retrieved.
    required: true
  organization:
    description:
      - Name of the GitHub organization in which the repository is hosted.
    required: true
  issue:
    description:
      - Issue number for which information is required.
    required: true
  action:
    description:
        - Get various details about issue depending upon action specified.
    default: 'get_status'
    choices:
        - 'get_status'

author:
    - Abhijeet Kasurde (@Akasurde)
requirements:
    - "github3.py >= 1.0.0"
'''

RETURN = '''
get_status:
    description: State of the GitHub issue
    type: str
    returned: success
    sample: open, closed
'''

EXAMPLES = '''
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
            organization=dict(required=True),
            repo=dict(required=True),
            issue=dict(type='int', required=True),
            action=dict(choices=['get_status'], default='get_status'),
        ),
        supports_check_mode=True,
    )

    if not HAS_GITHUB_PACKAGE:
        module.fail_json(msg=missing_required_lib('github3.py >= 1.0.0'),
                         exception=GITHUB_IMP_ERR)

    try:
        current_version = tuple(map(int, github3.__version__.split(".")))
        if current_version < (1, 0, 0):
            raise ValueError
    except ValueError:
        module.fail_json(msg="Failed to parse github3.py version."
                             " Please make sure you have correct version install."
                             " Required is >= 1.0.0, got %s" % github3.__version__)

    organization = module.params['organization']
    repo = module.params['repo']
    issue = module.params['issue']
    action = module.params['action']

    result = dict()
    gh_obj = None
    not_found = False

    try:
        gh_obj = github3.issue(organization, repo, issue)
    except (github3.exceptions.NotFoundError, github3.exceptions.GitHubError, ValueError):
        not_found = True

    if gh_obj is None or not_found:
        module.fail_json(msg="Failed to get details about issue specified. "
                             "Please check organization [%s], repo [%s] and issue "
                             "details [%s] and try again." % (organization, repo, issue))

    if action == 'get_status' or action is None:
        if module.check_mode:
            result.update(changed=True)
        else:
            result.update(changed=True, issue_status=gh_obj.state)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
