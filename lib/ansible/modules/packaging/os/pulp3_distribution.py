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

module: pulp3_distribution

short_description: Manage Pulp3 Distributions

version_added: "2.10"

author:
  - Timo Funke (@timoses)

description:
  - Supports CRUD operations against Pulp3 Distributions.
  - Enables assignment to publications matching a repository name or repository_version.

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
  base_path:
    description:
    - The base (relative) path component of the published url.
    - Avoid paths that overlap with other distribution base paths (e.g. "foo" and "foo/bar").
    type: str
    required: true
  publication:
    description:
    - Specification of a publication which this distribution will connect to.
    - If no matching publication is found one is created.
    - Required only for the following plugins - C(file), C(rpm)
    type: dict
    suboptions:
      repository:
        description:
        - Name of a repository.
        type: str
        required: true
      repository_version:
        description:
        - Version of the repository. Defaults to latest if not specified.
        type: int
  repository:
    description:
    - Name of the repository to distribute.
    - Only required by the following plugins - C(docker)
    type: str
  repository_version:
    description:
    - Version of the I(repository). Defaults to latest if not specified.
    - Only valid for the following plugins - C(docker)
    type: int


requirements:
  - "pulpcore-client >= 2.7"
  - "pulp-<pulp_plugin>-client"
'''

EXAMPLES = '''
# Files will be available under http://<pulp_host>/pulp/content/testfiles/<file>
- name: Distribute a file repository
  pulp3_distribution:
    name: file_distribution
    pulp_plugin: file
    base_path: testfiles
    publication:
      repository: my_repo
      repository_version: 14

# Distribute docker repo available as `docker pull <pulp_host>/testdocker`
- name: Distribute a docker repository
  pulp3_distribution:
    name: docker_distribution
    pulp_plugin: docker
    base_path: testdocker
    repository: my_repo
'''

RETURN = r''' # '''

from time import sleep

from ansible.module_utils.pulp3 import PulpPluginAnsibleModule, DISTRIBUTION_API, PUBLICATION_API, \
    load_pulp_plugin_api, get_repo, load_pulp_api, TASK_API, get_repo_version


PULP_API_DATA = {
    'base_path': 'base_path',
    'name': 'name'
}

PULP_PUBLICATION = {
    'type': 'dict',
    'options': {
        'repository': {'type': 'str'},
        'repository_version': {'type': 'int'}
    }
}

PULP_DISTRIBUTION_ARG_SPEC = {
    'base_path': {'required': True, 'type': 'str'},
    'name': {'required': True, 'type': 'str'},
    'publication': PULP_PUBLICATION,
    'repository': {'type': 'str'},
    'repository_version': {'type': 'int'},
}


class PulpDistributionAnsibleModule(PulpPluginAnsibleModule):

    def __init__(self):
        self.module_to_api_data = PULP_API_DATA
        PulpPluginAnsibleModule.__init__(self)

        self.state = self.module.params['state']
        self.api = load_pulp_plugin_api(self.module, self.pulp_plugin, DISTRIBUTION_API)

    def module_spec(self):
        arg_spec = PulpPluginAnsibleModule.argument_spec(self)
        arg_spec.update(
            name=dict(type='str', required=True),
            state=dict(
                default="present",
                choices=['absent', 'present'])
        )
        arg_spec.update(PULP_DISTRIBUTION_ARG_SPEC)
        return {'argument_spec': arg_spec}

    def execute(self):
        tasks = []
        changed = False

        if self.state == 'present':

            if self.module.params['publication'] is not None:
                self.api_data.update(self.process_publication())

            if self.module.params['repository'] is not None:
                self.api_data.update(self.process_repository())

            changed = self.create_or_update()

        elif self.state == 'absent':
            changed = self.delete()

        self.module.exit_json(changed=changed)

    def process_publication(self):
        data = {}
        publication_params = self.module.params['publication']
        publ_api = load_pulp_plugin_api(self.module, self.pulp_plugin, PUBLICATION_API)

        if 'repository' in publication_params:
            repository = get_repo(self.module, publication_params['repository'])

            if not repository.latest_version_href:
                self.module.fail_json(msg="Repository %s has no versions. Unable to process publication." % publication_params['repository'])

            latest_version = repository.latest_version_href.split('/')[-2]
            if publication_params['repository_version']:
                if int(publication_params['repository_version']) > int(latest_version):
                    self.module.fail_json(msg="Repository version '%s' is larger than latest available \
                            version (%s)." % (publication_params['repository_version'], latest_version))

            # Search for matching Publication
            publications = publ_api.list()
            found_publ = None
            for publication in publications.results:
                if publication.repository_version is not None:
                    publ_repo_href = '/'.join(publication.repository_version.split('/')[0:-3]) + '/'
                    if publ_repo_href == repository.pulp_href:
                        publ_repo_version = publication.repository_version.split('/')[-2]
                        if publication_params['repository_version'] and \
                                int(publication_params['repository_version']) == int(publ_repo_version):
                            data['publication'] = publication.pulp_href
                            break
                        elif int(publ_repo_version) == int(latest_version):
                            data['publication'] = publication.pulp_href
                            break

            # Create publication if not present
            if 'publication' not in data:
                publ_data = dict()
                if publication_params['repository_version']:
                    publ_data['repository_version'] = repository.pulp_href + 'versions/' + str(publication_params['repository_version']) + '/'
                else:
                    publ_data['repository'] = repository.pulp_href
                publication = publ_api.create(publ_data)
                task_api = load_pulp_api(self.module, TASK_API)
                while True:
                    publ_task = task_api.read(publication.task)
                    if publ_task.state == 'completed':
                        break
                    sleep(.500)
                data['publication'] = publ_task.created_resources[0]

            return data

    def process_repository(self):
        data = {}
        repository = get_repo(self.module, self.module.params['repository'])
        if self.module.params['repository_version'] is not None:
            repository_version = get_repo_version(self.module, repository, self.module.params['repository_version'])
            data['repository_version'] = repository_version.pulp_href
        else:
            data['repository'] = repository.pulp_href

        return data


def main():
    PulpDistributionAnsibleModule().execute()


if __name__ == '__main__':
    main()
