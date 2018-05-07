#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Raphaël Droz (raphael@droz.eu)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: gitlab_webhook
short_description: Creates, updates or deletes Gitlab webhook
version_added: "2.6"
description:
  - When the webhook does not exists in this Gitlab project, it will be created.
  - When the webhook does exists and state=absent, the webhook will be deleted.
  - When changes are made to the webhook, the webhook will be updated.
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
  url:
    description:
      - The URL for that webhook
    default: null
  events:
    description:
      - The events that trigger the webhook (required state is present)
    choices: ["push", "issues", "confidential_issues", "merge_requests", "tag_push", "note", "job", "pipeline", "wiki_page"]
    default: ["push"]
  hook_id:
    description:
      - The Gitlab id of the webhook
    default: null
  solo:
    description:
      - Defines how to proceed when hook_id is omitted
    type: bool
    default: 'yes'
  enable_ssl_verification:
    description:
      - Enable SSL verification of webhook URL
    type: bool
    default: 'yes'
  token:
    description:
      - Secret token usually used to validate Gitlab HTTP requests
    default: null
  state:
    description:
      - create or delete webhook.
      - Possible values are present and absent.
    default: "present"
    choices: ["present", "absent"]
'''

EXAMPLES = '''
# Deletes a Gitlab webhook specifying only its url
- name: delete Gitlab webhook
  gitlab_webhook:
    server_url: https://gitlab.com
    login_token: foobar
    project: 123456
    url: http://dev.newapp.st/hook.php
    state: absent
  delegate_to: localhost

# Deletes a Gitlab webhook specifying its hook_id (URL can be omitted)
- name: delete Gitlab webhook
  gitlab_webhook:
    server_url: https://gitlab.com
    login_token: foobar
    project: my/proj
    hook_id: 1547318
    state: absent
  delegate_to: localhost

# Creates a Gitlab webhook or alter it if one already exists
# for https://hook.me/app.php
- name: webhook for hook.me
  gitlab_webhook:
    server_url: https://gitorious.org
    login_user: foo
    login_password: bar
    project: my/app
    url: https://hook.me/app.php
    events: ['push', 'issues']
    solo: true
    state: present
  delegate_to: localhost

# Setting token implies tasks is always marked changed
- name: Create/edit webhook
  gitlab_webhook:
    server_url: https://git.sf.net
    login_user: foo
    login_password: bar
    project: my/app
    url: https://hook.me/auth/app.php
    events: ['push', 'issues']
    token: secr3t
    state: presentt
  delegate_to: localhost

- If a token is specified, webhook is always modified since API does not
  provide a way to know current token
- To forcefully remove the value of token for an already existing webhook,
  set it to the empty string.
- For convenience, webhook's URL may be used as the unique key for webhook
  edition/deletion instead of providing the hook_id.
  The "solo" attribute can be used to handle cases where various hooks are
  defined for the same URL.
  * state=absent,  none found                        error
  * state=absent,     1 found, solo=yes              remove
  * state=absent,     1 found, solo=no               remove
  * state=absent,    2+ found, solo=yes              error
  * state=absent,    2+ found, solo=no               remove all
  * state=present, none found                        create
  * state=present,    1 found, solo=yes              edit
  * state=present,    1 found, solo=no               edit
  * state=present,   2+ found, solo=yes              error
  * state=present,   2+ found, solo=no, no hook_id   error
  * state=present, none found, hook_id               error
  * state=present,    1 found, hook_id               edit
  See https://gitlab.com/gitlab-org/gitlab-ce/issues/39864
- See https://gitlab.com/gitlab-org/gitlab-ce/merge_requests/7220 about
  token being a write-only attribute
- See https://docs.gitlab.com/ce/api/projects.html#list-project-hooks
'''

RETURN = '''
---
webhook:
  description: A dict containing key/value pairs representing Gitlab webhook
  returned: success
  type: dictionary
  sample:
    id: 298159
    url: https://foo.bar/hook.php
    created_at: 2018-03-09T13:16:22.000Z
    push_events: true
    tag_push_events: false
    merge_requests_events: false
    repository_update_events: false
    enable_ssl_verification: true
    project_id: 5617915
    issues_events: false
    confidential_issues_events: false
    note_events: false
    confidential_note_events: null
    pipeline_events: false
    wiki_page_events: false
    job_events: false
state:
  description: A string indicating whether the hook was "created" or "changed"
  returned: success
  type: string
  sample: created
'''

try:
    from gitlab import Gitlab
    HAS_GITLAB_PACKAGE = True
except:
    HAS_GITLAB_PACKAGE = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


class GitLabWebhook(object):
    HOOK_EVENTS = ['push', 'issues', 'confidential_issues', 'merge_requests', 'tag_push', 'note', 'job', 'pipeline', 'wiki_page']

    def __init__(self, module, git):
        self._module = module

    def create(self, project, local_webhook, combined_events):
        if self._module.check_mode:
            self._module.exit_json(changed=True)
        return project.hooks.create(local_webhook)

    def delete(self, project, remote_webhook, local_webhook):
        if self._module.check_mode:
            self._module.exit_json(changed=True)
        if 'hook_id' in local_webhook and local_webhook['hook_id']:
            return project.hooks.delete(local_webhook['hook_id'])
        else:
            return self.deleteByUrl(project, remote_webhook, local_webhook['url'])

    def deleteByUrl(self, project, remote_webhooks, url):
        deleted = []
        for wh in remote_webhooks:
            if wh.attributes['url'] == url:
                deleted.append(project.hooks.delete(wh.attributes['id']))
        return deleted

    def update(self, project, local_webhook, remote_webhook):
        webhook_diff = False
        new_hook_attr = remote_webhook.attributes.copy()
        new_hook_attr.update(local_webhook)
        compare_on = ['url', 'events', 'token']
        webhook_diff = not self.equals(remote_webhook.attributes, new_hook_attr, compare_on)
        if webhook_diff:
            self.setattrs(remote_webhook, local_webhook)
            if self._module.check_mode:
                self._module.exit_json(changed=True)

            remote_webhook.save()
            return remote_webhook
        else:
            return False

    def findByUrl(self, remote_webhooks, url):
        found = []
        for wh in remote_webhooks:
            if wh.attributes['url'] == url:
                found.append(wh)
        return found

    def asApiObject(self, url, events, hook_id=None, token=None):
        obj = {
            'url': url,
            'push_events': bool('push' in events) and len(events) > 0,
        }
        for value in self.HOOK_EVENTS:
            if value == 'push':
                continue
            obj[value + '_events'] = bool(value in events)
        if hook_id:
            obj['hook_id'] = hook_id
        if token is not None:
            obj['token'] = token
        return obj

    # ToDo: API does not provide current token of a given webhook
    # https://gitlab.com/gitlab-org/gitlab-ce/merge_requests/7220
    def equals(self, prev_attr, new_attr, attributes):
        for attr in attributes:
            if attr == 'events':
                for event in self.HOOK_EVENTS:
                    if bool(prev_attr[event + '_events']) != bool(new_attr[event + '_events']):
                        return False
            elif attr == 'token':
                if 'token' in new_attr and new_attr['token'] is not None:
                    return False
                else:
                    continue
            elif prev_attr[attr] != new_attr[attr]:
                return False
        return True

    def setattrs(self, obj, new_attr):
        for k, v in new_attr.items():
            setattr(obj, k, v)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(required=True),
            validate_certs=dict(required=False, default=True, type='bool'),
            login_user=dict(required=False, no_log=True),
            login_password=dict(required=False, no_log=True),
            login_token=dict(required=False, no_log=True),
            hook_id=dict(required=False, type='int'),
            solo=dict(required=False, default=True, type='bool'),
            project=dict(required=True),
            url=dict(required=False),
            events=dict(required=False, type='list', elements='str', default=['push'],
                        choices=['push', 'issues', 'confidential_issues', 'merge_requests', 'tag_push', 'note', 'job', 'pipeline', 'wiki_page']),
            enable_ssl_verification=dict(required=False, default='yes', type='bool'),
            token=dict(required=False, no_log=True),
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
            ["state", "present", ["events"]]
        ],
        supports_check_mode=True
    )

    if not HAS_GITLAB_PACKAGE:
        module.fail_json(msg="Missing required gitlab module (check docs or install with: pip install python-gitlab")

    server_url = module.params['server_url']
    validate_certs = module.params['validate_certs']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    login_token = module.params['login_token']
    hook_id = module.params['hook_id']
    solo = module.params['solo']
    project = module.params['project']
    url = module.params['url']
    events = module.params['events']
    enable_ssl_verification = module.params['enable_ssl_verification']
    token = module.params['token']
    state = module.params['state']

    if (state != 'absent' or not hook_id) and not url:
        module.fail_json(msg="url is required (except for removal via hook_id)")

    try:
        git = Gitlab(url=server_url, ssl_verify=validate_certs, email=login_user, password=login_password, private_token=login_token, api_version=4)
        git.auth()
    except Exception as e:
        module.fail_json(msg="Failed to connect to Gitlab server: %s " % to_native(e))

    # Validate if project exists and take action based on "state"
    HookHelper = GitLabWebhook(module, git)

    # user = git.user
    project = git.projects.get(project)
    if hook_id:
        remote_webhook = project.hooks.get(hook_id)
        if not remote_webhook:
            # * state=present, none found, hook_id  : error
            # * state=absent, none found, hook_id  : error
            # hook_id set, none found: error (whether state=present or absent)
            module.exit_json(changed=False, msg='No webhook match', details='Webhook does not exists for this id %d' % hook_id)
        num_found = 1
    else:
        all_remote_webhooks = project.hooks.list()
        remote_webhook = HookHelper.findByUrl(all_remote_webhooks, url)
        num_found = len(remote_webhook)

    local_webhook = HookHelper.asApiObject(url, events, hook_id, token)
    if remote_webhook and state == "absent":
        if num_found <= 1:
            # * state=absent, 1 found, solo=yes : remove
            # * state=absent, 1 found, solo=no  : remove
            h = HookHelper.delete(project, remote_webhook, local_webhook)
            module.exit_json(changed=True, result="Successfully deleted webhook %s" % url, webhook=h)
        else:
            if not solo:
                # * state=absent, 2+ found, solo=no  : remove all
                deleted = HookHelper.delete(project, remote_webhook, local_webhook)
                module.exit_json(changed=len(deleted) > 0, result="Successfully deleted %d webhooks" % len(deleted))
            else:
                # * state=absent, 2+ found, solo=yes : error
                module.fail_json(msg='Multiple hooks match',
                                 details="solo=yes but %d webhooks match for url %s" % (num_found, url))

    elif state == "absent":
        # state=absent,  none found: error
        module.exit_json(changed=False, result="Webhook does not exists for this url")
    else:
        # state == "present"
        if remote_webhook and num_found > 1:
            if not solo and not hook_id:
                # * state=present, 2+ found, solo=no, no hook_id : error
                # (but matching heuristic could be further improved)
                module.fail_json(msg='Multiple webhooks match, specify <hook_id>',
                                 details="%d webhooks match but no hook_id were provided" % num_found)
            elif solo:
                # * state=present, 2+ found, solo=yes : error
                module.fail_json(msg='More than one webhooks match but only one was expected',
                                 details="%d webhooks match but solo=yes" % num_found)
            else:
                module.fail_json(msg='unexpected error')

        if num_found == 1:
            # Edit, no confusion
            # * state=present, 1 found, solo=yes : edit
            # * state=present, 1 found, solo=no  : edit
            # * state=present, 1 found, hook_id  : edit
            try:
                diff = {'before': str(remote_webhook[0].attributes)}
                h = HookHelper.update(project, local_webhook, remote_webhook[0])
                diff['after'] = str(h)
            except:
                module.fail_json(changed=False, msg='Could not update webhook %s' % url)
            else:
                if h:
                    module.exit_json(changed=True, webhook=h.attributes, diff=diff, state='changed', result='Successfully updated hook %s' % url)
                else:
                    module.exit_json(changed=False)

        else:
            # Create
            # * state=present, none found : create
            try:
                h = HookHelper.create(project, local_webhook, events)
                diff = {'before': {}, 'after': str(h)}
            except:
                module.fail_json(changed=False, msg='Could not create webhook %s' % url)
            else:
                module.exit_json(changed=True, webhook=h.attributes, diff=diff, state='created', result='Successfully created hook %s' % url)


if __name__ == '__main__':
    main()
