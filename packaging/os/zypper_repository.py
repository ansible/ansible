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
        aliases: []
    refresh:
        description:
            - Enable autorefresh of the repository.
        required: false
        default: "yes"
        choices: [ "yes", "no" ]
        aliases: []
notes: []
requirements: [ zypper ]
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

def zypper_version(module):
    """Return (rc, message) tuple"""
    cmd = ['/usr/bin/zypper', '-V']
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)
    if rc == 0:
        return rc, stdout
    else:
        return rc, stderr

def _parse_repos(module):
    """parses the output of zypper -x lr and returns a parse repo dictionary"""
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

def _parse_repos_old(module):
    """parses the output of zypper sl and returns a parse repo dictionary"""
    cmd = ['/usr/bin/zypper', 'sl']
    repos = []
    rc, stdout, stderr = module.run_command(cmd, check_rc=True)
    for line in stdout.split('\n'):
        matched = re.search(r'\d+\s+\|\s+(?P<enabled>\w+)\s+\|\s+(?P<autorefresh>\w+)\s+\|\s+(?P<type>\w+)\s+\|\s+(?P<name>\w+)\s+\|\s+(?P<url>.*)', line)
        if matched == None:
            continue

        m = matched.groupdict()
        m['alias']= m['name']
        m['priority'] = 100
        m['gpgcheck'] = 1
        repos.append(m)

    return repos

def repo_exists(module, old_zypper, **kwargs):

    def repo_subset(realrepo, repocmp):
        for k in repocmp:
            if k not in realrepo:
                return False

        for k, v in realrepo.items():
            if k in repocmp:
                if v.rstrip("/") != repocmp[k].rstrip("/"):
                    return False
        return True

    if old_zypper:
        repos = _parse_repos_old(module)
    else:
        repos = _parse_repos(module)

    for repo in repos:
        if repo_subset(repo, kwargs):
            return True
    return False


def add_repo(module, repo, alias, description, disable_gpg_check, old_zypper, refresh):
    if old_zypper:
        cmd = ['/usr/bin/zypper', 'sa']
    else:
        cmd = ['/usr/bin/zypper', 'ar', '--check']

    if repo.startswith("file:/") and old_zypper:
        cmd.extend(['-t', 'Plaindir'])
    else:
        cmd.extend(['-t', 'plaindir'])

    if description:
        cmd.extend(['--name', description])

    if disable_gpg_check and not old_zypper:
        cmd.append('--no-gpgcheck')

    if refresh:
        cmd.append('--refresh')

    cmd.append(repo)

    if not repo.endswith('.repo'):
        cmd.append(alias)

    rc, stdout, stderr = module.run_command(cmd, check_rc=False)
    changed = rc == 0
    if rc == 0:
        changed = True
    elif 'already exists. Please use another alias' in stderr:
        changed = False
    else:
        #module.fail_json(msg=stderr if stderr else stdout)
        if stderr:
            module.fail_json(msg=stderr)
        else:
            module.fail_json(msg=stdout)

    return changed


def remove_repo(module, repo, alias, old_zypper):

    if old_zypper:
        cmd = ['/usr/bin/zypper', 'sd']
    else:
        cmd = ['/usr/bin/zypper', 'rr']
    if alias:
        cmd.append(alias)
    else:
        cmd.append(repo)

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
        ),
        supports_check_mode=False,
    )

    repo = module.params['repo']
    state = module.params['state']
    name = module.params['name']
    description = module.params['description']
    disable_gpg_check = module.params['disable_gpg_check']
    refresh = module.params['refresh']

    def exit_unchanged():
        module.exit_json(changed=False, repo=repo, state=state, name=name)

    rc, out = zypper_version(module)
    match = re.match(r'zypper\s+(\d+)\.(\d+)\.(\d+)', out)
    if not match or  int(match.group(1)) > 0:
        old_zypper = False
    else:
        old_zypper = True

    # Check run-time module parameters
    if state == 'present' and not repo:
        module.fail_json(msg='Module option state=present requires repo')
    if state == 'absent' and not repo and not name:
        module.fail_json(msg='Alias or repo parameter required when state=absent')

    if repo and repo.endswith('.repo'):
        if name:
            module.fail_json(msg='Incompatible option: \'name\'. Do not use name when adding repo files')
    else:
        if not name and state == "present":
            module.fail_json(msg='Name required when adding non-repo files:')

    if repo and repo.endswith('.repo'):
        exists = repo_exists(module, old_zypper, url=repo, alias=name)
    elif repo:
        exists = repo_exists(module, old_zypper, url=repo)
    else:
        exists = repo_exists(module, old_zypper, alias=name)

    if state == 'present':
        if exists:
            exit_unchanged()

        changed = add_repo(module, repo, name, description, disable_gpg_check, old_zypper, refresh)
    elif state == 'absent':
        if not exists:
            exit_unchanged()

        changed = remove_repo(module, repo, name, old_zypper)

    module.exit_json(changed=changed, repo=repo, state=state)

# import module snippets
from ansible.module_utils.basic import *

main()
