#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Raphaël Droz <raphael@droz.eu>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: gitlab_service
short_description: Creates, updates or deletes Gitlab services
version_added: "2.6"
description:
  - Setup or delete Gitlab integration services.
author: "Raphaël Droz (@drzraf)"
requirements:
  - python-gitlab
options:
  server_url:
    description:
      - Url of Gitlab server, with protocol (http or https).
    required: true
  validate_certs:
    description:
      - When using https if SSL certificate needs to be verified.
    type: bool
    default: 'yes'
  login_user:
    description:
      - Gitlab user name
    default: null
  login_password:
    description:
      - Gitlab password for login_user
    default: null
  login_token:
    description:
      - Gitlab personal token for logging in (preferred method)
    default: null
  project:
    description:
      - The ID or path of the project (urlencoded or not)
    required: true
    default: null
  active:
    description:
      - Not yet supported (U(https://gitlab.com/gitlab-org/gitlab-ce/issues/41113))
    type: bool
    default: 'yes'
  service:
    description:
      - The service
    required: true
    choices:
      - asana
      - assembla
      - bamboo
      - bugzilla
      - buildkite
      - campfire
      - custom-issue-tracker
      - drone-ci
      - emails-on-push
      - external-wiki
      - flowdock
      - gemnasium
      - hipchat
      - irker
      - jira
      - kubernetes
      - mattermost
      - mattermost-slash-commands
      - microsoft-teams
      - packagist
      - pipelines-email
      - pivotaltracker
      - prometheus
      - pushover
      - redmine
      - slack
      - slack-slash-commands
      - teamcity
  params:
    description:
      - The description of the service, see documentation U(https://docs.gitlab.com/ee/api/services.html)
  events:
    description:
      - The events that trigger the service (required state is present)
    choices: ["push", "issues", "confidential_issues", "merge_requests", "tag_push", "note", "confidential_note", "job", "pipeline", "wiki_page"]
    default: ["push", "issues", "confidential_issues", "merge_requests", "tag_push", "note", "confidential_note", "job", "pipeline", "wiki_page"]
  state:
    description:
      - Create or delete a service.
      - Possible values are present and absent.
    default: "present"
    choices: ["present", "absent"]
'''

EXAMPLES = '''
# Setup email on push for this project
- name: emails me on push
  gitlab_service:
    server_url: https://gitlab.com
    login_token: foobar
    project: 123456
    service: emails-on-push
    params:
      recipients: foo@example.com
      disable_diffs: true
    state: present
  delegate_to: localhost

# This will always be set to change because a non-null token is mandatory
- name: trigger packagist update on push events (only)
  gitlab_service:
    server_url: https://gitlab.com
    login_token: foobar
    project: foo/proj
    service: packagist
    events: ["push"]
    params:
      username: foo
      token: bar
      server: https://packagist.org
  delegate_to: localhost

- Idempotency is only partially provided since Gitlab does
  not expose secret params like tokens or password.
  See U(https://gitlab.com/gitlab-org/gitlab-ce/issues/46313)
'''

RETURN = '''
---
service:
  description: A dict containing key/value pairs representing Gitlab service
  returned: success
  type: dictionary
  sample:
    id: 40812345
    push_events: true
    issues_events: true
    confidential_issues_events: true
    merge_requests_events: true
    tag_push_events: true
    note_events: true
    confidential_note_events: true
    job_events: true
    pipeline_events: true
    wiki_page_events: true
    recipients: me@example.com
    disable_diffs: null
    send_from_committer_email: null
    title: Emails on push
    created_at: '2018-05-13T03:08:07.943Z'
    updated_at: '2018-05-13T03:09:17.651Z'
    active: true
    properties:
      send_from_committer_email: null
      disable_diffs: null
      recipients: me@example.com
    project_id: 1234567
state:
  description: A string indicating whether the service was "created" or "changed"
  returned: success
  type: string
  sample: created
'''

try:
    import gitlab
    from gitlab import Gitlab
    HAS_GITLAB_PACKAGE = True
except ImportError:
    HAS_GITLAB_PACKAGE = False

import json
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

# auto-generated 2018/05/12 from https://gitlab.com/gitlab-org/gitlab-ee/blob/f850b1bdb74de78875a49126e0401cc975fda32a/lib/api/services.rb
RAW_SERVICES_DEFINITIONS = '''
{"asana":{"api_key":{"required":true},"restrict_to_branch":{}},"assembla":{"token":{"required":true},"subdomain":{}},"bamboo":{"bamboo_url":{"required":true},"build_key":{"required":true},"username":{"required":true},"password":{"required":true}},"bugzilla":{"new_issue_url":{"required":true},"issues_url":{"required":true},"project_url":{"required":true},"description":{},"title":{}},"buildkite":{"token":{"required":true},"project_url":{"required":true},"enable_ssl_verification":{"type":"bool"}},"campfire":{"token":{"required":true},"subdomain":{},"room":{}},"custom-issue-tracker":{"new_issue_url":{"required":true},"issues_url":{"required":true},"project_url":{"required":true},"description":{},"title":{}},"drone-ci":{"token":{"required":true},"drone_url":{"required":true},"enable_ssl_verification":{"type":"bool"}},"emails-on-push":{"recipients":{"required":true},"disable_diffs":{"type":"bool"},"send_from_committer_email":{"type":"bool"}},"external-wiki":{"external_wiki_url":{"required":true}},"flowdock":{"token":{"required":true}},"gemnasium":{"api_key":{"required":true},"token":{"required":true}},"hipchat":{"token":{"required":true},"room":{},"color":{},"notify":{"type":"bool"},"api_version":{},"server":{}},"irker":{"recipients":{"required":true},"default_irc_uri":{},"server_host":{},"server_port":{"type":"Integer"},"colorize_messages":{"type":"bool"}},"jira":{"url":{"required":true},"api_url":{},"username":{"required":true},"password":{"required":true},"jira_issue_transition_id":{"type":"Integer"}},"kubernetes":{"namespace":{"required":true},"api_url":{"required":true},"token":{"required":true},"ca_pem":{}},"mattermost-slash-commands":{"token":{"required":true}},"slack-slash-commands":{"token":{"required":true}},"packagist":{"username":{"required":true},"token":{"required":true},"server":{}},"pipelines-email":{"recipients":{"required":true},"notify_only_broken_pipelines":{"type":"bool"}},"pivotaltracker":{"token":{"required":true},"restrict_to_branch":{}},"prometheus":{"api_url":{"required":true}},"pushover":{"api_key":{"required":true},"user_key":{"required":true},"priority":{"required":true},"device":{"required":true},"sound":{"required":true}},"redmine":{"new_issue_url":{"required":true},"project_url":{"required":true},"issues_url":{"required":true},"description":{}},"slack":{"webhook":{"required":true},"username":{},"channel":{},"notify_only_broken_pipelines":{"type":"bool"},"notify_only_default_branch":{"type":"bool"},"push_channel":{},"issue_channel":{},"confidential_issue_channel":{},"merge_request_channel":{},"note_channel":{},"tag_push_channel":{},"pipeline_channel":{},"wiki_page_channel":{},"push_events":{"type":"bool"},"issues_events":{"type":"bool"},"confidential_issues_events":{"type":"bool"},"merge_requests_events":{"type":"bool"},"note_events":{"type":"bool"},"tag_push_events":{"type":"bool"},"pipeline_events":{"type":"bool"},"wiki_page_events":{"type":"bool"}},"microsoft-teams":{"webhook":{"required":true}},"mattermost":{"webhook":{"required":true},"username":{},"channel":{},"notify_only_broken_pipelines":{"type":"bool"},"notify_only_default_branch":{"type":"bool"},"push_channel":{},"issue_channel":{},"confidential_issue_channel":{},"merge_request_channel":{},"note_channel":{},"tag_push_channel":{},"pipeline_channel":{},"wiki_page_channel":{},"push_events":{"type":"bool"},"issues_events":{"type":"bool"},"confidential_issues_events":{"type":"bool"},"merge_requests_events":{"type":"bool"},"note_events":{"type":"bool"},"tag_push_events":{"type":"bool"},"pipeline_events":{"type":"bool"},"wiki_page_events":{"type":"bool"}},"teamcity":{"teamcity_url":{"required":true},"build_type":{"required":true},"username":{"required":true},"password":{"required":true}}}
'''


def init_definitions():
    sd = json.loads(RAW_SERVICES_DEFINITIONS)
    for service_slug, params in sd.items():
        for name, definition in params.items():
            if 'type' in definition:
                definition['type'] = bool if definition['type'] == 'bool' else int if definition['type'] == 'int' else definition['type']
            if name in GitLabServices.credentialParams:
                definition['no_log'] = True
    return sd


class GitLabServices(object):
    HOOK_EVENTS = ['push', 'issues', 'confidential_issues', 'merge_requests', 'tag_push', 'note', 'confidential_note', 'job', 'pipeline', 'wiki_page']
    credentialParams = ['password', 'token', 'api_key']

    def __init__(self, module, git):
        self._module = module

    def update(self, project, remote, active, params, events):
        diff = not self.equals(remote.attributes, active, params, events)
        if diff:
            # remote.active = active
            for k, v in self.expandEvents(events).items():
                setattr(remote, k, v)
            # when saving, params does directly in the request
            # (remember they get retrieved under the "property" key of the remote dict())
            for k, v in params.items():
                setattr(remote, k, v)
            if self._module.check_mode:
                self._module.exit_json(changed=True)
            remote.save()
            return remote
        else:
            return False

    def asApiObject(self, active, params, events):
        obj = {'active': active}
        obj.update(self.expandEvents(events))
        obj.update(params)
        return obj

    def expandEvents(self, events):
        # python >= 2.7: return {value + '_events': bool(value in events) for value in self.HOOK_EVENTS}
        v = {}
        for value in self.HOOK_EVENTS:
            setattr(v, value + '_events', bool(value in events))
        return v

    def eventsEqual(self, obj, events):
        return all((k in obj and obj[k] == v) for k, v in events.items())

    def hasCredentials(self, attr):
        return ('password' in attr and attr['password']) or ('token' in attr and attr['token']) or ('api_key' in attr and attr['api_key'])

    def equals(self, prev_attr, active, params, events):
        # python >= 2.7: filtered_params = {k: v for k, v in params.items() if k not in self.credentialParams}
        filtered_params = {}
        for k, v in params.items():
            if k not in self.credentialParams:
                setattr(filtered_params, k, v)
        # ToDo: this is not (yet?) supported by Gitlab
        # if prev_attr['active'] != active:
        # return False
        if self.hasCredentials(params):
            return False
        if not self.eventsEqual(prev_attr, self.expandEvents(events)):
            return False
        return prev_attr['properties'] == filtered_params

    def setattrs(self, obj, new_attr):
        for k, v in new_attr.items():
            setattr(obj, k, v)


def main():
    definitions = init_definitions()

    base_specs = dict(
        argument_spec=dict(
            server_url=dict(required=True),
            validate_certs=dict(required=False, default=True, type='bool'),
            login_user=dict(required=False, no_log=True),
            login_password=dict(required=False, no_log=True),
            login_token=dict(required=False, no_log=True),
            project=dict(required=True),
            service=dict(required=False, type='str', choices=list(definitions.keys())),
            active=dict(required=False, default=True, type='bool'),
            params=dict(required=False, type='dict'),
            events=dict(required=False, type='list', elements='str', default=GitLabServices.HOOK_EVENTS, choices=GitLabServices.HOOK_EVENTS),
            state=dict(default='present', choices=['present', 'absent']),
        ),
        mutually_exclusive=[
            ['login_user', 'login_token'],
            ['login_password', 'login_token']
        ],
        required_together=[
            ['login_user', 'login_password']
        ],
        required_one_of=[
            ['login_user', 'login_token']
        ],
        required_if=[
            ['state', 'present', ['params']]
        ],
        supports_check_mode=True
    )

    stub_init = AnsibleModule(**base_specs)
    service = stub_init.params['service']
    state = stub_init.params['state']
    if state == 'present':
        # since we know the service (which has been validated), recreate a module_specs to validate suboptions
        base_specs['argument_spec']['params'] = dict(required=False, type='dict', options=definitions[service])
        module = AnsibleModule(**base_specs)
    else:
        module = stub_init

    if not HAS_GITLAB_PACKAGE:
        module.fail_json(msg='Missing required gitlab module (check docs or install with: pip install python-gitlab')

    server_url = module.params['server_url']
    validate_certs = module.params['validate_certs']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    login_token = module.params['login_token']
    project = module.params['project']
    active = True
    # active = module.params['active']
    params = module.params['params']
    events = module.params['events']

    try:
        git = Gitlab(url=server_url, ssl_verify=validate_certs, email=login_user, password=login_password, private_token=login_token, api_version=4)
        # git.enable_debug() ?
        git.auth()
        project = git.projects.get(project)
    except (gitlab.GitlabHttpError, gitlab.GitlabAuthenticationError, gitlab.GitlabGetError) as e:
        module.fail_json(msg='Failed to connect to Gitlab server: %s' % to_native(e))

    try:
        remote_service = project.services.get(service)
    except gitlab.GitlabGetError as e:
        module.fail_json(msg='No such a service %s' % service, exception=to_native(e))

    ServicesHelper = GitLabServices(module, git)
    if state == 'absent':
        if not remote_service or not remote_service.created_at:
            module.exit_json(changed=False, msg='Service not found', details='Service %s not found' % service)
        else:
            if module.check_mode:
                module.exit_json(changed=True)
            try:
                remote_service.delete()
            except (gitlab.GitlabHttpError, gitlab.GitlabDeleteError) as e:
                module.fail_json(msg='Failed to remove service %s' % service, exception=to_native(e))
            else:
                module.exit_json(changed=True, result='Successfully deleted service %s' % service)

    else:
        if remote_service.created_at:
            # update
            try:
                diff = {'before': str(remote_service.attributes)}
                h = ServicesHelper.update(project, remote_service, active, params, events)
                # if diff: fetch again
                # diff['after'] = str(remote_service.attributes)
            except gitlab.GitlabUpdateError as e:
                module.fail_json(changed=False, msg='Could not update service %s' % service, exception=to_native(e))
            else:
                if h:
                    module.exit_json(changed=True, service=remote_service.attributes, diff=diff, state='changed', result='Successfully updated service %s' % service)
                else:
                    module.exit_json(changed=False)

        else:
            # create (could only happen once for this service during the life of the project)
            # merge new attributes in the object retrieved from the server
            local_service = ServicesHelper.asApiObject(active, params, events)
            for k, v in local_service.items():
                setattr(remote_service, k, v)
            if module.check_mode:
                module.exit_json(changed=True)
            try:
                remote_service.save()
                diff = {'before': {}, 'after': str(remote_service.attributes)}
            except (gitlab.GitlabCreateError, gitlab.GitlabUpdateError) as e:
                module.fail_json(changed=False, msg='Could not create service %s' % service, exception=to_native(e))
            else:
                module.exit_json(changed=True, service=remote_service.attributes, diff=diff, state='created',
                                 result='Successfully created service %s' % service)


if __name__ == '__main__':
    main()
