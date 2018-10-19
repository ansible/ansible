#!/usr/bin/python
# encoding: utf-8

# (c) 2013, Matthias Vogelgesang <matthias.vogelgesang@gmail.com>
# (c) 2014, Justin Lecher <jlec@gentoo.org>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


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
        description:
            - A name for the repository. Not required when adding repofiles.
    repo:
        description:
            - URI of the repository or .repo file. Required when state=present.
    state:
        description:
            - A source string state.
        choices: [ "absent", "present" ]
        default: "present"
    description:
        description:
            - A description of the repository
    disable_gpg_check:
        description:
            - Whether to disable GPG signature checking of
              all packages. Has an effect only if state is
              I(present).
            - Needs zypper version >= 1.6.2.
        type: bool
        default: 'no'
    autorefresh:
        description:
            - Enable autorefresh of the repository.
        type: bool
        default: 'yes'
        aliases: [ "refresh" ]
    priority:
        description:
            - Set priority of repository. Packages will always be installed
              from the repository with the smallest priority number.
            - Needs zypper version >= 1.12.25.
        version_added: "2.1"
    overwrite_multiple:
        description:
            - Overwrite multiple repository entries, if repositories with both name and
              URL already exist.
        type: bool
        default: 'no'
        version_added: "2.1"
    auto_import_keys:
        description:
            - Automatically import the gpg signing key of the new or changed repository.
            - Has an effect only if state is I(present). Has no effect on existing (unchanged) repositories or in combination with I(absent).
            - Implies runrefresh.
            - Only works with C(.repo) files if `name` is given explicitly.
        type: bool
        default: 'no'
        version_added: "2.2"
    runrefresh:
        description:
            - Refresh the package list of the given repository.
            - Can be used with repo=* to refresh all repositories.
        type: bool
        default: 'no'
        version_added: "2.2"
    enabled:
        description:
            - Set repository to enabled (or disabled).
        type: bool
        default: 'yes'
        version_added: "2.2"


requirements:
    - "zypper >= 1.0  # included in openSuSE >= 11.1 or SuSE Linux Enterprise Server/Desktop >= 11.0"
    - python-xml
'''

EXAMPLES = '''
# Add NVIDIA repository for graphics drivers
- zypper_repository:
    name: nvidia-repo
    repo: 'ftp://download.nvidia.com/opensuse/12.2'
    state: present

# Remove NVIDIA repository
- zypper_repository:
    name: nvidia-repo
    repo: 'ftp://download.nvidia.com/opensuse/12.2'
    state: absent

# Add python development repository
- zypper_repository:
    repo: 'http://download.opensuse.org/repositories/devel:/languages:/python/SLE_11_SP3/devel:languages:python.repo'

# Refresh all repos
- zypper_repository:
    repo: '*'
    runrefresh: yes

# Add a repo and add it's gpg key
- zypper_repository:
    repo: 'http://download.opensuse.org/repositories/systemsmanagement/openSUSE_Leap_42.1/'
    auto_import_keys: yes

# Force refresh of a repository
- zypper_repository:
    repo: 'http://my_internal_ci_repo/repo'
    name: my_ci_repo
    state: present
    runrefresh: yes
'''

from distutils.version import LooseVersion

from ansible.module_utils.basic import AnsibleModule


REPO_OPTS = ['alias', 'name', 'priority', 'enabled', 'autorefresh', 'gpgcheck']


def _get_cmd(*args):
    """Combines the non-interactive zypper command with arguments/subcommands"""
    cmd = ['/usr/bin/zypper', '--quiet', '--non-interactive']
    cmd.extend(args)

    return cmd


def _parse_repos(module):
    """parses the output of zypper --xmlout repos and return a parse repo dictionary"""
    cmd = _get_cmd('--xmlout', 'repos')

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
        module.fail_json(msg='Failed to execute "%s"' % " ".join(cmd), rc=rc, stdout=stdout, stderr=stderr)


def _repo_changes(realrepo, repocmp):
    "Check whether the 2 given repos have different settings."
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
    """Check whether the repository already exists.

        returns (exists, mod, old_repos)
            exists: whether a matching (name, URL) repo exists
            mod: whether there are changes compared to the existing repo
            old_repos: list of matching repos
    """
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
    elif len(repos) >= 2:
        if overwrite_multiple:
            # Found two repos and want to overwrite_multiple
            return (True, True, repos)
        else:
            errmsg = 'More than one repo matched "%s": "%s".' % (name, repos)
            errmsg += ' Use overwrite_multiple to allow more than one repo to be overwritten'
            module.fail_json(msg=errmsg)


def addmodify_repo(module, repodata, old_repos, zypper_version, warnings):
    "Adds the repo, removes old repos before, that would conflict."
    repo = repodata['url']
    cmd = _get_cmd('addrepo', '--check')
    if repodata['name']:
        cmd.extend(['--name', repodata['name']])

    # priority on addrepo available since 1.12.25
    # https://github.com/openSUSE/zypper/blob/b9b3cb6db76c47dc4c47e26f6a4d2d4a0d12b06d/package/zypper.changes#L327-L336
    if repodata['priority']:
        if zypper_version >= LooseVersion('1.12.25'):
            cmd.extend(['--priority', str(repodata['priority'])])
        else:
            warnings.append("Setting priority only available for zypper >= 1.12.25. Ignoring priority argument.")

    if repodata['enabled'] == '0':
        cmd.append('--disable')

    # gpgcheck available since 1.6.2
    # https://github.com/openSUSE/zypper/blob/b9b3cb6db76c47dc4c47e26f6a4d2d4a0d12b06d/package/zypper.changes#L2446-L2449
    # the default changed in the past, so don't assume a default here and show warning for old zypper versions
    if zypper_version >= LooseVersion('1.6.2'):
        if repodata['gpgcheck'] == '1':
            cmd.append('--gpgcheck')
        else:
            cmd.append('--no-gpgcheck')
    else:
        warnings.append("Enabling/disabling gpgcheck only available for zypper >= 1.6.2. Using zypper default value.")

    if repodata['autorefresh'] == '1':
        cmd.append('--refresh')

    cmd.append(repo)

    if not repo.endswith('.repo'):
        cmd.append(repodata['alias'])

    if old_repos is not None:
        for oldrepo in old_repos:
            remove_repo(module, oldrepo['url'])

    rc, stdout, stderr = module.run_command(cmd, check_rc=False)
    return rc, stdout, stderr


def remove_repo(module, repo):
    "Removes the repo."
    cmd = _get_cmd('removerepo', repo)

    rc, stdout, stderr = module.run_command(cmd, check_rc=True)
    return rc, stdout, stderr


def get_zypper_version(module):
    rc, stdout, stderr = module.run_command(['/usr/bin/zypper', '--version'])
    if rc != 0 or not stdout.startswith('zypper '):
        return LooseVersion('1.0')
    return LooseVersion(stdout.split()[1])


def runrefreshrepo(module, auto_import_keys=False, shortname=None):
    "Forces zypper to refresh repo metadata."
    if auto_import_keys:
        cmd = _get_cmd('--gpg-auto-import-keys', 'refresh', '--force')
    else:
        cmd = _get_cmd('refresh', '--force')
    if shortname is not None:
        cmd.extend(['-r', shortname])

    rc, stdout, stderr = module.run_command(cmd, check_rc=True)
    return rc, stdout, stderr


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=False),
            repo=dict(required=False),
            state=dict(choices=['present', 'absent'], default='present'),
            runrefresh=dict(required=False, default='no', type='bool'),
            description=dict(required=False),
            disable_gpg_check=dict(required=False, default=False, type='bool'),
            autorefresh=dict(required=False, default=True, type='bool', aliases=['refresh']),
            priority=dict(required=False, type='int'),
            enabled=dict(required=False, default=True, type='bool'),
            overwrite_multiple=dict(required=False, default=False, type='bool'),
            auto_import_keys=dict(required=False, default=False, type='bool'),
        ),
        supports_check_mode=False,
        required_one_of=[['state', 'runrefresh']],
    )

    repo = module.params['repo']
    alias = module.params['name']
    state = module.params['state']
    overwrite_multiple = module.params['overwrite_multiple']
    auto_import_keys = module.params['auto_import_keys']
    runrefresh = module.params['runrefresh']

    zypper_version = get_zypper_version(module)
    warnings = []  # collect warning messages for final output

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
    if module.params['autorefresh']:
        repodata['autorefresh'] = '1'
    else:
        repodata['autorefresh'] = '0'

    def exit_unchanged():
        module.exit_json(changed=False, repodata=repodata, state=state)

    # Check run-time module parameters
    if repo == '*' or alias == '*':
        if runrefresh:
            runrefreshrepo(module, auto_import_keys)
            module.exit_json(changed=False, runrefresh=True)
        else:
            module.fail_json(msg='repo=* can only be used with the runrefresh option.')

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

    if repo:
        shortname = repo
    else:
        shortname = alias

    if state == 'present':
        if exists and not mod:
            if runrefresh:
                runrefreshrepo(module, auto_import_keys, shortname)
            exit_unchanged()
        rc, stdout, stderr = addmodify_repo(module, repodata, old_repos, zypper_version, warnings)
        if rc == 0 and (runrefresh or auto_import_keys):
            runrefreshrepo(module, auto_import_keys, shortname)
    elif state == 'absent':
        if not exists:
            exit_unchanged()
        rc, stdout, stderr = remove_repo(module, shortname)

    if rc == 0:
        module.exit_json(changed=True, repodata=repodata, state=state, warnings=warnings)
    else:
        module.fail_json(msg="Zypper failed with rc %s" % rc, rc=rc, stdout=stdout, stderr=stderr, repodata=repodata, state=state, warnings=warnings)


if __name__ == '__main__':
    main()
