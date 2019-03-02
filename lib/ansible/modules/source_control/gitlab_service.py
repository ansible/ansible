#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018-2019, Raphaël Droz <raphael@droz.eu>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: gitlab_service
short_description: Creates, updates or deletes GitLab services
version_added: "2.8"
description:
  - Setup or delete GitLab integration services.
author: "Raphaël Droz (@drzraf)"
requirements:
  - python >= 2.7
  - python-gitlab
extends_documentation_fragment:
  - auth_basic
options:
  api_token:
    description:
      - GitLab personal token for logging in (preferred method)
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
    default: yes
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
      - discord
      - drone-ci
      - emails-on-push
      - external-wiki
      - flowdock
      - github
      - hangouts-chat
      - irker
      - jenkins
      - jenkins-deprecated
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
      - youtrack
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
    api_url: https://gitlab.com
    api_token: foobar
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
    api_url: https://gitlab.com
    api_token: foobar
    project: foo/proj
    service: packagist
    events: ["push"]
    params:
      username: foo
      token: bar
      server: https://packagist.org
  delegate_to: localhost

- Idempotency is only partially provided since GitLab does
  not expose secret parameters like tokens or passwords.
  See U(https://gitlab.com/gitlab-org/gitlab-ce/issues/46313)
'''

RETURN = '''
---
diff:
  description: The differences about the given arguments.
  returned: success
  type: complex
  contains:
    before:
      description: The values before change
      type: dict
    after:
      description: The values after change
      type: dict
service:
  description: A dict containing key/value pairs representing GitLab service
  returned: success
  type: dict
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
  type: str
  sample: created
'''

import traceback
from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils._text import to_native

GITLAB_IMP_ERR = None
try:
    import gitlab
    from gitlab import Gitlab
    HAS_GITLAB_PACKAGE = True
except ImportError:
    GITLAB_IMP_ERR = traceback.format_exc()
    HAS_GITLAB_PACKAGE = False

# auto-generated 2019/02/28 from https://gitlab.com/gitlab-org/gitlab-ee/blob/2811250ba2c5637c328f77c318c995f7c0b59207/lib/api/services.rb
RAW_SERVICES_DEFINITIONS = {"asana":{"api_key":{"required":1}, "restrict_to_branch":{}, "_events":["push"]}, "assembla":{"token":{"required":1}, "subdomain":{}, "_events":["push"]}, "bamboo":{"bamboo_url":{"required":1}, "build_key":{"required":1}, "username":{"required":1}, "password":{"required":1}}, "bugzilla":{"new_issue_url":{"required":1}, "issues_url":{"required":1}, "project_url":{"required":1}, "description":{}, "title":{}}, "buildkite":{"token":{"required":1}, "project_url":{"required":1}, "enable_ssl_verification":{"type":"bool"}}, "campfire":{"token":{"required":1}, "subdomain":{}, "room":{}, "_events":["push"]}, "custom-issue-tracker":{"new_issue_url":{"required":1}, "issues_url":{"required":1}, "project_url":{"required":1}, "description":{}, "title":{}}, "discord":{"webhook":{"required":1}}, "drone-ci":{"token":{"required":1}, "drone_url":{"required":1}, "enable_ssl_verification":{"type":"bool"}, "_events":["push", "merge_request", "tag_push"]}, "emails-on-push":{"recipients":{"required":1}, "disable_diffs":{"type":"bool"}, "send_from_committer_email":{"type":"bool"}, "_events":["push", "tag_push"]}, "external-wiki":{"external_wiki_url":{"required":1}, "_events":[]}, "flowdock":{"token":{"required":1}, "_events":["push"]}, "hangouts-chat":{"webhook":{"required":1}, "push_events":{"type":"bool"}, "issues_events":{"type":"bool"}, "confidential_issues_events":{"type":"bool"}, "merge_requests_events":{"type":"bool"}, "note_events":{"type":"bool"}, "tag_push_events":{"type":"bool"}, "pipeline_events":{"type":"bool"}, "wiki_page_events":{"type":"bool"}}, "irker":{"recipients":{"required":1}, "default_irc_uri":{}, "server_host":{}, "server_port":{"type":"Integer"}, "colorize_messages":{"type":"bool"}, "_events":["push"]}, "jira":{"url":{"required":1}, "api_url":{}, "username":{"required":1}, "password":{"required":1}, "jira_issue_transition_id":{}, "_events":["commit", "merge_request"]}, "kubernetes":{"namespace":{"required":1}, "api_url":{"required":1}, "token":{"required":1}, "ca_pem":{}}, "mattermost-slash-commands":{"token":{"required":1}}, "slack-slash-commands":{"token":{"required":1}}, "packagist":{"username":{"required":1}, "token":{"required":1}, "server":{}, "_events":["push", "merge_request", "tag_push"]}, "pipelines-email":{"recipients":{"required":1}, "notify_only_broken_pipelines":{"type":"bool"}, "_events":["pipeline"]}, "pivotaltracker":{"token":{"required":1}, "restrict_to_branch":{}, "_events":["push"]}, "prometheus":{"api_url":{"required":1}}, "pushover":{"api_key":{"required":1}, "user_key":{"required":1}, "priority":{"required":1}, "device":{"required":1}, "sound":{"required":1}, "_events":["push"]}, "redmine":{"new_issue_url":{"required":1}, "project_url":{"required":1}, "issues_url":{"required":1}, "description":{}}, "youtrack":{"project_url":{"required":1}, "issues_url":{"required":1}, "description":{}}, "slack":{"webhook":{"required":1}, "username":{}, "channel":{}, "notify_only_broken_pipelines":{"type":"bool"}, "notify_only_default_branch":{"type":"bool"}, "push_channel":{}, "issue_channel":{}, "confidential_issue_channel":{}, "merge_request_channel":{}, "note_channel":{}, "tag_push_channel":{}, "pipeline_channel":{}, "wiki_page_channel":{}, "push_events":{"type":"bool"}, "issues_events":{"type":"bool"}, "confidential_issues_events":{"type":"bool"}, "merge_requests_events":{"type":"bool"}, "note_events":{"type":"bool"}, "tag_push_events":{"type":"bool"}, "pipeline_events":{"type":"bool"}, "wiki_page_events":{"type":"bool"}}, "microsoft-teams":{"webhook":{"required":1}}, "mattermost":{"webhook":{"required":1}, "username":{}, "channel":{}, "notify_only_broken_pipelines":{"type":"bool"}, "notify_only_default_branch":{"type":"bool"}, "push_channel":{}, "issue_channel":{}, "confidential_issue_channel":{}, "merge_request_channel":{}, "note_channel":{}, "tag_push_channel":{}, "pipeline_channel":{}, "wiki_page_channel":{}, "push_events":{"type":"bool"}, "issues_events":{"type":"bool"}, "confidential_issues_events":{"type":"bool"}, "merge_requests_events":{"type":"bool"}, "note_events":{"type":"bool"}, "tag_push_events":{"type":"bool"}, "pipeline_events":{"type":"bool"}, "wiki_page_events":{"type":"bool"}}, "teamcity":{"teamcity_url":{"required":1}, "build_type":{"required":1}, "username":{"required":1}, "password":{"required":1}}, "github":{"token":{"required":1}, "repository_url":{"required":1}}, "jenkins":{"jenkins_url":{"required":1}, "project_name":{"required":1}, "username":{}, "password":{}}, "jenkins-deprecated":{"project_url":{"required":1}, "pass_unstable":{"type":"bool"}, "multiproject_enabled":{"type":"bool"}}}


def init_definitions():
    for service_slug, params in RAW_SERVICES_DEFINITIONS.items():
        for name, definition in params.items():
            if 'type' in definition:
                definition['type'] = bool if definition['type'] == 'bool' else int if definition['type'] == 'int' else definition['type']
            if name in GitLabServices.credentialParams:
                definition['no_log'] = True
    return RAW_SERVICES_DEFINITIONS


class GitLabServices(object):
    HOOK_EVENTS = ['push', 'issues', 'confidential_issues', 'merge_requests', 'tag_push', 'note', 'confidential_note', 'job', 'pipeline', 'wiki_page']
    credentialParams = ['password', 'token', 'api_key']

    def __init__(self, module, git, name):
        self._module = module
        self.name = name

    # "create" can only happen once for this service during the life of the project)
    # merge new attributes in the object retrieved from the server
    def create(self, remote_service, active, params, events):
        local_service = self.asApiObject(active, params, events)
        for k, v in local_service.items():
            setattr(remote_service, k, v)
        if not self._module.check_mode:
            remote_service.save()
        return {'before': {}, 'after': str(remote_service.attributes)}

    def update(self, remote, active, params, events):
        diff = not self.equals(remote.attributes, active, params, events)
        if diff:
            # remote.active = active
            for k, v in self.expandEvents(events).items():
                setattr(remote, k, v)
            # when saving, params does directly in the request
            # (remember they get retrieved under the "property" key of the remote dict())
            for k, v in params.items():
                setattr(remote, k, v)
            if not self._module.check_mode:
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
        try:
            # See https://gitlab.com/gitlab-org/gitlab-ce/issues/58321 for why it's useful to
            # discard unsupported events before comparing
            supported_events = RAW_SERVICES_DEFINITIONS[self.name]['_events']
        except KeyError:
            supported_events = None
        return {value + '_events': bool(value in events) for value in self.HOOK_EVENTS if supported_events is None or value in supported_events}

    def eventsEqual(self, obj, events):
        return all((k in obj and obj[k] == v) for k, v in events.items())

    def hasCredentials(self, attr):
        return ('password' in attr and attr['password']) or ('token' in attr and attr['token']) or ('api_key' in attr and attr['api_key'])

    def equals(self, prev_attr, active, params, events):
        filtered_params = {k: v for k, v in params.items() if k not in self.credentialParams}
        if prev_attr['active'] != active:
            self._module.debug("active status differs")
            return False
        if self.hasCredentials(params):
            self._module.debug("has credentials: assuming difference")
            return False
        if not self.eventsEqual(prev_attr, self.expandEvents(events)):
            self._module.debug("events differs: %s != %s" % (prev_attr, events))
            return False
        if prev_attr['properties'] != filtered_params:
            self._module.debug("services attributes differs: %s != %s" % (prev_attr['properties'], filtered_params))
            return False
        return True

    def setattrs(self, obj, new_attr):
        for k, v in new_attr.items():
            setattr(obj, k, v)


def main():
    definitions = init_definitions()

    base_specs = dict(
        argument_spec=dict(
            api_url=dict(required=True),
            validate_certs=dict(required=False, default=True, type='bool'),
            api_username=dict(required=False, no_log=True),
            api_password=dict(required=False, no_log=True),
            api_token=dict(required=False, no_log=True),
            project=dict(required=True),
            service=dict(required=False, type='str', choices=list(definitions.keys())),
            active=dict(required=False, default=True, type='bool', choices=[True]),
            params=dict(required=False, type='dict'),
            events=dict(required=False, type='list', elements='str', default=GitLabServices.HOOK_EVENTS, choices=GitLabServices.HOOK_EVENTS),
            state=dict(default='present', choices=['present', 'absent']),
        ),
        mutually_exclusive=[
            ['api_username', 'api_token'],
            ['api_password', 'api_token']
        ],
        required_together=[
            ['api_username', 'api_password']
        ],
        required_one_of=[
            ['api_username', 'api_token']
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
        sub_arg_specs = {i: definitions[service][i] for i in definitions[service] if i != '_events'}
        base_specs['argument_spec']['params'] = dict(required=False, type='dict', options=sub_arg_specs)
        if '_events' in definitions[service]:
            base_specs['argument_spec']['events'] = dict(required=True, type='list', elements='str', choices=definitions[service]['_events'])
        module = AnsibleModule(**base_specs)
    else:
        module = stub_init

    if not HAS_GITLAB_PACKAGE:
        module.fail_json(msg=missing_required_lib("python-gitlab"), exception=GITLAB_IMP_ERR)

    api_url = module.params['api_url']
    validate_certs = module.params['validate_certs']
    api_username = module.params['api_username']
    api_password = module.params['api_password']
    api_token = module.params['api_token']
    project = module.params['project']
    active = True
    # active = module.params['active']
    params = module.params['params']
    events = module.params['events']

    try:
        git = Gitlab(url=api_url, ssl_verify=validate_certs, email=api_username, password=api_password, private_token=api_token, api_version=4)
        # git.enable_debug() ?
        git.auth()
    except (gitlab.GitlabHttpError, gitlab.GitlabAuthenticationError) as e:
        module.fail_json(msg='Failed to connect to GitLab server: %s' % to_native(e))

    try:
        project = git.projects.get(project)
    except gitlab.GitlabGetError as e:
        module.fail_json(msg='No such a project %s' % project, exception=to_native(e))

    try:
        remote_service = project.services.get(service)
        original_attributes = remote_service.attributes.copy()
    except gitlab.GitlabGetError as e:
        module.fail_json(msg='No such a service %s' % service, exception=to_native(e))

    ServicesHelper = GitLabServices(module, git, service)
    if state == 'absent':
        if not remote_service or not remote_service.created_at:
            module.exit_json(changed=False, service={}, msg='Service not found', details='Service %s not found' % service)
        else:
            try:
                if not module.check_mode:
                    remote_service.delete()
            except (gitlab.GitlabHttpError, gitlab.GitlabDeleteError) as e:
                module.fail_json(msg='Failed to remove service %s' % service, exception=to_native(e))
            else:
                module.exit_json(changed=True, service=remote_service.attributes, msg='Successfully deleted service %s' % service)

    else:
        if remote_service.created_at:
            # update
            try:
                h = ServicesHelper.update(remote_service, active, params, events)
            except gitlab.GitlabUpdateError as e:
                module.fail_json(changed=False, msg='Could not update service %s' % service, exception=to_native(e))
            else:
                diff = {'before': original_attributes, 'after': remote_service.attributes if module.check_mode else project.services.get(service).attributes} if module._diff else None
                if h:
                    module.exit_json(changed=True, service=remote_service.attributes, diff=diff, state='changed',
                                     msg='Successfully updated service %s' % service)
                else:
                    module.exit_json(changed=False)

        else:
            try:
                diff = ServicesHelper.create(remote_service, active, params, events)
            except (gitlab.GitlabCreateError, gitlab.GitlabUpdateError) as e:
                module.fail_json(changed=False, msg='Could not create service %s' % service, exception=to_native(e))
            else:
                module.exit_json(changed=True, service=remote_service.attributes, diff=diff, state='created',
                                 msg='Successfully created service %s' % service)


if __name__ == '__main__':
    main()
