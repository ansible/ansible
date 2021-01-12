#!/usr/bin/python

# Copyright: (c) 2020, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
---
module: reset_pulp
short_description: Resets pulp back to the initial state
description:
- See short_description
options:
  pulp_api:
    description:
    - The Pulp API endpoint.
    required: yes
    type: str
  galaxy_ng_server:
    description:
    - The Galaxy NG API endpoint.
    required: yes
    type: str
  url_username:
    description:
    - The username to use when authenticating against Pulp.
    required: yes
    type: str
  url_password:
    description:
    - The password to use when authenticating against Pulp.
    required: yes
    type: str
  repositories:
    description:
    - A list of pulp repositories to create.
    - Galaxy NG expects a repository that matches C(GALAXY_API_DEFAULT_DISTRIBUTION_BASE_PATH) in
      C(/etc/pulp/settings.py) or the default of C(published).
    required: yes
    type: list
    elements: str
  namespaces:
    description:
    - A list of namespaces to create for Galaxy NG.
    required: yes
    type: list
    elements: str
author:
- Jordan Borean (@jborean93)
'''

EXAMPLES = '''
- name: reset pulp content
  reset_pulp:
    pulp_api: http://galaxy:24817
    galaxy_ng_server: http://galaxy/api/galaxy/
    url_username: username
    url_password: password
    repository: published
    namespaces:
    - namespace1
    - namespace2
'''

RETURN = '''
#
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.common.text.converters import to_text


def invoke_api(module, url, method='GET', data=None, status_codes=None):
    status_codes = status_codes or [200]
    headers = {}
    if data:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(data)

    resp, info = fetch_url(module, url, method=method, data=data, headers=headers)
    if info['status'] not in status_codes:
        module.fail_json(url=url, **info)

    data = to_text(resp.read())
    if data:
        return json.loads(data)


def delete_galaxy_namespace(namespace, module):
    """ Deletes the galaxy ng namespace specified. """
    ns_uri = '%sv3/namespaces/%s/' % (module.params['galaxy_ng_server'], namespace)
    invoke_api(module, ns_uri, method='DELETE', status_codes=[204])


def delete_pulp_distribution(distribution, module):
    """ Deletes the pulp distribution at the URI specified. """
    task_info = invoke_api(module, distribution, method='DELETE', status_codes=[202])
    wait_pulp_task(task_info['task'], module)


def delete_pulp_orphans(module):
    """ Deletes any orphaned pulp objects. """
    orphan_uri = module.params['pulp_api'] + '/pulp/api/v3/orphans/'
    task_info = invoke_api(module, orphan_uri, method='DELETE', status_codes=[202])
    wait_pulp_task(task_info['task'], module)


def delete_pulp_repository(repository, module):
    """ Deletes the pulp repository at the URI specified. """
    task_info = invoke_api(module, repository, method='DELETE', status_codes=[202])
    wait_pulp_task(task_info['task'], module)


def get_galaxy_namespaces(module):
    """ Gets a list of galaxy namespaces. """
    # No pagination has been implemented, shouldn't need unless we ever exceed 100 namespaces.
    namespace_uri = module.params['galaxy_ng_server'] + 'v3/namespaces/?limit=100&offset=0'
    ns_info = invoke_api(module, namespace_uri)

    return [n['name'] for n in ns_info['data']]


def get_pulp_distributions(module):
    """ Gets a list of all the pulp distributions. """
    distro_uri = module.params['pulp_api'] + '/pulp/api/v3/distributions/ansible/ansible/'
    distro_info = invoke_api(module, distro_uri)
    return [module.params['pulp_api'] + r['pulp_href'] for r in distro_info['results']]


def get_pulp_repositories(module):
    """ Gets a list of all the pulp repositories. """
    repo_uri = module.params['pulp_api'] + '/pulp/api/v3/repositories/ansible/ansible/'
    repo_info = invoke_api(module, repo_uri)
    return [module.params['pulp_api'] + r['pulp_href'] for r in repo_info['results']]


def new_galaxy_namespace(name, module):
    """ Creates a new namespace in Galaxy NG. """
    ns_uri = module.params['galaxy_ng_server'] + 'v3/_ui/namespaces/'
    data = {'name': name, 'groups': [{'name': 'system:partner-engineers', 'object_permissions':
            ['add_namespace', 'change_namespace', 'upload_to_namespace']}]}
    ns_info = invoke_api(module, ns_uri, method='POST', data=data, status_codes=[201])

    return ns_info['id']


def new_pulp_repository(name, module):
    """ Creates a new pulp repository. """
    repo_uri = module.params['pulp_api'] + '/pulp/api/v3/repositories/ansible/ansible/'
    data = {'name': name}
    repo_info = invoke_api(module, repo_uri, method='POST', data=data, status_codes=[201])

    return module.params['pulp_api'] + repo_info['pulp_href']


def new_pulp_distribution(name, base_path, repository, module):
    """ Creates a new pulp distribution for a repository. """
    distro_uri = module.params['pulp_api'] + '/pulp/api/v3/distributions/ansible/ansible/'
    data = {'name': name, 'base_path': base_path, 'repository': repository}
    task_info = invoke_api(module, distro_uri, method='POST', data=data, status_codes=[202])
    task_info = wait_pulp_task(task_info['task'], module)

    return module.params['pulp_api'] + task_info['created_resources'][0]


def wait_pulp_task(task, module):
    """ Waits for a pulp import task to finish. """
    while True:
        task_info = invoke_api(module, module.params['pulp_api'] + task)
        if task_info['finished_at'] is not None:
            break

    return task_info


def main():
    module_args = dict(
        pulp_api=dict(type='str', required=True),
        galaxy_ng_server=dict(type='str', required=True),
        url_username=dict(type='str', required=True),
        url_password=dict(type='str', required=True, no_log=True),
        repositories=dict(type='list', elements='str', required=True),
        namespaces=dict(type='list', elements='str', required=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )
    module.params['force_basic_auth'] = True

    [delete_pulp_distribution(d, module) for d in get_pulp_distributions(module)]
    [delete_pulp_repository(r, module) for r in get_pulp_repositories(module)]
    delete_pulp_orphans(module)
    [delete_galaxy_namespace(n, module) for n in get_galaxy_namespaces(module)]

    for repository in module.params['repositories']:
        repo_href = new_pulp_repository(repository, module)
        new_pulp_distribution(repository, repository, repo_href, module)
    [new_galaxy_namespace(n, module) for n in module.params['namespaces']]

    module.exit_json(changed=True)


if __name__ == '__main__':
    main()
