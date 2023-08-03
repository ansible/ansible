# encoding: utf-8

# (c) 2015-2016, Jiri Tyr <jiri.tyr@gmail.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: yum_repository
author: Jiri Tyr (@jtyr)
version_added: '2.1'
short_description: Add or remove YUM repositories
description:
  - Add or remove YUM repositories in RPM-based Linux distributions.
  - If you wish to update an existing repository definition use M(community.general.ini_file) instead.

options:
  async:
    description:
      - If set to V(true) Yum will download packages and metadata from this
        repo in parallel, if possible.
      - In ansible-core 2.11, 2.12, and 2.13 the default value is V(true).
      - This option has been deprecated in RHEL 8. If you're using one of the
        versions listed above, you can set this option to None to avoid passing an
        unknown configuration option.
    type: bool
  bandwidth:
    description:
      - Maximum available network bandwidth in bytes/second. Used with the
        O(throttle) option.
      - If O(throttle) is a percentage and bandwidth is V(0) then bandwidth
        throttling will be disabled. If O(throttle) is expressed as a data rate
        (bytes/sec) then this option is ignored. Default is V(0) (no bandwidth
        throttling).
    type: str
  baseurl:
    description:
      - URL to the directory where the yum repository's 'repodata' directory
        lives.
      - It can also be a list of multiple URLs.
      - This, the O(metalink) or O(mirrorlist) parameters are required if O(state) is set to
        V(present).
    type: list
    elements: str
  cost:
    description:
      - Relative cost of accessing this repository. Useful for weighing one
        repo's packages as greater/less than any other.
    type: str
  deltarpm_metadata_percentage:
    description:
      - When the relative size of deltarpm metadata vs pkgs is larger than
        this, deltarpm metadata is not downloaded from the repo. Note that you
        can give values over V(100), so V(200) means that the metadata is
        required to be half the size of the packages. Use V(0) to turn off
        this check, and always download metadata.
    type: str
  deltarpm_percentage:
    description:
      - When the relative size of delta vs pkg is larger than this, delta is
        not used. Use V(0) to turn off delta rpm processing. Local repositories
        (with file://O(baseurl)) have delta rpms turned off by default.
    type: str
  description:
    description:
      - A human readable string describing the repository. This option corresponds to the "name" property in the repo file.
      - This parameter is only required if O(state) is set to V(present).
    type: str
  enabled:
    description:
      - This tells yum whether or not use this repository.
      - Yum default value is V(true).
    type: bool
  enablegroups:
    description:
      - Determines whether yum will allow the use of package groups for this
        repository.
      - Yum default value is V(true).
    type: bool
  exclude:
    description:
      - List of packages to exclude from updates or installs. This should be a
        space separated list. Shell globs using wildcards (for example V(*) and V(?))
        are allowed.
      - The list can also be a regular YAML array.
    type: list
    elements: str
  failovermethod:
    choices: [roundrobin, priority]
    description:
      - V(roundrobin) randomly selects a URL out of the list of URLs to start
        with and proceeds through each of them as it encounters a failure
        contacting the host.
      - V(priority) starts from the first O(baseurl) listed and reads through
        them sequentially.
    type: str
  file:
    description:
      - File name without the C(.repo) extension to save the repo in. Defaults
        to the value of O(name).
    type: str
  gpgcakey:
    description:
      - A URL pointing to the ASCII-armored CA key file for the repository.
    type: str
  gpgcheck:
    description:
      - Tells yum whether or not it should perform a GPG signature check on
        packages.
      - No default setting. If the value is not set, the system setting from
        C(/etc/yum.conf) or system default of V(false) will be used.
    type: bool
  gpgkey:
    description:
      - A URL pointing to the ASCII-armored GPG key file for the repository.
      - It can also be a list of multiple URLs.
    type: list
    elements: str
  module_hotfixes:
    description:
      - Disable module RPM filtering and make all RPMs from the repository
        available. The default is V(None).
    version_added: '2.11'
    type: bool
  http_caching:
    description:
      - Determines how upstream HTTP caches are instructed to handle any HTTP
        downloads that Yum does.
      - V(all) means that all HTTP downloads should be cached.
      - V(packages) means that only RPM package downloads should be cached (but
         not repository metadata downloads).
      - V(none) means that no HTTP downloads should be cached.
    choices: [all, packages, none]
    type: str
  include:
    description:
      - Include external configuration file. Both, local path and URL is
        supported. Configuration file will be inserted at the position of the
        C(include=) line. Included files may contain further include lines.
        Yum will abort with an error if an inclusion loop is detected.
    type: str
  includepkgs:
    description:
      - List of packages you want to only use from a repository. This should be
        a space separated list. Shell globs using wildcards (for example V(*) and V(?))
        are allowed. Substitution variables (for example V($releasever)) are honored
        here.
      - The list can also be a regular YAML array.
    type: list
    elements: str
  ip_resolve:
    description:
      - Determines how yum resolves host names.
      - V(4) or V(IPv4) - resolve to IPv4 addresses only.
      - V(6) or V(IPv6) - resolve to IPv6 addresses only.
    choices: ['4', '6', IPv4, IPv6, whatever]
    type: str
  keepalive:
    description:
      - This tells yum whether or not HTTP/1.1 keepalive should be used with
        this repository. This can improve transfer speeds by using one
        connection when downloading multiple files from a repository.
    type: bool
  keepcache:
    description:
      - Either V(1) or V(0). Determines whether or not yum keeps the cache of
        headers and packages after successful installation.
      - This parameter is deprecated and will be removed in version 2.20.
    choices: ['0', '1']
    type: str
  metadata_expire:
    description:
      - Time (in seconds) after which the metadata will expire.
      - Default value is 6 hours.
    type: str
  metadata_expire_filter:
    description:
      - Filter the O(metadata_expire) time, allowing a trade of speed for
        accuracy if a command doesn't require it. Each yum command can specify
        that it requires a certain level of timeliness quality from the remote
        repos. from "I'm about to install/upgrade, so this better be current"
        to "Anything that's available is good enough".
      - V(never) - Nothing is filtered, always obey O(metadata_expire).
      - V(read-only:past) - Commands that only care about past information are
        filtered from metadata expiring. Eg. C(yum history) info (if history
        needs to lookup anything about a previous transaction, then by
        definition the remote package was available in the past).
      - V(read-only:present) - Commands that are balanced between past and
        future. Eg. C(yum list yum).
      - V(read-only:future) - Commands that are likely to result in running
        other commands which will require the latest metadata. Eg.
        C(yum check-update).
      - Note that this option does not override "yum clean expire-cache".
    choices: [never, 'read-only:past', 'read-only:present', 'read-only:future']
    type: str
  metalink:
    description:
      - Specifies a URL to a metalink file for the repomd.xml, a list of
        mirrors for the entire repository are generated by converting the
        mirrors for the repomd.xml file to a O(baseurl).
      - This, the O(baseurl) or O(mirrorlist) parameters are required if O(state) is set to
        V(present).
    type: str
  mirrorlist:
    description:
      - Specifies a URL to a file containing a list of baseurls.
      - This, the O(baseurl) or O(metalink) parameters are required if O(state) is set to
        V(present).
    type: str
  mirrorlist_expire:
    description:
      - Time (in seconds) after which the mirrorlist locally cached will
        expire.
      - Default value is 6 hours.
    type: str
  name:
    description:
      - Unique repository ID. This option builds the section name of the repository in the repo file.
      - This parameter is only required if O(state) is set to V(present) or
        V(absent).
    type: str
    required: true
  password:
    description:
      - Password to use with the username for basic authentication.
    type: str
  priority:
    description:
      - Enforce ordered protection of repositories. The value is an integer
        from 1 to 99.
      - This option only works if the YUM Priorities plugin is installed.
    type: str
  protect:
    description:
      - Protect packages from updates from other repositories.
    type: bool
  proxy:
    description:
      - URL to the proxy server that yum should use. Set to V(_none_) to
        disable the global proxy setting.
    type: str
  proxy_password:
    description:
      - Password for this proxy.
    type: str
  proxy_username:
    description:
      - Username to use for proxy.
    type: str
  repo_gpgcheck:
    description:
      - This tells yum whether or not it should perform a GPG signature check
        on the repodata from this repository.
    type: bool
  reposdir:
    description:
      - Directory where the C(.repo) files will be stored.
    type: path
    default: /etc/yum.repos.d
  retries:
    description:
      - Set the number of times any attempt to retrieve a file should retry
        before returning an error. Setting this to V(0) makes yum try forever.
    type: str
  s3_enabled:
    description:
      - Enables support for S3 repositories.
      - This option only works if the YUM S3 plugin is installed.
    type: bool
  skip_if_unavailable:
    description:
      - If set to V(true) yum will continue running if this repository cannot be
        contacted for any reason. This should be set carefully as all repos are
        consulted for any given command.
    type: bool
  ssl_check_cert_permissions:
    description:
      - Whether yum should check the permissions on the paths for the
        certificates on the repository (both remote and local).
      - If we can't read any of the files then yum will force
        O(skip_if_unavailable) to be V(true). This is most useful for non-root
        processes which use yum on repos that have client cert files which are
        readable only by root.
    type: bool
  sslcacert:
    description:
      - Path to the directory containing the databases of the certificate
        authorities yum should use to verify SSL certificates.
    type: str
    aliases: [ ca_cert ]
  sslclientcert:
    description:
      - Path to the SSL client certificate yum should use to connect to
        repos/remote sites.
    type: str
    aliases: [ client_cert ]
  sslclientkey:
    description:
      - Path to the SSL client key yum should use to connect to repos/remote
        sites.
    type: str
    aliases: [ client_key ]
  sslverify:
    description:
      - Defines whether yum should verify SSL certificates/hosts at all.
    type: bool
    aliases: [ validate_certs ]
  state:
    description:
      - State of the repo file.
    choices: [absent, present]
    type: str
    default: present
  throttle:
    description:
      - Enable bandwidth throttling for downloads.
      - This option can be expressed as a absolute data rate in bytes/sec. An
        SI prefix (k, M or G) may be appended to the bandwidth value.
    type: str
  timeout:
    description:
      - Number of seconds to wait for a connection before timing out.
    type: str
  ui_repoid_vars:
    description:
      - When a repository id is displayed, append these yum variables to the
        string if they are used in the O(baseurl)/etc. Variables are appended
        in the order listed (and found).
    type: str
  username:
    description:
      - Username to use for basic authentication to a repo or really any url.
    type: str

extends_documentation_fragment:
    - action_common_attributes
    - files
attributes:
    check_mode:
        support: full
    diff_mode:
        support: full
    platform:
        platforms: rhel
notes:
  - All comments will be removed if modifying an existing repo file.
  - Section order is preserved in an existing repo file.
  - Parameters in a section are ordered alphabetically in an existing repo
    file.
  - The repo file will be automatically deleted if it contains no repository.
  - When removing a repository, beware that the metadata cache may still remain
    on disk until you run C(yum clean all). Use a notification handler for this.
  - "The O(ignore:params) parameter was removed in Ansible 2.5 due to circumventing Ansible's parameter
    handling"
'''

EXAMPLES = '''
- name: Add repository
  ansible.builtin.yum_repository:
    name: epel
    description: EPEL YUM repo
    baseurl: https://download.fedoraproject.org/pub/epel/$releasever/$basearch/

- name: Add multiple repositories into the same file (1/2)
  ansible.builtin.yum_repository:
    name: epel
    description: EPEL YUM repo
    file: external_repos
    baseurl: https://download.fedoraproject.org/pub/epel/$releasever/$basearch/
    gpgcheck: no

- name: Add multiple repositories into the same file (2/2)
  ansible.builtin.yum_repository:
    name: rpmforge
    description: RPMforge YUM repo
    file: external_repos
    baseurl: http://apt.sw.be/redhat/el7/en/$basearch/rpmforge
    mirrorlist: http://mirrorlist.repoforge.org/el7/mirrors-rpmforge
    enabled: no

# Handler showing how to clean yum metadata cache
- name: yum-clean-metadata
  ansible.builtin.command: yum clean metadata

# Example removing a repository and cleaning up metadata cache
- name: Remove repository (and clean up left-over metadata)
  ansible.builtin.yum_repository:
    name: epel
    state: absent
  notify: yum-clean-metadata

- name: Remove repository from a specific repo file
  ansible.builtin.yum_repository:
    name: epel
    file: external_repos
    state: absent
'''

RETURN = '''
repo:
    description: repository name
    returned: success
    type: str
    sample: "epel"
state:
    description: state of the target, after execution
    returned: success
    type: str
    sample: "present"
'''

import os

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves import configparser
from ansible.module_utils.common.text.converters import to_native


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
        'module_hotfixes',
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
                if key == 'keepcache':
                    self.module.deprecate(
                        "'keepcache' parameter is deprecated.",
                        version='2.20'
                    )
                self.repofile.set(self.section, key, value)

    def save(self):
        if len(self.repofile.sections()):
            # Write data into the file
            try:
                with open(self.params['dest'], 'w') as fd:
                    self.repofile.write(fd)
            except IOError as e:
                self.module.fail_json(
                    msg="Problems handling file %s." % self.params['dest'],
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
        baseurl=dict(type='list', elements='str'),
        cost=dict(),
        deltarpm_metadata_percentage=dict(),
        deltarpm_percentage=dict(),
        description=dict(),
        enabled=dict(type='bool'),
        enablegroups=dict(type='bool'),
        exclude=dict(type='list', elements='str'),
        failovermethod=dict(choices=['roundrobin', 'priority']),
        file=dict(),
        gpgcakey=dict(no_log=False),
        gpgcheck=dict(type='bool'),
        gpgkey=dict(type='list', elements='str', no_log=False),
        module_hotfixes=dict(type='bool'),
        http_caching=dict(choices=['all', 'packages', 'none']),
        include=dict(),
        includepkgs=dict(type='list', elements='str'),
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
        sslcacert=dict(aliases=['ca_cert']),
        ssl_check_cert_permissions=dict(type='bool'),
        sslclientcert=dict(aliases=['client_cert']),
        sslclientkey=dict(aliases=['client_key'], no_log=False),
        sslverify=dict(type='bool', aliases=['validate_certs']),
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
