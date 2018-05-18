#!/usr/bin/python
# encoding: utf-8

# (c) 2015-2016, Jiri Tyr <jiri.tyr@gmail.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['stableinterface'],
    'supported_by': 'core'
}

DOCUMENTATION = '''
---
module: yum_repository
author: Jiri Tyr (@jtyr)
version_added: '2.1'
short_description: Add or remove YUM repositories
description:
  - Add or remove YUM repositories in RPM-based Linux distributions.

options:
  async:
    description:
      - If set to C(yes) Yum will download packages and metadata from this
        repo in parallel, if possible.
    type: bool
    default: 'yes'
  bandwidth:
    description:
      - Maximum available network bandwidth in bytes/second. Used with the
        I(throttle) option.
      - If I(throttle) is a percentage and bandwidth is C(0) then bandwidth
        throttling will be disabled. If I(throttle) is expressed as a data rate
        (bytes/sec) then this option is ignored. Default is C(0) (no bandwidth
        throttling).
    default: 0
  baseurl:
    description:
      - URL to the directory where the yum repository's 'repodata' directory
        lives.
      - It can also be a list of multiple URLs.
      - This, the I(metalink) or I(mirrorlist) parameters are required if I(state) is set to
        C(present).
  cost:
    description:
      - Relative cost of accessing this repository. Useful for weighing one
        repo's packages as greater/less than any other.
    default: 1000
  deltarpm_metadata_percentage:
    description:
      - When the relative size of deltarpm metadata vs pkgs is larger than
        this, deltarpm metadata is not downloaded from the repo. Note that you
        can give values over C(100), so C(200) means that the metadata is
        required to be half the size of the packages. Use C(0) to turn off
        this check, and always download metadata.
    default: 100
  deltarpm_percentage:
    description:
      - When the relative size of delta vs pkg is larger than this, delta is
        not used. Use C(0) to turn off delta rpm processing. Local repositories
        (with file:// I(baseurl)) have delta rpms turned off by default.
    default: 75
  description:
    description:
      - A human readable string describing the repository.
      - This parameter is only required if I(state) is set to C(present).
  enabled:
    description:
      - This tells yum whether or not use this repository.
    type: bool
    default: 'yes'
  enablegroups:
    description:
      - Determines whether yum will allow the use of package groups for this
        repository.
    type: bool
    default: 'yes'
  exclude:
    description:
      - List of packages to exclude from updates or installs. This should be a
        space separated list. Shell globs using wildcards (eg. C(*) and C(?))
        are allowed.
      - The list can also be a regular YAML array.
  failovermethod:
    choices: [roundrobin, priority]
    default: roundrobin
    description:
      - C(roundrobin) randomly selects a URL out of the list of URLs to start
        with and proceeds through each of them as it encounters a failure
        contacting the host.
      - C(priority) starts from the first I(baseurl) listed and reads through
        them sequentially.
  file:
    description:
      - File name without the C(.repo) extension to save the repo in. Defaults
        to the value of I(name).
  gpgcakey:
    description:
      - A URL pointing to the ASCII-armored CA key file for the repository.
  gpgcheck:
    description:
      - Tells yum whether or not it should perform a GPG signature check on
        packages.
    type: bool
  gpgkey:
    description:
      - A URL pointing to the ASCII-armored GPG key file for the repository.
      - It can also be a list of multiple URLs.
  http_caching:
    description:
      - Determines how upstream HTTP caches are instructed to handle any HTTP
        downloads that Yum does.
      - C(all) means that all HTTP downloads should be cached.
      - C(packages) means that only RPM package downloads should be cached (but
         not repository metadata downloads).
      - C(none) means that no HTTP downloads should be cached.
    choices: [all, packages, none]
    default: all
  include:
    description:
      - Include external configuration file. Both, local path and URL is
        supported. Configuration file will be inserted at the position of the
        I(include=) line. Included files may contain further include lines.
        Yum will abort with an error if an inclusion loop is detected.
  includepkgs:
    description:
      - List of packages you want to only use from a repository. This should be
        a space separated list. Shell globs using wildcards (eg. C(*) and C(?))
        are allowed. Substitution variables (e.g. C($releasever)) are honored
        here.
      - The list can also be a regular YAML array.
  ip_resolve:
    description:
      - Determines how yum resolves host names.
      - C(4) or C(IPv4) - resolve to IPv4 addresses only.
      - C(6) or C(IPv6) - resolve to IPv6 addresses only.
    choices: [4, 6, IPv4, IPv6, whatever]
    default: whatever
  keepalive:
    description:
      - This tells yum whether or not HTTP/1.1 keepalive should be used with
        this repository. This can improve transfer speeds by using one
        connection when downloading multiple files from a repository.
    type: bool
    default: 'no'
  keepcache:
    description:
      - Either C(1) or C(0). Determines whether or not yum keeps the cache of
        headers and packages after successful installation.
    choices: ['0', '1']
    default: '1'
  metadata_expire:
    description:
      - Time (in seconds) after which the metadata will expire.
      - Default value is 6 hours.
    default: 21600
  metadata_expire_filter:
    description:
      - Filter the I(metadata_expire) time, allowing a trade of speed for
        accuracy if a command doesn't require it. Each yum command can specify
        that it requires a certain level of timeliness quality from the remote
        repos. from "I'm about to install/upgrade, so this better be current"
        to "Anything that's available is good enough".
      - C(never) - Nothing is filtered, always obey I(metadata_expire).
      - C(read-only:past) - Commands that only care about past information are
        filtered from metadata expiring. Eg. I(yum history) info (if history
        needs to lookup anything about a previous transaction, then by
        definition the remote package was available in the past).
      - C(read-only:present) - Commands that are balanced between past and
        future. Eg. I(yum list yum).
      - C(read-only:future) - Commands that are likely to result in running
        other commands which will require the latest metadata. Eg.
        I(yum check-update).
      - Note that this option does not override "yum clean expire-cache".
    choices: [never, 'read-only:past', 'read-only:present', 'read-only:future']
    default: 'read-only:present'
  metalink:
    description:
      - Specifies a URL to a metalink file for the repomd.xml, a list of
        mirrors for the entire repository are generated by converting the
        mirrors for the repomd.xml file to a I(baseurl).
      - This, the I(baseurl) or I(mirrorlist) parameters are required if I(state) is set to
        C(present).
  mirrorlist:
    description:
      - Specifies a URL to a file containing a list of baseurls.
      - This, the I(baseurl) or I(metalink) parameters are required if I(state) is set to
        C(present).
  mirrorlist_expire:
    description:
      - Time (in seconds) after which the mirrorlist locally cached will
        expire.
      - Default value is 6 hours.
    default: 21600
  name:
    description:
      - Unique repository ID.
      - This parameter is only required if I(state) is set to C(present) or
        C(absent).
    required: true
  password:
    description:
      - Password to use with the username for basic authentication.
  priority:
    description:
      - Enforce ordered protection of repositories. The value is an integer
        from 1 to 99.
      - This option only works if the YUM Priorities plugin is installed.
    default: 99
  protect:
    description:
      - Protect packages from updates from other repositories.
    type: bool
    default: 'no'
  proxy:
    description:
      - URL to the proxy server that yum should use. Set to C(_none_) to
        disable the global proxy setting.
  proxy_password:
    description:
      - Username to use for proxy.
  proxy_username:
    description:
      - Password for this proxy.
  repo_gpgcheck:
    description:
      - This tells yum whether or not it should perform a GPG signature check
        on the repodata from this repository.
    type: bool
    default: 'no'
  reposdir:
    description:
      - Directory where the C(.repo) files will be stored.
    default: /etc/yum.repos.d
  retries:
    description:
      - Set the number of times any attempt to retrieve a file should retry
        before returning an error. Setting this to C(0) makes yum try forever.
    default: 10
  s3_enabled:
    description:
      - Enables support for S3 repositories.
      - This option only works if the YUM S3 plugin is installed.
    type: bool
    default: 'no'
  skip_if_unavailable:
    description:
      - If set to C(yes) yum will continue running if this repository cannot be
        contacted for any reason. This should be set carefully as all repos are
        consulted for any given command.
    type: bool
    default: 'no'
  ssl_check_cert_permissions:
    description:
      - Whether yum should check the permissions on the paths for the
        certificates on the repository (both remote and local).
      - If we can't read any of the files then yum will force
        I(skip_if_unavailable) to be C(yes). This is most useful for non-root
        processes which use yum on repos that have client cert files which are
        readable only by root.
    type: bool
    default: 'no'
  sslcacert:
    description:
      - Path to the directory containing the databases of the certificate
        authorities yum should use to verify SSL certificates.
  sslclientcert:
    description:
      - Path to the SSL client certificate yum should use to connect to
        repos/remote sites.
  sslclientkey:
    description:
      - Path to the SSL client key yum should use to connect to repos/remote
        sites.
  sslverify:
    description:
      - Defines whether yum should verify SSL certificates/hosts at all.
    type: bool
    default: 'yes'
  state:
    description:
      - State of the repo file.
    choices: [absent, present]
    default: present
  throttle:
    description:
      - Enable bandwidth throttling for downloads.
      - This option can be expressed as a absolute data rate in bytes/sec. An
        SI prefix (k, M or G) may be appended to the bandwidth value.
  timeout:
    description:
      - Number of seconds to wait for a connection before timing out.
    default: 30
  ui_repoid_vars:
    description:
      - When a repository id is displayed, append these yum variables to the
        string if they are used in the I(baseurl)/etc. Variables are appended
        in the order listed (and found).
    default: releasever basearch
  username:
    description:
      - Username to use for basic authentication to a repo or really any url.

extends_documentation_fragment:
  - files

notes:
  - All comments will be removed if modifying an existing repo file.
  - Section order is preserved in an existing repo file.
  - Parameters in a section are ordered alphabetically in an existing repo
    file.
  - The repo file will be automatically deleted if it contains no repository.
  - When removing a repository, beware that the metadata cache may still remain
    on disk until you run C(yum clean all). Use a notification handler for this.
  - "The C(params) parameter was removed in Ansible 2.5 due to circumventing Ansible's parameter
    handling"
'''

EXAMPLES = '''
- name: Add repository
  yum_repository:
    name: epel
    description: EPEL YUM repo
    baseurl: https://download.fedoraproject.org/pub/epel/$releasever/$basearch/

- name: Add multiple repositories into the same file (1/2)
  yum_repository:
    name: epel
    description: EPEL YUM repo
    file: external_repos
    baseurl: https://download.fedoraproject.org/pub/epel/$releasever/$basearch/
    gpgcheck: no

- name: Add multiple repositories into the same file (2/2)
  yum_repository:
    name: rpmforge
    description: RPMforge YUM repo
    file: external_repos
    baseurl: http://apt.sw.be/redhat/el7/en/$basearch/rpmforge
    mirrorlist: http://mirrorlist.repoforge.org/el7/mirrors-rpmforge
    enabled: no

# Handler showing how to clean yum metadata cache
- name: yum-clean-metadata
  command: yum clean metadata
  args:
    warn: no

# Example removing a repository and cleaning up metadata cache
- name: Remove repository (and clean up left-over metadata)
  yum_repository:
    name: epel
    state: absent
  notify: yum-clean-metadata

- name: Remove repository from a specific repo file
  yum_repository:
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

import os

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves import configparser
from ansible.module_utils._text import to_native


class YumRepo(object):
    # Class global variables
    module = None
    params = None
    section = None
    repofile = configparser.RawConfigParser()

    # List of parameters which will be allowed in the repo file output
    allowed_params = [
        'async',
        'bandwidth',
        'baseurl',
        'cost',
        'deltarpm_metadata_percentage',
        'deltarpm_percentage',
        'enabled',
        'enablegroups',
        'exclude',
        'failovermethod',
        'gpgcakey',
        'gpgcheck',
        'gpgkey',
        'http_caching',
        'include',
        'includepkgs',
        'ip_resolve',
        'keepalive',
        'keepcache',
        'metadata_expire',
        'metadata_expire_filter',
        'metalink',
        'mirrorlist',
        'mirrorlist_expire',
        'name',
        'password',
        'priority',
        'protect',
        'proxy',
        'proxy_password',
        'proxy_username',
        'repo_gpgcheck',
        'retries',
        's3_enabled',
        'skip_if_unavailable',
        'sslcacert',
        'ssl_check_cert_permissions',
        'sslclientcert',
        'sslclientkey',
        'sslverify',
        'throttle',
        'timeout',
        'ui_repoid_vars',
        'username']

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
                msg="Repo directory '%s' does not exist." % repos_dir)

        # Set dest; also used to set dest parameter for the FS attributes
        self.params['dest'] = os.path.join(
            repos_dir, "%s.repo" % self.params['file'])

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
        req_params = (self.params['baseurl'], self.params['metalink'], self.params['mirrorlist'])
        if req_params == (None, None, None):
            self.module.fail_json(
                msg="Parameter 'baseurl', 'metalink' or 'mirrorlist' is required for "
                    "adding a new repo.")

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
                fd = open(self.params['dest'], 'w')
            except IOError as e:
                self.module.fail_json(
                    msg="Cannot open repo file %s." % self.params['dest'],
                    details=to_native(e))

            self.repofile.write(fd)

            try:
                fd.close()
            except IOError as e:
                self.module.fail_json(
                    msg="Cannot write repo file %s." % self.params['dest'],
                    details=to_native(e))
        else:
            # Remove the file if there are not repos
            try:
                os.remove(self.params['dest'])
            except OSError as e:
                self.module.fail_json(
                    msg=(
                        "Cannot remove empty repo file %s." %
                        self.params['dest']),
                    details=to_native(e))

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
    argument_spec = dict(
        bandwidth=dict(),
        baseurl=dict(type='list'),
        cost=dict(),
        deltarpm_metadata_percentage=dict(),
        deltarpm_percentage=dict(),
        description=dict(),
        enabled=dict(type='bool'),
        enablegroups=dict(type='bool'),
        exclude=dict(type='list'),
        failovermethod=dict(choices=['roundrobin', 'priority']),
        file=dict(),
        gpgcakey=dict(),
        gpgcheck=dict(type='bool'),
        gpgkey=dict(type='list'),
        http_caching=dict(choices=['all', 'packages', 'none']),
        include=dict(),
        includepkgs=dict(type='list'),
        ip_resolve=dict(choices=['4', '6', 'IPv4', 'IPv6', 'whatever']),
        keepalive=dict(type='bool'),
        keepcache=dict(choices=['0', '1']),
        metadata_expire=dict(),
        metadata_expire_filter=dict(
            choices=[
                'never',
                'read-only:past',
                'read-only:present',
                'read-only:future']),
        metalink=dict(),
        mirrorlist=dict(),
        mirrorlist_expire=dict(),
        name=dict(required=True),
        params=dict(type='dict'),
        password=dict(no_log=True),
        priority=dict(),
        protect=dict(type='bool'),
        proxy=dict(),
        proxy_password=dict(no_log=True),
        proxy_username=dict(),
        repo_gpgcheck=dict(type='bool'),
        reposdir=dict(default='/etc/yum.repos.d', type='path'),
        retries=dict(),
        s3_enabled=dict(type='bool'),
        skip_if_unavailable=dict(type='bool'),
        sslcacert=dict(),
        ssl_check_cert_permissions=dict(type='bool'),
        sslclientcert=dict(),
        sslclientkey=dict(),
        sslverify=dict(type='bool'),
        state=dict(choices=['present', 'absent'], default='present'),
        throttle=dict(),
        timeout=dict(),
        ui_repoid_vars=dict(),
        username=dict(),
    )

    argument_spec['async'] = dict(type='bool')

    module = AnsibleModule(
        argument_spec=argument_spec,
        add_file_common_args=True,
        supports_check_mode=True,
    )

    # Params was removed
    # https://meetbot.fedoraproject.org/ansible-meeting/2017-09-28/ansible_dev_meeting.2017-09-28-15.00.log.html
    if module.params['params']:
        module.fail_json(msg="The params option to yum_repository was removed in Ansible 2.5"
                         "since it circumvents Ansible's option handling")

    name = module.params['name']
    state = module.params['state']

    # Check if required parameters are present
    if state == 'present':
        if (
                module.params['baseurl'] is None and
                module.params['metalink'] is None and
                module.params['mirrorlist'] is None):
            module.fail_json(
                msg="Parameter 'baseurl', 'metalink' or 'mirrorlist' is required.")
        if module.params['description'] is None:
            module.fail_json(
                msg="Parameter 'description' is required.")

    # Rename "name" and "description" to ensure correct key sorting
    module.params['repoid'] = module.params['name']
    module.params['name'] = module.params['description']
    del module.params['description']

    # Change list type to string for baseurl and gpgkey
    for list_param in ['baseurl', 'gpgkey']:
        if (
                list_param in module.params and
                module.params[list_param] is not None):
            module.params[list_param] = "\n".join(module.params[list_param])

    # Define repo file name if it doesn't exist
    if module.params['file'] is None:
        module.params['file'] = module.params['repoid']

    # Instantiate the YumRepo object
    yumrepo = YumRepo(module)

    # Get repo status before change
    diff = {
        'before_header': yumrepo.params['dest'],
        'before': yumrepo.dump(),
        'after_header': yumrepo.params['dest'],
        'after': ''
    }

    # Perform action depending on the state
    if state == 'present':
        yumrepo.add()
    elif state == 'absent':
        yumrepo.remove()

    # Get repo status after change
    diff['after'] = yumrepo.dump()

    # Compare repo states
    changed = diff['before'] != diff['after']

    # Save the file only if not in check mode and if there was a change
    if not module.check_mode and changed:
        yumrepo.save()

    # Change file attributes if needed
    if os.path.isfile(module.params['dest']):
        file_args = module.load_file_common_arguments(module.params)
        changed = module.set_fs_attributes_if_different(file_args, changed)

    # Print status of the change
    module.exit_json(changed=changed, repo=name, state=state, diff=diff)


if __name__ == '__main__':
    main()
