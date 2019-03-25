#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Alejandro Guirao <lekumberri@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: taiga_issue
short_description: Creates/deletes an issue in a Taiga Project Management Platform
description:
  - Creates/deletes an issue in a Taiga Project Management Platform (U(https://taiga.io)).
  - An issue is identified by the combination of project, issue subject and issue type.
  - This module implements the creation or deletion of issues (not the update).
version_added: "2.0"
options:
  taiga_host:
    description:
      - The hostname of the Taiga instance.
    default: https://api.taiga.io
  project:
    description:
      - Name of the project containing the issue. Must exist previously.
    required: True
  subject:
    description:
      - The issue subject.
    required: True
  issue_type:
    description:
      - The issue type. Must exist previously.
    required: True
  priority:
    description:
      - The issue priority. Must exist previously.
    default: Normal
  status:
    description:
      - The issue status. Must exist previously.
    default: New
  severity:
    description:
      - The issue severity. Must exist previously.
    default: Normal
  description:
    description:
      - The issue description.
    default: ""
  attachment:
    description:
      - Path to a file to be attached to the issue.
  attachment_description:
    description:
      - A string describing the file to be attached to the issue.
    default: ""
  tags:
    description:
      - A lists of tags to be assigned to the issue.
    default: []
  state:
    description:
      - Whether the issue should be present or not.
    choices: ["present", "absent"]
    default: present
author: Alejandro Guirao (@lekum)
requirements: [python-taiga]
notes:
- The authentication is achieved either by the environment variable TAIGA_TOKEN or by the pair of environment variables TAIGA_USERNAME and TAIGA_PASSWORD
'''

EXAMPLES = '''
# Create an issue in the my hosted Taiga environment and attach an error log
- taiga_issue:
    taiga_host: https://mytaigahost.example.com
    project: myproject
    subject: An error has been found
    issue_type: Bug
    priority: High
    status: New
    severity: Important
    description: An error has been found. Please check the attached error log for details.
    attachment: /path/to/error.log
    attachment_description: Error log file
    tags:
      - Error
      - Needs manual check
    state: present

# Deletes the previously created issue
- taiga_issue:
    taiga_host: https://mytaigahost.example.com
    project: myproject
    subject: An error has been found
    issue_type: Bug
    state: absent
'''

RETURN = '''# '''
import traceback

from os import getenv
from os.path import isfile
from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils._text import to_native

TAIGA_IMP_ERR = None
try:
    from taiga import TaigaAPI
    from taiga.exceptions import TaigaException
    TAIGA_MODULE_IMPORTED = True
except ImportError:
    TAIGA_IMP_ERR = traceback.format_exc()
    TAIGA_MODULE_IMPORTED = False


def manage_issue(module, taiga_host, project_name, issue_subject, issue_priority,
                 issue_status, issue_type, issue_severity, issue_description,
                 issue_attachment, issue_attachment_description,
                 issue_tags, state, check_mode=False):
    """
    Method that creates/deletes issues depending whether they exist and the state desired

    The credentials should be passed via environment variables:
        - TAIGA_TOKEN
        - TAIGA_USERNAME and TAIGA_PASSWORD

    Returns a tuple with these elements:
        - A boolean representing the success of the operation
        - A descriptive message
        - A dict with the issue attributes, in case of issue creation, otherwise empty dict
    """

    changed = False

    try:
        token = getenv('TAIGA_TOKEN')
        if token:
            api = TaigaAPI(host=taiga_host, token=token)
        else:
            api = TaigaAPI(host=taiga_host)
            username = getenv('TAIGA_USERNAME')
            password = getenv('TAIGA_PASSWORD')
            if not any([username, password]):
                return (False, changed, "Missing credentials", {})
            api.auth(username=username, password=password)

        user_id = api.me().id
        project_list = filter(lambda x: x.name == project_name, api.projects.list(member=user_id))
        if len(project_list) != 1:
            return (False, changed, "Unable to find project %s" % project_name, {})
        project = project_list[0]
        project_id = project.id

        priority_list = filter(lambda x: x.name == issue_priority, api.priorities.list(project=project_id))
        if len(priority_list) != 1:
            return (False, changed, "Unable to find issue priority %s for project %s" % (issue_priority, project_name), {})
        priority_id = priority_list[0].id

        status_list = filter(lambda x: x.name == issue_status, api.issue_statuses.list(project=project_id))
        if len(status_list) != 1:
            return (False, changed, "Unable to find issue status %s for project %s" % (issue_status, project_name), {})
        status_id = status_list[0].id

        type_list = filter(lambda x: x.name == issue_type, project.list_issue_types())
        if len(type_list) != 1:
            return (False, changed, "Unable to find issue type %s for project %s" % (issue_type, project_name), {})
        type_id = type_list[0].id

        severity_list = filter(lambda x: x.name == issue_severity, project.list_severities())
        if len(severity_list) != 1:
            return (False, changed, "Unable to find severity %s for project %s" % (issue_severity, project_name), {})
        severity_id = severity_list[0].id

        issue = {
            "project": project_name,
            "subject": issue_subject,
            "priority": issue_priority,
            "status": issue_status,
            "type": issue_type,
            "severity": issue_severity,
            "description": issue_description,
            "tags": issue_tags,
        }

        # An issue is identified by the project_name, the issue_subject and the issue_type
        matching_issue_list = filter(lambda x: x.subject == issue_subject and x.type == type_id, project.list_issues())
        matching_issue_list_len = len(matching_issue_list)

        if matching_issue_list_len == 0:
            # The issue does not exist in the project
            if state == "present":
                # This implies a change
                changed = True
                if not check_mode:
                    # Create the issue
                    new_issue = project.add_issue(issue_subject, priority_id, status_id, type_id, severity_id, tags=issue_tags, description=issue_description)
                    if issue_attachment:
                        new_issue.attach(issue_attachment, description=issue_attachment_description)
                        issue["attachment"] = issue_attachment
                        issue["attachment_description"] = issue_attachment_description
                return (True, changed, "Issue created", issue)

            else:
                # If does not exist, do nothing
                return (True, changed, "Issue does not exist", {})

        elif matching_issue_list_len == 1:
            # The issue exists in the project
            if state == "absent":
                # This implies a change
                changed = True
                if not check_mode:
                    # Delete the issue
                    matching_issue_list[0].delete()
                return (True, changed, "Issue deleted", {})

            else:
                # Do nothing
                return (True, changed, "Issue already exists", {})

        else:
            # More than 1 matching issue
            return (False, changed, "More than one issue with subject %s in project %s" % (issue_subject, project_name), {})

    except TaigaException as exc:
        msg = "An exception happened: %s" % to_native(exc)
        return (False, changed, msg, {})


def main():
    module = AnsibleModule(
        argument_spec=dict(
            taiga_host=dict(required=False, default="https://api.taiga.io"),
            project=dict(required=True),
            subject=dict(required=True),
            issue_type=dict(required=True),
            priority=dict(required=False, default="Normal"),
            status=dict(required=False, default="New"),
            severity=dict(required=False, default="Normal"),
            description=dict(required=False, default=""),
            attachment=dict(required=False, default=None),
            attachment_description=dict(required=False, default=""),
            tags=dict(required=False, default=[], type='list'),
            state=dict(required=False, choices=['present', 'absent'],
                       default='present'),
        ),
        supports_check_mode=True
    )

    if not TAIGA_MODULE_IMPORTED:
        module.fail_json(msg=missing_required_lib("python-taiga"),
                         exception=TAIGA_IMP_ERR)

    taiga_host = module.params['taiga_host']
    project_name = module.params['project']
    issue_subject = module.params['subject']
    issue_priority = module.params['priority']
    issue_status = module.params['status']
    issue_type = module.params['issue_type']
    issue_severity = module.params['severity']
    issue_description = module.params['description']
    issue_attachment = module.params['attachment']
    issue_attachment_description = module.params['attachment_description']
    if issue_attachment:
        if not isfile(issue_attachment):
            msg = "%s is not a file" % issue_attachment
            module.fail_json(msg=msg)
    issue_tags = module.params['tags']
    state = module.params['state']

    return_status, changed, msg, issue_attr_dict = manage_issue(
        module,
        taiga_host,
        project_name,
        issue_subject,
        issue_priority,
        issue_status,
        issue_type,
        issue_severity,
        issue_description,
        issue_attachment,
        issue_attachment_description,
        issue_tags,
        state,
        check_mode=module.check_mode
    )
    if return_status:
        if len(issue_attr_dict) > 0:
            module.exit_json(changed=changed, msg=msg, issue=issue_attr_dict)
        else:
            module.exit_json(changed=changed, msg=msg)
    else:
        module.fail_json(msg=msg)


if __name__ == '__main__':
    main()
