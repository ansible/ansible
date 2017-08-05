#!/usr/bin/python
# (c) 2017, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: github_issue
short_description: View GitHub issue.
description:
    - View GitHub issue for a given repository.
version_added: "2.4"
options:
  repo:
    description:
      - Name of repository from which issue needs to be retrieved.
    required: true
    default: none
  organization:
    description:
      - Name of the GitHub organization in which the repository is hosted.
    required: true
    default: none
  issue:
    description:
      - Issue number for which information is required.
    default: none
    required: true
  action:
    description:
        - Get various details about issue depending upon action specified.
    default: 'get_status'
    required: false
    choices:
        - ['get_status']

author:
    - Abhijeet Kasurde (@akasurde)
requirements:
    - "github3.py >= 1.0.0a4"
'''

RETURN = '''
get_status:
    description: State of the GitHub issue
    type: string
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


try:
    import github3
    HAS_GITHUB_PACKAGE = True
except ImportError:
    HAS_GITHUB_PACKAGE = False

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            organization=dict(required=True),
            repo=dict(required=True),
            issue=dict(required=True),
            action=dict(required=False, choices=['get_status']),
        ),
        supports_check_mode=True,
    )

    if not HAS_GITHUB_PACKAGE:
        module.fail_json(msg="Missing required github3 module. (check docs or "
                             "install with: pip install github3.py==1.0.0a4)")

    organization = module.params['organization']
    repo = module.params['repo']
    issue = module.params['issue']
    action = module.params['action']

    result = dict()

    gh_obj = github3.issue(organization, repo, issue)
    if isinstance(gh_obj, github3.null.NullObject):
        module.fail_json(msg="Failed to get details about issue specified. "
                             "Please check organization, repo and issue "
                             "details and try again.")

    if action == 'get_status' or action is None:
        if module.check_mode:
            result.update(changed=True)
        else:
            result.update(changed=True, issue_status=gh_obj.state)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
