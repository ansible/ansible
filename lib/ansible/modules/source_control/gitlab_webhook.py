#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018-2019, Raphaël Droz (raphael@droz.eu)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: gitlab_webhook
short_description: Creates, updates or deletes GitLab webhook
version_added: "2.8"
description:
  - When the webhook does not exists in this GitLab project, it will be created.
  - When the webhook does exists and C(state=absent), the webhook will be deleted.
  - When changes are made to the webhook, the webhook will be updated.
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
      - The GitLab id of the webhook
    default: null
  solo:
    description:
      - Defines how to proceed when hook_id is omitted
    type: bool
    default: yes
  hook_ssl_verify:
    description:
      - Enable SSL verification of webhook URL
    type: bool
    default: yes
  token:
    description:
      - Secret token usually used to validate GitLab HTTP requests
    default: null
  state:
    description:
      - create or delete webhook.
      - Possible values are present and absent.
    default: "present"
    choices: ["present", "absent"]
'''

EXAMPLES = '''
# Deletes a GitLab webhook specifying only its url
- name: delete GitLab webhook
  gitlab_webhook:
    api_url: https://gitlab.com
    api_token: foobar
    project: 123456
    url: http://dev.newapp.st/hook.php
    state: absent
  delegate_to: localhost

# Deletes a GitLab webhook specifying its hook_id (URL can be omitted)
- name: delete GitLab webhook
  gitlab_webhook:
    api_url: https://gitlab.com
    api_token: foobar
    project: my/proj
    hook_id: 1547318
    state: absent
  delegate_to: localhost

# Creates a GitLab webhook or alter it if one already exists
# for https://hook.me/app.php
- name: webhook for hook.me
  gitlab_webhook:
    api_url: https://gitorious.org
    api_username: foo
    api_password: bar
    project: my/app
    url: https://hook.me/app.php
    events: ['push', 'issues']
    solo: true
    state: present
  delegate_to: localhost

# Setting token implies tasks is always marked changed
- name: Create/edit webhook
  gitlab_webhook:
    api_url: https://git.sf.net
    api_username: foo
    api_password: bar
    project: my/app
    url: https://hook.me/auth/app.php
    events: ['push', 'issues']
    token: secr3t
    state: presentt
  delegate_to: localhost

- If a token is specified, webhook is always modified since API does not
  provide a way to know the value of the token store inside GitLab.
- Use token = '' to reset the value of the token for an existing webhook.
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
  description: A dict containing key/value pairs representing GitLab webhook
  returned: success
  type: dict
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


class GitLabWebhook(object):
    HOOK_EVENTS = ['push', 'issues', 'confidential_issues', 'merge_requests', 'tag_push', 'note', 'job', 'pipeline', 'wiki_page']

    def __init__(self, module, git):
        self._module = module

    def delete(self, project, local_webhook):
        if not self._module.check_mode:
            project.hooks.delete(local_webhook['hook_id'])

    def deleteByUrl(self, project, remote_webhooks, url):
        deleted = 0
        try:
            for wh in remote_webhooks:
                if wh.attributes['url'] == url:
                    if not self._module.check_mode:
                        project.hooks.delete(wh.attributes['id'])
                    deleted += 1
        except (gitlab.GitlabHttpError, gitlab.GitlabDeleteError) as e:
            self._module.fail_json(msg='Failed to delete 1 of %d webhooks' % len(remote_webhooks), exception=to_native(e))
        return deleted

    def update(self, project, local_webhook, remote_webhook):
        webhook_diff = False
        new_hook_attr = remote_webhook.attributes.copy()
        new_hook_attr.update(local_webhook)
        compare_on = ['url', 'events', 'token', 'enable_ssl_verification']
        webhook_diff = not self.equals(remote_webhook.attributes, new_hook_attr, compare_on)
        if webhook_diff:
            self.setattrs(remote_webhook, local_webhook)
            if not self._module.check_mode:
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

    def asApiObject(self, url, events, hook_id=None, token=None, enable_ssl_verification=True):
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
        obj['enable_ssl_verification'] = enable_ssl_verification
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
            api_url=dict(required=True),
            validate_certs=dict(required=False, default=True, type='bool'),
            api_username=dict(required=False, no_log=True),
            api_password=dict(required=False, no_log=True),
            api_token=dict(required=False, no_log=True),
            hook_id=dict(required=False, type='int'),
            solo=dict(required=False, default=True, type='bool'),
            project=dict(required=True),
            url=dict(required=False),
            events=dict(required=False, type='list', elements='str', default=['push'],
                        choices=['push', 'issues', 'confidential_issues', 'merge_requests', 'tag_push', 'note', 'job', 'pipeline', 'wiki_page']),
            hook_ssl_verify=dict(required=False, default='yes', type='bool'),
            token=dict(required=False, no_log=True),
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
            ['state', 'present', ['events']]
        ],
        supports_check_mode=True
    )

    if not HAS_GITLAB_PACKAGE:
        module.fail_json(msg=missing_required_lib("python-gitlab"), exception=GITLAB_IMP_ERR)

    api_url = module.params['api_url']
    validate_certs = module.params['validate_certs']
    api_username = module.params['api_username']
    api_password = module.params['api_password']
    api_token = module.params['api_token']
    hook_id = module.params['hook_id']
    solo = module.params['solo']
    project = module.params['project']
    url = module.params['url']
    events = module.params['events']
    enable_ssl_verification = module.params['hook_ssl_verify']
    token = module.params['token']
    state = module.params['state']

    if (state != 'absent' or not hook_id) and not url:
        module.fail_json(msg="url is required (except for removal via hook_id)")

    try:
        git = Gitlab(url=api_url, ssl_verify=validate_certs, email=api_username, password=api_password, private_token=api_token, api_version=4)
        # git.enable_debug() ?
        git.auth()
    except (gitlab.GitlabHttpError, gitlab.GitlabAuthenticationError) as e:
        module.fail_json(msg="Failed to connect to GitLab server", exception=to_native(e))

    try:
        project = git.projects.get(project)
    except gitlab.GitlabGetError as e:
        module.fail_json(msg='No such a project %s' % project, exception=to_native(e))

    HookHelper = GitLabWebhook(module, git)
    if hook_id:
        try:
            remote_webhook = project.hooks.get(hook_id)
            num_found = 1
        except gitlab.GitlabGetError as e:
            # * state=present, none found, hook_id  : error
            # * state=absent, none found, hook_id  : error
            # hook_id set, none found: error (whether state=present or absent)
            module.exit_json(changed=False, msg='No webhook match', details='No webhook %d' % hook_id, exception=to_native(e))
    else:
        all_remote_webhooks = project.hooks.list()
        remote_webhook = HookHelper.findByUrl(all_remote_webhooks, url)
        num_found = len(remote_webhook)

    local_webhook = HookHelper.asApiObject(url, events, hook_id, token, enable_ssl_verification)
    deleteByHookId = 'hook_id' in local_webhook and local_webhook['hook_id']

    if remote_webhook and state == "absent":
        if num_found <= 1:
            # * state=absent, 1 found, solo=yes : remove
            # * state=absent, 1 found, solo=no  : remove
            if deleteByHookId:
                try:
                    HookHelper.delete(project, local_webhook)
                except (gitlab.GitlabHttpError, gitlab.GitlabDeleteError) as e:
                    module.fail_json(msg='Failed to delete webhook %s' % hook_id, exception=to_native(e))
                else:
                    module.exit_json(changed=True, msg="Successfully deleted webhook %s" % url, webhook=remote_webhook)
            else:
                deleted = HookHelper.deleteByUrl(project, remote_webhook, local_webhook['url'])
                module.exit_json(changed=deleted > 0, msg="Successfully deleted %d webhooks" % deleted, webhook=remote_webhook[0].attributes)
        else:
            if not solo:
                # * state=absent, 2+ found, solo=no  : remove all
                if deleteByHookId:
                    try:
                        HookHelper.delete(project, local_webhook)
                    except (gitlab.GitlabHttpError, gitlab.GitlabDeleteError) as e:
                        module.fail_json(msg='Failed to delete webhook %s' % hook_id, exception=to_native(e))
                    else:
                        module.exit_json(changed=True, msg="Successfully deleted webhook %s" % url, webhook=remote_webhook)
                else:
                    deleted = HookHelper.deleteByUrl(project, remote_webhook, local_webhook['url'])
                    module.exit_json(changed=deleted > 0, msg="Successfully deleted %d webhooks" % deleted, webhook=remote_webhook[0].attributes)
            else:
                # * state=absent, 2+ found, solo=yes : error
                module.fail_json(msg='Multiple hooks match',
                                 details="solo=yes but %d webhooks match for url %s" % (num_found, url))

    elif state == "absent":
        # state=absent,  none found: error
        module.exit_json(changed=False, msg="No existing webhook for url %s" % url)
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
                remote_state = remote_webhook[0].attributes.copy()
                h = HookHelper.update(project, local_webhook, remote_webhook[0])
            except gitlab.GitlabUpdateError as e:
                module.fail_json(changed=False, msg='Could not update webhook %s' % url, exception=to_native(e))
            else:
                if not h:
                    module.exit_json(changed=False)
                diff = {'before': remote_state, 'after': h.attributes} if module._diff else None
                module.exit_json(changed=True, webhook=h.attributes, diff=diff, state='changed', msg='Successfully updated hook %s' % url)
        else:
            # Create
            # * state=present, none found : create
            try:
                h = False if module.check_mode else project.hooks.create(local_webhook)
            except gitlab.GitlabCreateError as e:
                module.fail_json(changed=False, msg='Could not create webhook %s' % url)
            else:
                diff = None
                if module._diff:
                    diff = {'before': {}, 'after': local_webhook if module.check_mode else project.hooks.get(h.attributes['id']).attributes}
                module.exit_json(changed=True, webhook=h.attributes if h else local_webhook, diff=diff, state='created',
                                 msg='Successfully created hook %s' % url)


if __name__ == '__main__':
    main()
