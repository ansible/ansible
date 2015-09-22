#!/usr/bin/python
# encoding: utf-8

# (c) 2015, Jiri Tyr <jiri.tyr@gmail.com>
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


import ConfigParser
import os


DOCUMENTATION = '''
---
module: yumrepo
author: Jiri Tyr (@jtyr)
version_added: '2.0'
short_description: Add and remove YUM repositories
description:
  - Add or remove YUM repositories in RPM-based Linux distributions.

options:
  bandwidth:
    required: false
    default: 0
    description:
      - Maximum available network bandwidth in bytes/second. Used with the
        I(throttle) option.
      - If I(throttle) is a percentage and bandwidth is C(0) then bandwidth
        throttling will be disabled. If I(throttle) is expressed as a data rate
        (bytes/sec) then this option is ignored. Default is C(0) (no bandwidth
        throttling).
  baseurl:
    required: false
    default: None
    description:
      - URL to the directory where the yum repository's 'repodata' directory
        lives.
      - This or the I(mirrorlist) parameter is required.
  cost:
    required: false
    default: 1000
    description:
      - Relative cost of accessing this repository. Useful for weighing one
        repo's packages as greater/less than any other.
  description:
    required: false
    default: None
    description:
      - A human readable string describing the repository.
  enabled:
    required: false
    choices: ['yes', 'no']
    default: 'yes'
    description:
      - This tells yum whether or not use this repository.
  enablegroups:
    required: false
    choices: ['yes', 'no']
    default: 'yes'
    description:
      - Determines whether yum will allow the use of package groups for this
        repository.
  exclude:
    required: false
    default: None
    description:
      - List of packages to exclude from updates or installs. This should be a
        space separated list. Shell globs using wildcards (eg. C(*) and C(?))
        are allowed.
      - The list can also be a regular YAML array.
  failovermethod:
    required: false
    choices: [roundrobin, priority]
    default: roundrobin
    description:
      - C(roundrobin) randomly selects a URL out of the list of URLs to start
        with and proceeds through each of them as it encounters a failure
        contacting the host.
      - C(priority) starts from the first baseurl listed and reads through them
        sequentially.
  file:
    required: false
    default: None
    description:
      - File to use to save the repo in. Defaults to the value of I(name).
  gpgcakey:
    required: false
    default: None
    description:
      - A URL pointing to the ASCII-armored CA key file for the repository.
  gpgcheck:
    required: false
    choices: ['yes', 'no']
    default: 'no'
    description:
      - Tells yum whether or not it should perform a GPG signature check on
        packages.
  gpgkey:
    required: false
    default: None
    description:
      - A URL pointing to the ASCII-armored GPG key file for the repository.
  http_caching:
    required: false
    choices: [all, packages, none]
    default: all
    description:
      - Determines how upstream HTTP caches are instructed to handle any HTTP
        downloads that Yum does.
      - C(all) means that all HTTP downloads should be cached.
      - C(packages) means that only RPM package downloads should be cached (but
         not repository metadata downloads).
      - C(none) means that no HTTP downloads should be cached.
  includepkgs:
    required: false
    default: None
    description:
      - List of packages you want to only use from a repository. This should be
        a space separated list. Shell globs using wildcards (eg. C(*) and C(?))
        are allowed. Substitution variables (e.g. C($releasever)) are honored
        here.
      - The list can also be a regular YAML array.
  keepalive:
    required: false
    choices: ['yes', 'no']
    default: 'no'
    description:
      - This tells yum whether or not HTTP/1.1 keepalive should be used with
        this repository. This can improve transfer speeds by using one
        connection when downloading multiple files from a repository.
  metadata_expire:
    required: false
    default: 21600
    description:
      - Time (in seconds) after which the metadata will expire.
      - Default value is 6 hours.
  metalink:
    required: false
    default: None
    description:
      - Specifies a URL to a metalink file for the repomd.xml, a list of
        mirrors for the entire repository are generated by converting the
        mirrors for the repomd.xml file to a baseurl.
  mirrorlist:
    required: false
    default: None
    description:
      - Specifies a URL to a file containing a list of baseurls.
      - This or the I(baseurl) parameter is required.
  mirrorlist_expire:
    required: false
    default: 21600
    description:
      - Time (in seconds) after which the mirrorlist locally cached will
        expire.
      - Default value is 6 hours.
  name:
    required: true
    description:
      - Unique repository ID.
  password:
    required: false
    default: None
    description:
      - Password to use with the username for basic authentication.
  protect:
    required: false
    choices: ['yes', 'no']
    default: 'no'
    description:
      - Protect packages from updates from other repositories.
  proxy:
    required: false
    default: None
    description:
      - URL to the proxy server that yum should use.
  proxy_password:
    required: false
    default: None
    description:
      - Username to use for proxy.
  proxy_username:
    required: false
    default: None
    description:
      - Password for this proxy.
  repo_gpgcheck:
    required: false
    choices: ['yes', 'no']
    default: 'no'
    description:
      - This tells yum whether or not it should perform a GPG signature check
        on the repodata from this repository.
  reposdir:
    required: false
    default: /etc/yum.repos.d
    description:
      - Directory where the C(.repo) files will be stored.
  retries:
    required: false
    default: 10
    description:
      - Set the number of times any attempt to retrieve a file should retry
        before returning an error. Setting this to C(0) makes yum try forever.
  skip_if_unavailable:
    required: false
    choices: ['yes', 'no']
    default: 'no'
    description:
      - If set to C(yes) yum will continue running if this repository cannot be
        contacted for any reason. This should be set carefully as all repos are
        consulted for any given command.
  sslcacert:
    required: false
    default: None
    description:
      - Path to the directory containing the databases of the certificate
        authorities yum should use to verify SSL certificates.
  ssl_check_cert_permissions:
    required: false
    choices: ['yes', 'no']
    default: 'no'
    description:
      - Whether yum should check the permissions on the paths for the
        certificates on the repository (both remote and local).
      - If we can't read any of the files then yum will force
        I(skip_if_unavailable) to be true. This is most useful for non-root
        processes which use yum on repos that have client cert files which are
        readable only by root.
  sslclientcert:
    required: false
    default: None
    description:
      - Path to the SSL client certificate yum should use to connect to
        repos/remote sites.
  sslclientkey:
    required: false
    default: None
    description:
      - Path to the SSL client key yum should use to connect to repos/remote
        sites.
  sslverify:
    required: false
    choices: ['yes', 'no']
    default: 'yes'
    description:
      - Defines whether yum should verify SSL certificates/hosts at all.
  state:
    required: false
    choices: [absent, present]
    default: present
    description:
      - A source string state.
  throttle:
    required: false
    default: None
    description:
      - Enable bandwidth throttling for downloads.
      - This option can be expressed as a absolute data rate in bytes/sec. An
        SI prefix (k, M or G) may be appended to the bandwidth value.
  timeout:
    required: false
    default: 30
    description:
      - Number of seconds to wait for a connection before timing out.
  username:
    required: false
    default: None
    description:
      - Username to use for basic authentication to a repo or really any url.

extends_documentation_fragment: files

notes:
  - All comments will be removed if modifying an existing repo file.
  - Section order is preserved in an existing repo file.
  - Parameters in a section are ordered alphabetically in an existing repo
    file.
  - The repo file will be automatically deleted if it contains no repository.
'''

EXAMPLES = '''
- name: Add repository
  yumrepo:
    name: epel
    description: EPEL YUM repo
    baseurl: http://download.fedoraproject.org/pub/epel/$releasever/$basearch/

- name: Add multiple repositories into the same file (1/2)
  yumrepo:
    name: epel
    description: EPEL YUM repo
    file: external_repos
    baseurl: http://download.fedoraproject.org/pub/epel/$releasever/$basearch/
    gpgcheck: no
- name: Add multiple repositories into the same file (2/2)
  yumrepo:
    name: rpmforge
    description: RPMforge YUM repo
    file: external_repos
    baseurl: http://apt.sw.be/redhat/el7/en/$basearch/rpmforge
    mirrorlist: http://mirrorlist.repoforge.org/el7/mirrors-rpmforge
    enabled: no

- name: Remove repository
  yumrepo:
    name: epel
    state: absent

- name: Remove repository from a specific repo file
  yumrepo:
    name: epel
    file: external_repos
    state: absent
'''

RETURN = '''
repo:
    description: repository name
    returned: success
    type: string
    sample: "epel"
state:
    description: state of the target, after execution
    returned: success
    type: string
    sample: "present"
'''


class YumRepo(object):
    # Class global variables
    module = None
    params = None
    section = None
    repofile = ConfigParser.RawConfigParser()

    # List of parameters which will be allowed in the repo file output
    allowed_params = [
        'bandwidth', 'baseurl', 'cost', 'enabled', 'enablegroups', 'exclude',
        'failovermethod', 'gpgcakey', 'gpgcheck', 'gpgkey', 'http_caching',
        'includepkgs', 'keepalive', 'metadata_expire', 'metalink',
        'mirrorlist', 'mirrorlist_expire', 'name', 'password', 'protect',
        'proxy', 'proxy_password', 'proxy_username', 'repo_gpgcheck',
        'retries', 'skip_if_unavailable', 'sslcacert',
        'ssl_check_cert_permissions', 'sslclientcert', 'sslclientkey',
        'sslverify', 'throttle', 'timeout', 'username']

    # List of parameters which can be a list
    list_params = ['exclude', 'includepkgs']

    def __init__(self, module):
        # To be able to use fail_json
        self.module = module
        # Shortcut for the params
        self.params = self.module.params
        # Section is always the repoid
        self.section = self.params['repoid']

        # Check if repo directory exists
        repos_dir = self.params['reposdir']
        if not os.path.isdir(repos_dir):
            self.module.fail_json(
                msg='Repo directory "%s" does not exist.' % repos_dir)

        # Get the given or the default repo file name
        repo_file = self.params['repoid']
        if self.params['file'] is not None:
            repo_file = self.params['file']

        # Set dest; also used to set dest parameter for the FS attributes
        self.params['dest'] = os.path.join(repos_dir, "%s.repo" % repo_file)

        # Read the repo file if it exists
        if os.path.isfile(self.params['dest']):
            self.repofile.read(self.params['dest'])

    def add(self):
        # Remove already existing repo and create a new one
        if self.repofile.has_section(self.section):
            self.repofile.remove_section(self.section)

        # Add section
        self.repofile.add_section(self.section)

        # Baseurl/mirrorlist is not required because for removal we need only
        # the repo name. This is why we check if the baseurl/mirrorlist is
        # defined.
        if (self.params['baseurl'], self.params['mirrorlist']) == (None, None):
            self.module.fail_json(
                msg='Paramater "baseurl" or "mirrorlist" is required for '
                'adding a new repo.')

        # Set options
        for key, value in sorted(self.params.items()):
            if key in self.list_params and isinstance(value, list):
                # Join items into one string for specific parameters
                value = ' '.join(value)
            elif isinstance(value, bool):
                # Convert boolean value to integer
                value = int(value)

            # Set the value only if it was defined (default is None)
            if value is not None and key in self.allowed_params:
                self.repofile.set(self.section, key, value)

    def save(self):
        if len(self.repofile.sections()):
            # Write data into the file
            try:
                fd = open(self.params['dest'], 'wb')
            except IOError:
                self.module.fail_json(
                    msg='Cannot open repo file %s.' %
                    self.params['dest'])

            try:
                try:
                    self.repofile.write(fd)
                except Error:
                    self.module.fail_json(
                        msg='Cannot write repo file %s.' %
                        self.params['dest'])
            finally:
                fd.close()
        else:
            # Remove the file if there are not repos
            try:
                os.remove(self.params['dest'])
            except OSError:
                self.module.fail_json(
                    msg='Cannot remove empty repo file %s.' %
                    self.params['dest'])

    def remove(self):
        # Remove section if exists
        if self.repofile.has_section(self.section):
            self.repofile.remove_section(self.section)

    def dump(self):
        repo_string = ""

        # Compose the repo file
        for section in sorted(self.repofile.sections()):
            repo_string += "[%s]\n" % section

            for key, value in sorted(self.repofile.items(section)):
                repo_string += "%s = %s\n" % (key, value)

            repo_string += "\n"

        return repo_string


def main():
    # Module settings
    module = AnsibleModule(
        argument_spec=dict(
            bandwidth=dict(),
            baseurl=dict(),
            cost=dict(),
            description=dict(),
            enabled=dict(type='bool'),
            enablegroups=dict(type='bool'),
            exclude=dict(),
            failovermethod=dict(choices=['roundrobin', 'priority']),
            file=dict(),
            gpgcakey=dict(),
            gpgcheck=dict(type='bool'),
            gpgkey=dict(),
            http_caching=dict(choices=['all', 'packages', 'none']),
            includepkgs=dict(),
            keepalive=dict(type='bool'),
            metadata_expire=dict(),
            metalink=dict(),
            mirrorlist=dict(),
            mirrorlist_expire=dict(),
            name=dict(required=True),
            password=dict(no_log=True),
            protect=dict(type='bool'),
            proxy=dict(),
            proxy_password=dict(no_log=True),
            proxy_username=dict(),
            repo_gpgcheck=dict(type='bool'),
            reposdir=dict(default='/etc/yum.repos.d'),
            retries=dict(),
            skip_if_unavailable=dict(type='bool'),
            sslcacert=dict(),
            ssl_check_cert_permissions=dict(type='bool'),
            sslclientcert=dict(),
            sslclientkey=dict(),
            sslverify=dict(type='bool'),
            state=dict(choices=['present', 'absent'], default='present'),
            throttle=dict(),
            timeout=dict(),
            username=dict(),
        ),
        add_file_common_args=True,
        supports_check_mode=True,
    )

    name = module.params['name']
    state = module.params['state']

    # Rename "name" and "description" to ensure correct key sorting
    module.params['repoid'] = module.params['name']
    module.params['name'] = module.params['description']
    del module.params['description']

    # Instantiate the YumRepo object
    yumrepo = YumRepo(module)

    # Get repo status before change
    yumrepo_before = yumrepo.dump()

    # Perform action depending on the state
    if state == 'present':
        yumrepo.add()
    elif state == 'absent':
        yumrepo.remove()

    # Get repo status after change
    yumrepo_after = yumrepo.dump()

    # Compare repo states
    changed = yumrepo_before != yumrepo_after

    # Save the file only if not in check mode and if there was a change
    if not module.check_mode and changed:
        yumrepo.save()

    # Change file attributes if needed
    if os.path.isfile(module.params['dest']):
        file_args = module.load_file_common_arguments(module.params)
        changed = module.set_fs_attributes_if_different(file_args, changed)

    # Print status of the change
    module.exit_json(changed=changed, repo=name, state=state)


# Import module snippets
from ansible.module_utils.basic import *


if __name__ == '__main__':
    main()
