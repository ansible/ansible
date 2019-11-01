#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Timo Funke <timoses@msn.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''

module: pulp3_remote

short_description: Manage Pulp3 Remotes

version_added: "2.10"

author:
  - Timo Funke (@timoses)

description:
  - Supports CRUD operations against Pulp3 Remotes.
  - Enables synchronization with Pulp3 repositories.

extends_documentation_fragment:
  - url
  - pulp3
  - pulp3.named
  - pulp3.pulp_plugin

options:
  state:
    description:
    - Whether the remote should exist or not.
    choices:
    - present
    - absent
    default: present
    type: str
  repositories:
    description:
    - List of repository names.
    - If I(sync) is true, this remote will be synced into the listed repositories.
    type: list
  sync:
    description:
    - Whether to synchronize into I(repositories).
    type: bool
    default: false
  remote_url:
    description:
    - The URL of an external content source.
    type: str
    required: true
  proxy_url:
    description:
    - The proxy URL. Format is C(scheme://user:password@host:port).
    type: str
  ssl_validation:
    description:
    - If True, SSL peer validation must be performed.
    default: true
    type: bool
  upstream_name:
    description:
    - Name of the upstream repository.
    - Required when C(pulp_plugin=docker).
    type: str


requirements:
  - "python >= 2.7"
  - "pulp-<pulp_plugin>-client"
'''

EXAMPLES = '''
- name: Create remote without sync
  pulp3_remote:
    name: remote_not_synced
    remote_url: https://repos.fedorapeople.org/pulp/pulp/demo_repos/test_file_repo/PULP_MANIFEST

- name: Create a repository named 'foo'
  pulp3_repository:
    name: foo

- name: Create a file remote and sync to repository 'foo'
  pulp3_remote:
    name: file_remote
    remote_url: https://repos.fedorapeople.org/pulp/pulp/demo_repos/test_file_repo/PULP_MANIFEST
    repositories: foo
    sync: yes
'''

RETURN = '''
sync_tasks:
  description: "A list of { 'repository': '<repository_name>', 'task_href': '<task_pulp_href>' }"
  returned: when sync
  type: list
  sample: "{ 'repository': 'repository_name', 'task_href': '/pulp/api/v3/tasks/d82ff00f-8e40-4935-80a9-a598baa7a2d8/' }"
'''

from ansible.module_utils.pulp3 import PulpPluginAnsibleModule, load_pulp_plugin_api, REMOTE_API, get_repo


PULP_API_DATA = {
    'name': 'name',
    'url': 'remote_url',
    'upstream_name': 'upstream_name',
    'proxy_url': 'proxy_url',
    'ssl_validation': 'ssl_validation'
}

PULP_REMOTE_ARG_SPEC = {
    'common': {
        'name': {'required': True, 'type': 'str'},
        'remote_url': {'required': True, 'type': 'str'},
        'proxy_url': {'type': 'str'},
        'ssl_validation': {'default': True, 'type': 'bool'}
    },
    'file': {
    },
    'docker': {
        'upstream_name': {'required': True, 'type': 'str'}
    },
    'rpm': {
    }
}


class PulpRemoteAnsibleModule(PulpPluginAnsibleModule):

    def __init__(self):
        self.module_to_api_data = PULP_API_DATA
        PulpPluginAnsibleModule.__init__(self)

        self.state = self.module.params['state']
        self.api = load_pulp_plugin_api(self.module, self.pulp_plugin, REMOTE_API)

    def module_spec(self):
        arg_spec = PulpPluginAnsibleModule.argument_spec(self)
        arg_spec.update(
            name=dict(type='str', required=True),
            state=dict(
                default="present",
                choices=['absent', 'present']),
            repositories=dict(type='list', elements='str'),
            sync=dict(type='bool', default='false')
        )
        arg_spec.update(PULP_REMOTE_ARG_SPEC['common'])
        arg_spec.update(PULP_REMOTE_ARG_SPEC[self.pulp_plugin])
        return {'argument_spec': arg_spec, 'required_if': [('sync', True, ['repositories'])]}

    def execute(self):
        changed = False

        if self.state == 'present':
            changed = self.create_or_update()

            if self.module.params['sync']:
                sync_tasks = []
                repositories = []
                for repo_name in self.module.params['repositories']:
                    repository = get_repo(self.module, repo_name)
                    repositories.append(repository)

                remote = self.api.list(name=self.module.params['name']).results[0]
                for repository in repositories:
                    data = dict()
                    data['repository'] = repository.pulp_href
                    task = self.api.sync(remote.pulp_href, data)
                    sync_tasks.append({'repository': repository.name, 'task_href': task.task})
                    changed = True  # Syncing always seems to increment repo version

                self.module.exit_json(changed=changed, sync_tasks=sync_tasks)

        elif self.state == 'absent':
            changed = self.delete()

        self.module.exit_json(changed=changed)


def main():
    PulpRemoteAnsibleModule().execute()


if __name__ == '__main__':
    main()
