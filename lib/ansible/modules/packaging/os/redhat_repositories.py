#!/usr/bin/python
# vim:  et tw=120 ts=4 sw=4
# Jerome Fenal (jfenal@redhat.com)
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


ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '1.0'
}

DOCUMENTATION = '''
---
module: redhat_repositories
short_description: Manage repositories with RHSM using the C(subscription-manager) command
description:
  - Manage repositories with the Red Hat Subscription Management entitlement
    platform using the C(subscription-manager) command
author: "Jerome Fenal (@jfenal)"
notes:
  - In order to be able to enable repositories, a system will
    need first to be subscribed to RHSM. Use the
    C(redhat_subscription) Ansible module for that matter.
version_added: "2.4"
requirements:
  - subscription-manager
options:
  id:
    description:
      - id of repositories to enable or disable.
        When specifying multiple repos, separate them with a C(,).
        To specify all repositories, use C(*).
        In incremental mode, other repos won't be touched.
        In idempotent mode (default), other repos would be disabled or enabled
        depending on their actual state.
    required: False
    default: null
  list:
    description:
      - List either all repositories, or only enabled or disabled.
    required: False
    default: all
    choices: [ "all", "enabled", "disabled" ]
  mode:
    description:
      - Use either the idempotent or the incremental mode.
    required: False
    default: "idempotent"
    choices: [ "idempotent", "incremental" ]
  state:
    description:
      - Whether to enable (C(enabled)) or disable (C(disabled)) a repository.
    required: False
    choices: [ "enabled", "disabled" ]
    default: "enabled"

'''

EXAMPLES = '''
# List all repositories
- redhat_repositories:
    list: all

# List enabled repositories
- redhat_repositories:
    list: enabled

# List disabled repositories
- redhat_repositories:
    list: disabled

# Enable only those repositories (implicit default idempotent mode)
- redhat_repositories:
    id:
      - rhel-7-server-rpms
      - rhel-7-server-optional-rpms
    state: enabled

# Enable only those repositories (explicit idempotent mode)
- redhat_repositories:
    id:
      - rhel-7-server-rpms
      - rhel-7-server-optional-rpms
    state: enabled
    mode: idempotent

# Disable repositories
- redhat_repositories:
    id:
      - .*-beta-.*
      - .*-htb-.*
      - .*-eus-.*
      - .*-aus-.*
    state: disabled
    mode: incremental

# Disable all repositories (mode=incremental must be specified for now)
- redhat_repositories:
    id: "*"
    state: disabled
    mode: incremental
'''

RETURN = '''
redhat_repositories:
    description: list of repositories and their data
    returned: always
    type: dict
    sample: '{
        "redhat_repositories": {
            "rhel_7_server_extras_rpms": {
                "enabled": true,
                "id": "rhel-7-server-extras-rpms",
                "name": "Red Hat Enterprise Linux 7 Server - Extras (RPMs)",
                "url": "https://cdn.redhat.com/content/dist/rhel/server/7/7Server/$basearch/extras/os"
            },
            "rhel_7_server_rpms": {
                "enabled": true,
                "id": "rhel-7-server-rpms",
                "name": "Red Hat Enterprise Linux 7 Server (RPMs)",
                "url": "https://cdn.redhat.com/content/dist/rhel/server/7/$releasever/$basearch/os"
            }
        }
    }'

'''

import os
import re
import syslog
from ansible.module_utils.basic import AnsibleModule

debug=False


def notice(msg):
    if debug:
        syslog.syslog(syslog.LOG_NOTICE, msg)


if debug:
    syslog.openlog('ansible-%s' % os.path.basename(__file__))


class RhsmRepository(object):
    '''
        This class to host Repository information and enable/disable per repo
    '''
    def __init__(self, module, **kwargs):
        self.module = module
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __str__(self):
        return str(self.__getattribute('_name'))

    @property
    def id(self):
        return self.RepoID

    @property
    def name(self):
        return self.RepoName

    @property
    def url(self):
        return self.RepoURL

    @property
    def is_enabled(self):
        return self.Enabled

    @property
    def is_disabled(self):
        return not self.Enabled


class RhsmRepositories(object):
    '''
        This class to manipulate repositories
    '''

    def __init__(self, module):
        self.module = module
        self.repos = self._load_repo_list()

    def __iter__(self):
        return self.repos.__iter__()

    def _load_repo_list(self):
        """
            Loads list of all available repos, whether enabled or not
        """

        args = "subscription-manager repos --list"
        rc, stdout, stderr = self.module.run_command(args, check_rc=True, environ_update=dict(LANG='C'))

        repos = []
        for line in stdout.split('\n'):

            # Remove leading+trailing whitespace
            line = line.strip()

            # An empty line implies the end of a output group, strip headers too
            if len(line) == 0 or re.match(r'^\s+.*', line) or re.match(r'^\+s.*', line):
                key = ''
                value = ''
                continue

            # If a colon ':' is found, parse
            elif ':' in line:
                (key, value) = line.split(':', 1)
                key = key.strip().replace(" ", "")  # To unify
                value = value.strip()
                if key in ['RepoID']:
                    # Remember the name for later processing
                    repos.append(RhsmRepository(self.module, _name=value))
                    repos[-1].__setattr__(key, value)
                elif key in ['Enabled']:
                    # Use a real boolean
                    repos[-1].__setattr__(key, value == '1')
                elif repos:
                    # Associate value with most recently recorded repo
                    repos[-1].__setattr__(key, value)

        return repos

    def filter(self, state):
        '''
            Return a list of Repositories where state matches (null: all, enabled, disabled)
        '''
        if state is None or state == 'all':
            for repo in self.repos:
                yield repo

        elif state == 'enabled':
            for repo in self.repos:
                if repo.Enabled:
                    yield repo

        elif state == 'disabled':
            for repo in self.repos:
                if not repo.Enabled:
                    yield repo

    def list_stuff(self, stuff):
        l={}
        for repo in self.filter(stuff):
            id = repo.id
            id = id.replace("-", "_")
            l[id] = dict(id=repo.id, name=repo.name, enabled=repo.is_enabled, url=repo.url)
        return l

    def enable_only(self, id):
        changed = False
        to_enable = []
        to_disable = []

        # no repo id => disable all
        if len(id) == 0:
            self.disable_all()
            changed = True
            return [changed, dict(enabled=[], disabled='*')]

        # where are we now?
        current_repos=self.list_stuff('all')

        notice("redhat_repository: enable_only: changed=%s" % str(current_repos))
        for r in current_repos.keys():
            notice("redhat_repository: enable_only: **loop** id=%s r=%s" % (str(id), str(r)))

            if current_repos[r]['enabled'] and current_repos[r]['id'] not in id:
                to_disable.append(current_repos[r]['id'])
                changed = True

            if not current_repos[r]['enabled'] and current_repos[r]['id'] in id:
                to_enable.append(current_repos[r]['id'])
                changed = True

        notice("redhat_repository: enable_only: changed=%s" % str(changed))
        notice("redhat_repository: enable_only: to_enable=%s" % str(to_enable))
        notice("redhat_repository: enable_only: to_disable=%s" % str(to_disable))

        if changed:
            args = "subscription-manager repos "
            for n in to_disable:
                args += " --disable=" + n

            for n in to_enable:
                args += " --enable=" + n

            notice("redhat_repository: enable_only repos args: %s" % str(args))
            rc, stdout, stderr = self.module.run_command(args, check_rc=True)

        return [changed, dict(enabled=to_enable, disabled=to_disable)]

    def enablerepo(self, id):
        if len(id) > 0:
            args = "subscription-manager repos "
            for n in id:
                args += " --enable=" + n
            notice("redhat_repository: enable repos args: %s" % str(args))
            rc, stdout, stderr = self.module.run_command(args, check_rc=True)
            return True
        else:
            return False

    def disablerepo(self, id):
        if len(id) > 0:
            args = "subscription-manager repos "
            for n in id:
                args += " --disable=" + n
            notice("redhat_repository: disable repos args: %s" % str(args))
            rc, stdout, stderr = self.module.run_command(args, check_rc=True)
            return True
        else:
            return False

    def disable_all(self):
        notice("redhat_repository: disable all repos")
        args = "subscription-manager repos --disable='*'"
        rc, stdout, stderr = self.module.run_command(args, check_rc=True)


def main():
    #
    # Initialise Ansible module
    #
    module = AnsibleModule(
        argument_spec = dict(
            id      = dict(type="list"),
            # can't set a default='all' on list, otherwise id will never be used to enable/disable repos
            list    = dict(choices=['all', 'enabled', 'disabled']),
            mode    = dict(choices=['idempotent', 'incremental']),
            state   = dict(choices=['enabled', 'disabled']),
        ),
        required_one_of = [['id', 'list']],
        mutually_exclusive = [['id', 'list']],
        supports_check_mode = False,
    )

    #
    # Initialize RhsmRepositories
    #
    rhsmrepos = RhsmRepositories(module)

    p_list = module.params['list']
    p_id = module.params['id']
    p_state = module.params['state']
    p_mode = module.params['mode']

    # setting the default here, because if done at the AnsibleModule declaration, it screws things up
    if p_mode is None:
        p_mode = 'idempotent'

    notice("redhat_repository: in main | list=%s | id=%s | state=%s | mode=%s" %
        (str(p_list), str(p_id) , str(p_state), str(p_mode)))

    if p_list is not None:
        notice("redhat_repository: in main, list is not None")
        if p_list in ['all', 'enabled', 'disabled']:
            result = rhsmrepos.list_stuff(p_list)
            module.exit_json(changed=False, redhat_repositories=result)
        else:
            # we shouldn't reach this with Ansible.
            module.exit_json(changed=False, error="Unknown list primitive")

    elif p_id is not None:
        notice("redhat_repository: in main, id is not None")
        has_changed = False
        changed_repos = {}

        if p_mode == 'idempotent':
            if p_state == 'enabled':
                (has_changed, changed_repos) = rhsmrepos.enable_only(p_id)
            else:
                module.exit_json(changed=False, error="Can't use state=disabled in idempotent mode")

        elif p_mode == 'incremental':
            if p_state == 'enabled':
                has_changed = rhsmrepos.enablerepo(p_id)
                changed_repos['enabled'] = p_id
            elif p_state == 'disabled':
                has_changed = rhsmrepos.disablerepo(p_id)
                changed_repos['disabled'] = p_id

        changed_repos.setdefault('enabled', [])
        changed_repos.setdefault('disabled', [])
        module.exit_json(
            changed=has_changed,
            state=p_state,
            id=p_id,
            enabled=changed_repos['enabled'],
            disabled=changed_repos['disabled']
        )


if __name__ == '__main__':
    main()
