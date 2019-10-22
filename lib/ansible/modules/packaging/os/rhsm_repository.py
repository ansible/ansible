#!/usr/bin/python

# Copyright: (c) 2017, Giovanni Sciortino (@giovannisciortino)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: rhsm_repository
short_description: Manage RHSM repositories using the subscription-manager command
description:
  - Manage (Enable/Disable) RHSM repositories to the Red Hat Subscription
    Management entitlement platform using the C(subscription-manager) command.
version_added: '2.5'
author: Giovanni Sciortino (@giovannisciortino)
notes:
  - In order to manage RHSM repositories the system must be already registered
    to RHSM manually or using the Ansible C(redhat_subscription) module.

requirements:
  - subscription-manager
options:
  state:
    description:
      - If state is equal to present or disabled, indicates the desired
        repository state.
    choices: [present, enabled, absent, disabled]
    required: True
    default: "present"
  name:
    description:
      - The ID of repositories to enable.
      - To operate on several repositories this can accept a comma separated
        list or a YAML list.
    required: True
  purge:
    description:
      - Disable all currently enabled repositories that are not not specified in C(name).
        Only set this to C(True) if passing in a list of repositories to the C(name) field.
        Using this with C(loop) will most likely not have the desired result.
    type: bool
    default: False
    version_added: "2.8"
'''

EXAMPLES = '''
- name: Enable a RHSM repository
  rhsm_repository:
    name: rhel-7-server-rpms

- name: Disable all RHSM repositories
  rhsm_repository:
    name: '*'
    state: disabled

- name: Enable all repositories starting with rhel-6-server
  rhsm_repository:
    name: rhel-6-server*
    state: enabled

- name: Disable all repositories except rhel-7-server-rpms
  rhsm_repository:
    name: rhel-7-server-rpms
    purge: True
'''

RETURN = '''
repositories:
  description:
    - The list of RHSM repositories with their states.
    - When this module is used to change the repository states, this list contains the updated states after the changes.
  returned: success
  type: list
'''

import re
import os
from fnmatch import fnmatch
from copy import deepcopy
from ansible.module_utils.basic import AnsibleModule


def run_subscription_manager(module, arguments):
    # Execute subscription-manager with arguments and manage common errors
    rhsm_bin = module.get_bin_path('subscription-manager')
    if not rhsm_bin:
        module.fail_json(msg='The executable file subscription-manager was not found in PATH')

    lang_env = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C')
    rc, out, err = module.run_command("%s %s" % (rhsm_bin, " ".join(arguments)), environ_update=lang_env)

    if rc == 1 and (err == 'The password you typed is invalid.\nPlease try again.\n' or os.getuid() != 0):
        module.fail_json(msg='The executable file subscription-manager must be run using root privileges')
    elif rc == 0 and out == 'This system has no repositories available through subscriptions.\n':
        module.fail_json(msg='This system has no repositories available through subscriptions')
    elif rc == 1:
        module.fail_json(msg='subscription-manager failed with the following error: %s' % err)
    else:
        return rc, out, err


def get_repository_list(module, list_parameter):
    # Generate RHSM repository list and return a list of dict
    if list_parameter == 'list_enabled':
        rhsm_arguments = ['repos', '--list-enabled']
    elif list_parameter == 'list_disabled':
        rhsm_arguments = ['repos', '--list-disabled']
    elif list_parameter == 'list':
        rhsm_arguments = ['repos', '--list']
    rc, out, err = run_subscription_manager(module, rhsm_arguments)

    skip_lines = [
        '+----------------------------------------------------------+',
        '    Available Repositories in /etc/yum.repos.d/redhat.repo'
    ]
    repo_id_re = re.compile(r'Repo ID:\s+(.*)')
    repo_name_re = re.compile(r'Repo Name:\s+(.*)')
    repo_url_re = re.compile(r'Repo URL:\s+(.*)')
    repo_enabled_re = re.compile(r'Enabled:\s+(.*)')

    repo_id = ''
    repo_name = ''
    repo_url = ''
    repo_enabled = ''

    repo_result = []
    for line in out.splitlines():
        if line == '' or line in skip_lines:
            continue

        repo_id_match = repo_id_re.match(line)
        if repo_id_match:
            repo_id = repo_id_match.group(1)
            continue

        repo_name_match = repo_name_re.match(line)
        if repo_name_match:
            repo_name = repo_name_match.group(1)
            continue

        repo_url_match = repo_url_re.match(line)
        if repo_url_match:
            repo_url = repo_url_match.group(1)
            continue

        repo_enabled_match = repo_enabled_re.match(line)
        if repo_enabled_match:
            repo_enabled = repo_enabled_match.group(1)

            repo = {
                "id": repo_id,
                "name": repo_name,
                "url": repo_url,
                "enabled": True if repo_enabled == '1' else False
            }

            repo_result.append(repo)

    return repo_result


def repository_modify(module, state, name, purge=False):
    name = set(name)
    current_repo_list = get_repository_list(module, 'list')
    updated_repo_list = deepcopy(current_repo_list)
    matched_existing_repo = {}
    for repoid in name:
        matched_existing_repo[repoid] = []
        for idx, repo in enumerate(current_repo_list):
            if fnmatch(repo['id'], repoid):
                matched_existing_repo[repoid].append(repo)
                # Update current_repo_list to return it as result variable
                updated_repo_list[idx]['enabled'] = True if state == 'enabled' else False

    changed = False
    results = []
    diff_before = ""
    diff_after = ""
    rhsm_arguments = ['repos']

    for repoid in matched_existing_repo:
        if len(matched_existing_repo[repoid]) == 0:
            results.append("%s is not a valid repository ID" % repoid)
            module.fail_json(results=results, msg="%s is not a valid repository ID" % repoid)
        for repo in matched_existing_repo[repoid]:
            if state in ['disabled', 'absent']:
                if repo['enabled']:
                    changed = True
                    diff_before += "Repository '%s' is enabled for this system\n" % repo['id']
                    diff_after += "Repository '%s' is disabled for this system\n" % repo['id']
                results.append("Repository '%s' is disabled for this system" % repo['id'])
                rhsm_arguments += ['--disable', repo['id']]
            elif state in ['enabled', 'present']:
                if not repo['enabled']:
                    changed = True
                    diff_before += "Repository '%s' is disabled for this system\n" % repo['id']
                    diff_after += "Repository '%s' is enabled for this system\n" % repo['id']
                results.append("Repository '%s' is enabled for this system" % repo['id'])
                rhsm_arguments += ['--enable', repo['id']]

    # Disable all enabled repos on the system that are not in the task and not
    # marked as disabled by the task
    if purge:
        enabled_repo_ids = set(repo['id'] for repo in updated_repo_list if repo['enabled'])
        matched_repoids_set = set(matched_existing_repo.keys())
        difference = enabled_repo_ids.difference(matched_repoids_set)
        if len(difference) > 0:
            for repoid in difference:
                changed = True
                diff_before.join("Repository '{repoid}'' is enabled for this system\n".format(repoid=repoid))
                diff_after.join("Repository '{repoid}' is disabled for this system\n".format(repoid=repoid))
                results.append("Repository '{repoid}' is disabled for this system".format(repoid=repoid))
                rhsm_arguments.extend(['--disable', repoid])

    diff = {'before': diff_before,
            'after': diff_after,
            'before_header': "RHSM repositories",
            'after_header': "RHSM repositories"}

    if not module.check_mode:
        rc, out, err = run_subscription_manager(module, rhsm_arguments)
        results = out.splitlines()
    module.exit_json(results=results, changed=changed, repositories=updated_repo_list, diff=diff)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='list', required=True),
            state=dict(choices=['enabled', 'disabled', 'present', 'absent'], default='enabled'),
            purge=dict(type='bool', default=False),
        ),
        supports_check_mode=True,
    )
    name = module.params['name']
    state = module.params['state']
    purge = module.params['purge']

    repository_modify(module, state, name, purge)


if __name__ == '__main__':
    main()
