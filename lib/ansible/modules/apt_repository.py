# encoding: utf-8

# Copyright: (c) 2012, Matt Wright <matt@nobien.net>
# Copyright: (c) 2013, Alexander Saltanov <asd@mokote.com>
# Copyright: (c) 2014, Rutger Spiertz <rutger@kumina.nl>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = """
---
module: apt_repository
short_description: Add and remove APT repositories
description:
    - Add or remove an APT repositories in Ubuntu and Debian.
extends_documentation_fragment: action_common_attributes
attributes:
    check_mode:
        support: full
    diff_mode:
        support: full
    platform:
        platforms: debian
notes:
    - This module supports Debian Squeeze (version 6) as well as its successors and derivatives.
seealso:
  - module: ansible.builtin.deb822_repository
options:
    repo:
        description:
            - A source string for the repository.
        type: str
        required: true
    state:
        description:
            - A source string state.
        type: str
        choices: [ absent, present ]
        default: "present"
    mode:
        description:
            - The octal mode for newly created files in C(sources.list.d).
            - Default is what system uses (probably 0644).
        type: raw
        version_added: "1.6"
    update_cache:
        description:
            - Run the equivalent of C(apt-get update) when a change occurs. Cache updates are run after making changes.
        type: bool
        default: "yes"
        aliases: [ update-cache ]
    update_cache_retries:
        description:
        - Amount of retries if the cache update fails. Also see O(update_cache_retry_max_delay).
        type: int
        default: 5
        version_added: '2.10'
    update_cache_retry_max_delay:
        description:
        - Use an exponential backoff delay for each retry (see O(update_cache_retries)) up to this max delay in seconds.
        type: int
        default: 12
        version_added: '2.10'
    validate_certs:
        description:
            - If V(false), SSL certificates for the target repo will not be validated. This should only be used
              on personally controlled sites using self-signed certificates.
        type: bool
        default: 'yes'
        version_added: '1.8'
    filename:
        description:
            - Sets the name of the source list file in C(sources.list.d).
              Defaults to a file name based on the repository source url.
              The C(.list) extension will be automatically added.
        type: str
        version_added: '2.1'
    codename:
        description:
            - Override the distribution codename to use for PPA repositories.
              Should usually only be set when working with a PPA on
              a non-Ubuntu target (for example, Debian or Mint).
        type: str
        version_added: '2.3'
    install_python_apt:
        description:
            - Whether to automatically try to install the Python apt library or not, if it is not already installed.
              Without this library, the module does not work.
            - Runs C(apt-get install python3-apt).
            - Only works with the system Python. If you are using a Python on the remote that is not
              the system Python, set O(install_python_apt=false) and ensure that the Python apt library
              for your Python version is installed some other way.
        type: bool
        default: true
author:
- Alexander Saltanov (@sashka)
version_added: "0.7"
requirements:
   - python3-apt
   - apt-key or gpg
"""

EXAMPLES = """
- name: Add specified repository into sources list
  ansible.builtin.apt_repository:
    repo: deb http://archive.canonical.com/ubuntu hardy partner
    state: present

- name: Add specified repository into sources list using specified filename
  ansible.builtin.apt_repository:
    repo: deb http://dl.google.com/linux/chrome/deb/ stable main
    state: present
    filename: google-chrome

- name: Add source repository into sources list
  ansible.builtin.apt_repository:
    repo: deb-src http://archive.canonical.com/ubuntu hardy partner
    state: present

- name: Remove specified repository from sources list
  ansible.builtin.apt_repository:
    repo: deb http://archive.canonical.com/ubuntu hardy partner
    state: absent

- name: Add nginx stable repository from PPA and install its signing key on Ubuntu target
  ansible.builtin.apt_repository:
    repo: ppa:nginx/stable

- name: Add nginx stable repository from PPA and install its signing key on Debian target
  ansible.builtin.apt_repository:
    repo: 'ppa:nginx/stable'
    codename: trusty

- name: One way to avoid apt_key once it is removed from your distro
  block:
    - name: somerepo |no apt key
      ansible.builtin.get_url:
        url: https://download.example.com/linux/ubuntu/gpg
        dest: /etc/apt/keyrings/somerepo.asc

    - name: somerepo | apt source
      ansible.builtin.apt_repository:
        repo: "deb [arch=amd64 signed-by=/etc/apt/keyrings/somerepo.asc] https://download.example.com/linux/ubuntu {{ ansible_distribution_release }} stable"
        state: present
"""

RETURN = """
repo:
  description: A source string for the repository
  returned: always
  type: str
  sample: "deb https://artifacts.elastic.co/packages/6.x/apt stable main"

sources_added:
  description: List of sources added
  returned: success, sources were added
  type: list
  sample: ["/etc/apt/sources.list.d/artifacts_elastic_co_packages_6_x_apt.list"]
  version_added: "2.15"

sources_removed:
  description: List of sources removed
  returned: success, sources were removed
  type: list
  sample: ["/etc/apt/sources.list.d/artifacts_elastic_co_packages_6_x_apt.list"]
  version_added: "2.15"
"""

import copy
import glob
import json
import os
import re
import secrets
import sys
import tempfile
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.file import S_IRWU_RG_RO as DEFAULT_SOURCES_PERM
from ansible.module_utils.common.respawn import has_respawned, probe_interpreters_for_module, respawn_module
from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.urls import fetch_url

from ansible.module_utils.common.locale import get_best_parsable_locale

try:
    import apt
    import apt_pkg
    import aptsources.distro as aptsources_distro

    distro = aptsources_distro.get_distro()

    HAVE_PYTHON_APT = True
except ImportError:
    apt = apt_pkg = aptsources_distro = distro = None

    HAVE_PYTHON_APT = False

APT_KEY_DIRS = ['/etc/apt/keyrings', '/etc/apt/trusted.gpg.d', '/usr/share/keyrings']
VALID_SOURCE_TYPES = ('deb', 'deb-src')


def install_python_apt(module, apt_pkg_name):

    if not module.check_mode:
        apt_get_path = module.get_bin_path('apt-get')
        if apt_get_path:
            rc, so, se = module.run_command([apt_get_path, 'update'])
            if rc != 0:
                module.fail_json(msg="Failed to auto-install %s. Error was: '%s'" % (apt_pkg_name, se.strip()))
            rc, so, se = module.run_command([apt_get_path, 'install', apt_pkg_name, '-y', '-q'])
            if rc != 0:
                module.fail_json(msg="Failed to auto-install %s. Error was: '%s'" % (apt_pkg_name, se.strip()))
    else:
        module.fail_json(msg="%s must be installed to use check mode" % apt_pkg_name)


class InvalidSource(Exception):
    pass


# Simple version of aptsources.sourceslist.SourcesList.
# No advanced logic and no backups inside.
class SourcesList(object):
    def __init__(self, module):
        self.module = module
        self.files = {}  # group sources by file
        self.files_mapping = {}  # internal DS for tracking symlinks
        # Repositories that we're adding -- used to implement mode param
        self.new_repos = set()
        self.default_file = apt_pkg.config.find_file('Dir::Etc::sourcelist')

        # read sources.list if it exists
        if os.path.isfile(self.default_file):
            self.load(self.default_file)

        # read sources.list.d
        self.sources_dir = apt_pkg.config.find_dir('Dir::Etc::sourceparts')
        for file in glob.iglob(f'{self.sources_dir}/*.list'):
            if os.path.islink(file):
                self.files_mapping[file] = os.readlink(file)
            self.load(file)

    def __iter__(self):
        """Simple iterator to go over all sources. Empty, non-source, and other not valid lines will be skipped."""
        for file, sources in self.files.items():
            for n, valid, enabled, source, comment in sources:
                if valid:
                    yield file, n, enabled, source, comment

    def _expand_path(self, filename):
        if '/' in filename:
            return filename
        else:
            return os.path.abspath(os.path.join(self.sources_dir, filename))

    def _suggest_filename(self, line):
        def _cleanup_filename(s):
            filename = self.module.params['filename']
            if filename is not None:
                return filename
            return '_'.join(re.sub('[^a-zA-Z0-9]', ' ', s).split())

        def _strip_username_password(s):
            if '@' in s:
                s = s.split('@', 1)
                s = s[-1]
            return s

        # Drop options and protocols.
        line = re.sub(r'\[[^\]]+\]', '', line)
        line = re.sub(r'\w+://', '', line)

        # split line into valid keywords
        parts = [part for part in line.split() if part not in VALID_SOURCE_TYPES]

        # Drop usernames and passwords
        parts[0] = _strip_username_password(parts[0])

        return '%s.list' % _cleanup_filename(' '.join(parts[:1]))

    def _parse(self, line, raise_if_invalid_or_disabled=False):
        valid = False
        enabled = True
        source = ''
        comment = ''

        line = line.strip()
        if line.startswith('#'):
            enabled = False
            line = line[1:]

        # Check for another "#" in the line and treat a part after it as a comment.
        i = line.find('#')
        if i > 0:
            comment = line[i + 1:].strip()
            line = line[:i]

        # Split a source into substring to make sure that it is source spec.
        # Duplicated whitespaces in a valid source spec will be removed.
        source = line.strip()
        if source:
            chunks = source.split()
            if chunks[0] in VALID_SOURCE_TYPES:
                valid = True
                source = ' '.join(chunks)

        if raise_if_invalid_or_disabled and (not valid or not enabled):
            raise InvalidSource(line)

        return valid, enabled, source, comment

    def load(self, file):
        group = []
        f = open(file, 'r')
        for n, line in enumerate(f):
            valid, enabled, source, comment = self._parse(line)
            group.append((n, valid, enabled, source, comment))
        self.files[file] = group

    def save(self):
        for filename, sources in list(self.files.items()):
            if sources:
                d, fn = os.path.split(filename)
                try:
                    os.makedirs(d)
                except OSError as ex:
                    if not os.path.isdir(d):
                        self.module.fail_json("Failed to create directory %s: %s" % (d, to_native(ex)))

                try:
                    fd, tmp_path = tempfile.mkstemp(prefix=".%s-" % fn, dir=d)
                except OSError as ex:
                    raise Exception(f'Unable to create temp file at {d!r} for apt source.') from ex

                f = os.fdopen(fd, 'w')
                for n, valid, enabled, source, comment in sources:
                    chunks = []
                    if not enabled:
                        chunks.append('# ')
                    chunks.append(source)
                    if comment:
                        chunks.append(' # ')
                        chunks.append(comment)
                    chunks.append('\n')
                    line = ''.join(chunks)

                    try:
                        f.write(line)
                    except OSError as ex:
                        raise Exception(f"Failed to write to file {tmp_path!r}.") from ex
                if filename in self.files_mapping:
                    # Write to symlink target instead of replacing symlink as a normal file
                    self.module.atomic_move(tmp_path, self.files_mapping[filename])
                else:
                    self.module.atomic_move(tmp_path, filename)

                # allow the user to override the default mode
                if filename in self.new_repos:
                    this_mode = self.module.params.get('mode', DEFAULT_SOURCES_PERM)
                    self.module.set_mode_if_different(filename, this_mode, False)
            else:
                del self.files[filename]
                if os.path.exists(filename):
                    os.remove(filename)

    def dump(self):
        dumpstruct = {}
        for filename, sources in self.files.items():
            if sources:
                lines = []
                for n, valid, enabled, source, comment in sources:
                    chunks = []
                    if not enabled:
                        chunks.append('# ')
                    chunks.append(source)
                    if comment:
                        chunks.append(' # ')
                        chunks.append(comment)
                    chunks.append('\n')
                    lines.append(''.join(chunks))
                dumpstruct[filename] = ''.join(lines)
        return dumpstruct

    def _choice(self, new, old):
        if new is None:
            return old
        return new

    def modify(self, file, n, enabled=None, source=None, comment=None):
        """
        This function to be used with iterator, so we don't care of invalid sources.
        If source, enabled, or comment is None, original value from line ``n`` will be preserved.
        """
        valid, enabled_old, source_old, comment_old = self.files[file][n][1:]
        self.files[file][n] = (n, valid, self._choice(enabled, enabled_old), self._choice(source, source_old), self._choice(comment, comment_old))

    def _add_valid_source(self, source_new, comment_new, file):
        # We'll try to reuse disabled source if we have it.
        # If we have more than one entry, we will enable them all - no advanced logic, remember.
        self.module.log('adding source file: %s | %s | %s' % (source_new, comment_new, file))
        found = False
        for filename, n, enabled, source, comment in self:
            if source == source_new:
                self.modify(filename, n, enabled=True)
                found = True

        if not found:
            if file is None:
                file = self.default_file
            else:
                file = self._expand_path(file)

            if file not in self.files:
                self.files[file] = []

            files = self.files[file]
            files.append((len(files), True, True, source_new, comment_new))
            self.new_repos.add(file)

    def add_source(self, line, comment='', file=None):
        source = self._parse(line, raise_if_invalid_or_disabled=True)[2]

        # Prefer separate files for new sources.
        self._add_valid_source(source, comment, file=file or self._suggest_filename(source))

    def _remove_valid_source(self, source):
        # If we have more than one entry, we will remove them all (not comment, remove!)
        for filename, n, enabled, src, comment in self:
            if source == src and enabled:
                self.files[filename].pop(n)

    def remove_source(self, line):
        source = self._parse(line, raise_if_invalid_or_disabled=True)[2]
        self._remove_valid_source(source)


class UbuntuSourcesList(SourcesList):

    # prefer api.launchpad.net over launchpad.net/api
    # see: https://github.com/ansible/ansible/pull/81978#issuecomment-1767062178
    LP_API = 'https://api.launchpad.net/1.0/~%s/+archive/%s'
    PPA_URI = 'https://ppa.launchpadcontent.net'

    def __init__(self, module):
        self.module = module
        self.codename = module.params['codename'] or distro.codename
        super(UbuntuSourcesList, self).__init__(module)

        self.apt_key_bin = self.module.get_bin_path('apt-key', required=False)
        self.gpg_bin = self.module.get_bin_path('gpg', required=False)
        if not self.apt_key_bin and not self.gpg_bin:
            msg = 'Either apt-key or gpg binary is required, but neither could be found.' \
                  'The apt-key CLI has been deprecated and removed in modern Debian and derivatives, ' \
                  'you might want to use "deb822_repository" instead.'
            self.module.fail_json(msg)

    def __deepcopy__(self, memo=None):
        return UbuntuSourcesList(self.module)

    def _get_ppa_info(self, owner_name, ppa_name):
        lp_api = self.LP_API % (owner_name, ppa_name)

        headers = dict(Accept='application/json')
        response, info = fetch_url(self.module, lp_api, headers=headers)
        if info['status'] != 200:
            self.module.fail_json(msg="failed to fetch PPA information, error was: %s" % info['msg'])
        return json.loads(to_native(response.read()))

    def _expand_ppa(self, path):
        ppa = path.split(':')[1]
        ppa_owner = ppa.split('/')[0]
        try:
            ppa_name = ppa.split('/')[1]
        except IndexError:
            ppa_name = 'ppa'

        line = 'deb %s/%s/%s/ubuntu %s main' % (self.PPA_URI, ppa_owner, ppa_name, self.codename)
        return line, ppa_owner, ppa_name

    def _key_already_exists(self, key_fingerprint):

        if self.apt_key_bin:
            locale = get_best_parsable_locale(self.module)
            APT_ENV = dict(LANG=locale, LC_ALL=locale, LC_MESSAGES=locale, LC_CTYPE=locale, LANGUAGE=locale)
            self.module.run_command_environ_update = APT_ENV
            rc, out, err = self.module.run_command([self.apt_key_bin, 'export', key_fingerprint], check_rc=True)
            found = bool(not err or 'nothing exported' not in err)
        else:
            found = self._gpg_key_exists(key_fingerprint)

        return found

    def _gpg_key_exists(self, key_fingerprint):

        found = False
        keyfiles = ['/etc/apt/trusted.gpg']  # main gpg repo for apt
        for other_dir in APT_KEY_DIRS:
            # add other known sources of gpg sigs for apt, skip hidden files
            keyfiles.extend([os.path.join(other_dir, x) for x in os.listdir(other_dir) if not x.startswith('.')])

        for key_file in keyfiles:

            if os.path.exists(key_file):
                try:
                    rc, out, err = self.module.run_command([self.gpg_bin, '--list-packets', key_file])
                except OSError as ex:
                    self.module.debug(f"Could check key against file {key_file!r}: {ex}")
                    continue

                if key_fingerprint in out:
                    found = True
                    break

        return found

    # https://www.linuxuprising.com/2021/01/apt-key-is-deprecated-how-to-add.html
    def add_source(self, line, comment='', file=None):
        if line.startswith('ppa:'):
            source, ppa_owner, ppa_name = self._expand_ppa(line)

            if source in self.repos_urls:
                # repository already exists
                return

            info = self._get_ppa_info(ppa_owner, ppa_name)

            # add gpg sig if needed
            if not self._key_already_exists(info['signing_key_fingerprint']):

                # TODO: report file that would have been added if not check_mode
                keyfile = ''
                if not self.module.check_mode:
                    if self.apt_key_bin:
                        command = [self.apt_key_bin, 'adv', '--recv-keys', '--no-tty', '--keyserver', 'hkp://keyserver.ubuntu.com:80',
                                   info['signing_key_fingerprint']]
                    else:
                        # use first available key dir, in order of preference
                        for keydir in APT_KEY_DIRS:
                            if os.path.exists(keydir):
                                break
                        else:
                            self.module.fail_json("Unable to find any existing apt gpgp repo directories, tried the following: %s" % ', '.join(APT_KEY_DIRS))

                        keyfile = '%s/%s-%s-%s.gpg' % (keydir, os.path.basename(source).replace(' ', '-'), ppa_owner, ppa_name)
                        command = [self.gpg_bin, '--no-tty', '--keyserver', 'hkp://keyserver.ubuntu.com:80', '--export', info['signing_key_fingerprint']]

                    rc, stdout, stderr = self.module.run_command(command, check_rc=True, encoding=None)
                    if keyfile:
                        # using gpg we must write keyfile ourselves
                        if len(stdout) == 0:
                            self.module.fail_json(msg='Unable to get required signing key', rc=rc, stderr=stderr, command=command)
                        try:
                            with open(keyfile, 'wb') as f:
                                f.write(stdout)
                            self.module.log('Added repo key "%s" for apt to file "%s"' % (info['signing_key_fingerprint'], keyfile))
                        except OSError as ex:
                            self.module.fail_json(msg='Unable to add required signing key.', rc=rc, stderr=stderr, error=str(ex), exception=ex)

            # apt source file
            file = file or self._suggest_filename('%s_%s' % (line, self.codename))
        else:
            source = self._parse(line, raise_if_invalid_or_disabled=True)[2]
            file = file or self._suggest_filename(source)

        self._add_valid_source(source, comment, file)

    def remove_source(self, line):
        if line.startswith('ppa:'):
            source = self._expand_ppa(line)[0]
        else:
            source = self._parse(line, raise_if_invalid_or_disabled=True)[2]
        self._remove_valid_source(source)

    @property
    def repos_urls(self):
        _repositories = []
        for parsed_repos in self.files.values():
            for parsed_repo in parsed_repos:
                valid = parsed_repo[1]
                enabled = parsed_repo[2]
                source_line = parsed_repo[3]

                if not valid or not enabled:
                    continue

                if source_line.startswith('ppa:'):
                    source, ppa_owner, ppa_name = self._expand_ppa(source_line)
                    _repositories.append(source)
                else:
                    _repositories.append(source_line)

        return _repositories


def revert_sources_list(sources_before, sources_after, sourceslist_before):
    """Revert the sourcelist files to their previous state."""

    # First remove any new files that were created:
    for filename in set(sources_after.keys()).difference(sources_before.keys()):
        if os.path.exists(filename):
            os.remove(filename)
    # Now revert the existing files to their former state:
    sourceslist_before.save()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            repo=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['absent', 'present']),
            mode=dict(type='raw'),
            update_cache=dict(type='bool', default=True, aliases=['update-cache']),
            update_cache_retries=dict(type='int', default=5),
            update_cache_retry_max_delay=dict(type='int', default=12),
            filename=dict(type='str'),
            # This should not be needed, but exists as a failsafe
            install_python_apt=dict(type='bool', default=True),
            validate_certs=dict(type='bool', default=True),
            codename=dict(type='str'),
        ),
        supports_check_mode=True,
    )

    params = module.params
    repo = module.params['repo']
    state = module.params['state']
    update_cache = module.params['update_cache']
    # Note: mode is referenced in SourcesList class via the passed in module (self here)

    sourceslist = None

    if not HAVE_PYTHON_APT:
        # This interpreter can't see the apt Python library- we'll do the following to try and fix that:
        # 1) look in common locations for system-owned interpreters that can see it; if we find one, respawn under it
        # 2) finding none, try to install a matching python-apt package for the current interpreter version;
        #    we limit to the current interpreter version to try and avoid installing a whole other Python just
        #    for apt support
        # 3) if we installed a support package, try to respawn under what we think is the right interpreter (could be
        #    the current interpreter again, but we'll let it respawn anyway for simplicity)
        # 4) if still not working, return an error and give up (some corner cases not covered, but this shouldn't be
        #    made any more complex than it already is to try and cover more, eg, custom interpreters taking over
        #    system locations)

        apt_pkg_name = 'python3-apt'

        if has_respawned():
            # this shouldn't be possible; short-circuit early if it happens...
            module.fail_json(msg="{0} must be installed and visible from {1}.".format(apt_pkg_name, sys.executable))

        interpreters = ['/usr/bin/python3', '/usr/bin/python']

        interpreter = probe_interpreters_for_module(interpreters, 'apt')

        if interpreter:
            # found the Python bindings; respawn this module under the interpreter where we found them
            respawn_module(interpreter)
            # this is the end of the line for this process, it will exit here once the respawned module has completed

        # don't make changes if we're in check_mode
        if module.check_mode:
            module.fail_json(msg="%s must be installed to use check mode. "
                                 "If run normally this module can auto-install it." % apt_pkg_name)

        if params['install_python_apt']:
            install_python_apt(module, apt_pkg_name)
        else:
            module.fail_json(msg='%s is not installed, and install_python_apt is False' % apt_pkg_name)

        # try again to find the bindings in common places
        interpreter = probe_interpreters_for_module(interpreters, 'apt')

        if interpreter:
            # found the Python bindings; respawn this module under the interpreter where we found them
            # NB: respawn is somewhat wasteful if it's this interpreter, but simplifies the code
            respawn_module(interpreter)
            # this is the end of the line for this process, it will exit here once the respawned module has completed
        else:
            # we've done all we can do; just tell the user it's busted and get out
            module.fail_json(msg="{0} must be installed and visible from {1}.".format(apt_pkg_name, sys.executable))

    if not repo:
        module.fail_json(msg='Please set argument \'repo\' to a non-empty value')

    if isinstance(distro, aptsources_distro.Distribution):
        sourceslist = UbuntuSourcesList(module)
    else:
        module.fail_json(msg='Module apt_repository is not supported on target.')

    sourceslist_before = copy.deepcopy(sourceslist)
    sources_before = sourceslist.dump()

    try:
        if state == 'present':
            sourceslist.add_source(repo)
        elif state == 'absent':
            sourceslist.remove_source(repo)
    except InvalidSource as ex:
        module.fail_json(msg='Invalid repository string: %s' % to_native(ex))

    sources_after = sourceslist.dump()
    changed = sources_before != sources_after

    diff = []
    sources_added = set()
    sources_removed = set()
    if changed:
        sources_added = set(sources_after.keys()).difference(sources_before.keys())
        sources_removed = set(sources_before.keys()).difference(sources_after.keys())
        if module._diff:
            for filename in set(sources_added.union(sources_removed)):
                diff.append({'before': sources_before.get(filename, ''),
                             'after': sources_after.get(filename, ''),
                             'before_header': (filename, '/dev/null')[filename not in sources_before],
                             'after_header': (filename, '/dev/null')[filename not in sources_after]})

    if changed and not module.check_mode:
        try:
            err = ''
            sourceslist.save()
            if update_cache:
                update_cache_retries = module.params.get('update_cache_retries')
                update_cache_retry_max_delay = module.params.get('update_cache_retry_max_delay')
                randomize = secrets.randbelow(1000) / 1000.0

                cache = apt.Cache()
                for retry in range(update_cache_retries):
                    try:
                        cache.update()
                        break
                    except apt.cache.FetchFailedException as fetch_failed_exc:
                        err = fetch_failed_exc
                        module.warn(
                            f"Failed to update cache after {retry + 1} due "
                            f"to {to_native(fetch_failed_exc)} retry, retrying"
                        )

                    # Use exponential backoff with a max fail count, plus a little bit of randomness
                    delay = 2 ** retry + randomize
                    if delay > update_cache_retry_max_delay:
                        delay = update_cache_retry_max_delay + randomize
                    time.sleep(delay)
                    module.warn(f"Sleeping for {int(round(delay))} seconds, before attempting to update the cache again")
                else:
                    revert_sources_list(sources_before, sources_after, sourceslist_before)
                    msg = (
                        f"Failed to update apt cache after {update_cache_retries} retries: "
                        f"{err if err else 'unknown reason'}"
                    )
                    module.fail_json(msg=msg)

        except OSError as ex:
            revert_sources_list(sources_before, sources_after, sourceslist_before)
            raise

    module.exit_json(changed=changed, repo=repo, sources_added=sources_added, sources_removed=sources_removed, state=state, diff=diff)


if __name__ == '__main__':
    main()
