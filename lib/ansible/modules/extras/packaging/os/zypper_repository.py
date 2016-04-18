#!/usr/bin/python
# encoding: utf-8

# (c) 2013, Matthias Vogelgesang <matthias.vogelgesang@gmail.com>
# (c) 2014, Justin Lecher <jlec@gentoo.org>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.


DOCUMENTATION = '''
---
module: zypper_repository
author: "Matthias Vogelgesang (@matze)"
version_added: "1.4"
short_description: Add and remove Zypper repositories
description:
    - Add or remove Zypper repositories on SUSE and openSUSE
options:
    name:
        required: false
        default: none
        description:
            - A name for the repository. Not required when adding repofiles.
    repo:
        required: false
        default: none
        description:
            - URI of the repository or .repo file. Required when state=present.
    state:
        required: false
        choices: [ "absent", "present" ]
        default: "present"
        description:
            - A source string state.
    description:
        required: false
        default: none
        description:
            - A description of the repository
    disable_gpg_check:
        description:
            - Whether to disable GPG signature checking of
              all packages. Has an effect only if state is
              I(present).
        required: false
        default: "no"
        choices: [ "yes", "no" ]
    refresh:
        description:
            - Enable autorefresh of the repository.
        required: false
        default: "yes"
        choices: [ "yes", "no" ]
    priority:
        description:
            - Set priority of repository. Packages will always be installed
              from the repository with the smallest priority number.
        required: false
        version_added: "2.1"
    overwrite_multiple:
        description:
            - Overwrite multiple repository entries, if repositories with both name and
              URL already exist.
        required: false
        default: "no"
        choices: [ "yes", "no" ]
        version_added: "2.1"
requirements: 
    - "zypper >= 1.0  # included in openSuSE >= 11.1 or SuSE Linux Enterprise Server/Desktop >= 11.0"
'''

EXAMPLES = '''
# Add NVIDIA repository for graphics drivers
- zypper_repository: name=nvidia-repo repo='ftp://download.nvidia.com/opensuse/12.2' state=present

# Remove NVIDIA repository
- zypper_repository: name=nvidia-repo repo='ftp://download.nvidia.com/opensuse/12.2' state=absent

# Add python development repository
- zypper_repository: repo=http://download.opensuse.org/repositories/devel:/languages:/python/SLE_11_SP3/devel:languages:python.repo
'''

REPO_OPTS = ['alias', 'name', 'priority', 'enabled', 'autorefresh', 'gpgcheck']

def _parse_repos(module):
    """parses the output of zypper -x lr and return a parse repo dictionary"""
    cmd = ['/usr/bin/zypper', '-x', 'lr']

    from xml.dom.minidom import parseString as parseXML
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)
    if rc == 0:
        repos = []
        dom = parseXML(stdout)
        repo_list = dom.getElementsByTagName('repo')
        for repo in repo_list:
            opts = {}
            for o in REPO_OPTS:
                opts[o] = repo.getAttribute(o)
            opts['url'] = repo.getElementsByTagName('url')[0].firstChild.data
            # A repo can be uniquely identified by an alias + url
            repos.append(opts)
        return repos
    # exit code 6 is ZYPPER_EXIT_NO_REPOS (no repositories defined)
    elif rc == 6:
        return []
    else:
        d = { 'zypper_exit_code': rc }
        if stderr:
            d['stderr'] = stderr
        if stdout:
            d['stdout'] = stdout
        module.fail_json(msg='Failed to execute "%s"' % " ".join(cmd), **d)

def _repo_changes(realrepo, repocmp):
    for k in repocmp:
        if repocmp[k] and k not in realrepo:
            return True

    for k, v in realrepo.items():
        if k in repocmp and repocmp[k]:
            valold = str(repocmp[k] or "")
            valnew = v or ""
            if k == "url":
                valold, valnew = valold.rstrip("/"), valnew.rstrip("/")
            if valold != valnew:
                return True
    return False

def repo_exists(module, repodata, overwrite_multiple):
    existing_repos = _parse_repos(module)

    # look for repos that have matching alias or url to the one searched
    repos = []
    for kw in ['alias', 'url']:
        name = repodata[kw]
        for oldr in existing_repos:
            if repodata[kw] == oldr[kw] and oldr not in repos:
                repos.append(oldr)

    if len(repos) == 0:
        # Repo does not exist yet
        return (False, False, None)
    elif len(repos) == 1:
        # Found an existing repo, look for changes
        has_changes = _repo_changes(repos[0], repodata)
        return (True, has_changes, repos)
    elif len(repos) == 2 and overwrite_multiple:
        # Found two repos and want to overwrite_multiple
        return (True, True, repos)
    else:
        # either more than 2 repos (shouldn't happen)
        # or overwrite_multiple is not active
        module.fail_json(msg='More than one repo matched "%s": "%s"' % (name, repos))

def modify_repo(module, repodata, old_repos):
    repo = repodata['url']
    cmd = ['/usr/bin/zypper', 'ar', '--check']
    if repodata['name']:
        cmd.extend(['--name', repodata['name']])

    if repodata['priority']:
        cmd.extend(['--priority', str(repodata['priority'])])

    if repodata['enabled'] == '0':
        cmd.append('--disable')

    if repodata['gpgcheck'] == '1':
        cmd.append('--gpgcheck')
    else:
        cmd.append('--no-gpgcheck')

    if repodata['autorefresh'] == '1':
        cmd.append('--refresh')

    cmd.append(repo)

    if not repo.endswith('.repo'):
        cmd.append(repodata['alias'])

    if old_repos is not None:
        for oldrepo in old_repos:
            remove_repo(module, oldrepo['url'])

    rc, stdout, stderr = module.run_command(cmd, check_rc=False)
    changed = rc == 0
    if rc == 0:
        changed = True
    else:
        if stderr:
            module.fail_json(msg=stderr)
        else:
            module.fail_json(msg=stdout)

    return changed


def remove_repo(module, repo):
    cmd = ['/usr/bin/zypper', 'rr', repo]

    rc, stdout, stderr = module.run_command(cmd, check_rc=True)
    changed = rc == 0
    return changed


def fail_if_rc_is_null(module, rc, stdout, stderr):
    if rc != 0:
        #module.fail_json(msg=stderr if stderr else stdout)
        if stderr:
            module.fail_json(msg=stderr)
        else:
            module.fail_json(msg=stdout)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=False),
            repo=dict(required=False),
            state=dict(choices=['present', 'absent'], default='present'),
            description=dict(required=False),
            disable_gpg_check = dict(required=False, default='no', type='bool'),
            refresh = dict(required=False, default='yes', type='bool'),
            priority = dict(required=False, type='int'),
            enabled = dict(required=False, default='yes', type='bool'),
            overwrite_multiple = dict(required=False, default='no', type='bool'),
        ),
        supports_check_mode=False,
    )

    repo = module.params['repo']
    alias = module.params['name']
    state = module.params['state']
    overwrite_multiple = module.params['overwrite_multiple']

    repodata = {
        'url': repo,
        'alias': alias,
        'name': module.params['description'],
        'priority': module.params['priority'],
    }
    # rewrite bools in the language that zypper lr -x provides for easier comparison
    if module.params['enabled']:
        repodata['enabled'] = '1'
    else:
        repodata['enabled'] = '0'
    if module.params['disable_gpg_check']:
        repodata['gpgcheck'] = '0'
    else:
        repodata['gpgcheck'] = '1'
    if module.params['refresh']:
        repodata['autorefresh'] = '1'
    else:
        repodata['autorefresh'] = '0'

    def exit_unchanged():
        module.exit_json(changed=False, repodata=repodata, state=state)

    # Check run-time module parameters
    if state == 'present' and not repo:
        module.fail_json(msg='Module option state=present requires repo')
    if state == 'absent' and not repo and not alias:
        module.fail_json(msg='Alias or repo parameter required when state=absent')

    if repo and repo.endswith('.repo'):
        if alias:
            module.fail_json(msg='Incompatible option: \'name\'. Do not use name when adding .repo files')
    else:
        if not alias and state == "present":
            module.fail_json(msg='Name required when adding non-repo files.')

    exists, mod, old_repos = repo_exists(module, repodata, overwrite_multiple)

    if state == 'present':
        if exists and not mod:
            exit_unchanged()
        changed = modify_repo(module, repodata, old_repos)
    elif state == 'absent':
        if not exists:
            exit_unchanged()
        if not repo:
            repo=alias
        changed = remove_repo(module, repo)

    module.exit_json(changed=changed, repodata=repodata, state=state)

# import module snippets
from ansible.module_utils.basic import *

main()
