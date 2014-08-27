#!/usr/bin/python
# encoding: utf-8

# (c) 2012, Matt Wright <matt@nobien.net>
# (c) 2013, Alexander Saltanov <asd@mokote.com>
# (c) 2014, Rutger Spiertz <rutger@kumina.nl>
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
module: apt_repository
short_description: Add and remove APT repositories
description:
    - Add or remove an APT repositories in Ubuntu and Debian.
notes:
    - This module works on Debian and Ubuntu and requires C(python-apt).
    - This module supports Debian Squeeze (version 6) as well as its successors.
    - This module treats Debian and Ubuntu distributions separately. So PPA could be installed only on Ubuntu machines.
options:
    repo:
        required: true
        default: none
        description:
            - A source string for the repository.
    state:
        required: false
        choices: [ "absent", "present" ]
        default: "present"
        description:
            - A source string state.
    mode:
        required: false
        default: 0644
        description:
            - The octal mode for newly created files in sources.list.d
        version_added: "1.6"
    update_cache:
        description:
            - Run the equivalent of C(apt-get update) when a change occurs.  Cache updates are run after making changes.
        required: false
        default: "yes"
        choices: [ "yes", "no" ]
    validate_certs:
        version_added: '1.8'
        description:
            - If C(no), SSL certificates for the target repo will not be validated. This should only be used
              on personally controlled sites using self-signed certificates.
        required: false
        default: 'yes'
        choices: ['yes', 'no']
author: Alexander Saltanov
version_added: "0.7"
requirements: [ python-apt ]
'''

EXAMPLES = '''
# Add specified repository into sources list.
apt_repository: repo='deb http://archive.canonical.com/ubuntu hardy partner' state=present

# Add source repository into sources list.
apt_repository: repo='deb-src http://archive.canonical.com/ubuntu hardy partner' state=present

# Remove specified repository from sources list.
apt_repository: repo='deb http://archive.canonical.com/ubuntu hardy partner' state=absent

# On Ubuntu target: add nginx stable repository from PPA and install its signing key.
# On Debian target: adding PPA is not available, so it will fail immediately.
apt_repository: repo='ppa:nginx/stable'
'''

import glob
import os
import re
import tempfile

try:
    import apt
    import apt_pkg
    import aptsources.distro as aptsources_distro
    distro = aptsources_distro.get_distro()
    HAVE_PYTHON_APT = True
except ImportError:
    distro = None
    HAVE_PYTHON_APT = False


VALID_SOURCE_TYPES = ('deb', 'deb-src')

def install_python_apt(module):

    if not module.check_mode:
        apt_get_path = module.get_bin_path('apt-get')
        if apt_get_path:
            rc, so, se = module.run_command('%s update && %s install python-apt -y -q' % (apt_get_path, apt_get_path), use_unsafe_shell=True)
            if rc == 0:
                global apt, apt_pkg, aptsources_distro, distro, HAVE_PYTHON_APT
                import apt
                import apt_pkg
                import aptsources.distro as aptsources_distro
                distro = aptsources_distro.get_distro()
                HAVE_PYTHON_APT = True
            else:
                module.fail_json(msg="Failed to auto-install python-apt. Error was: '%s'" % se.strip())

class InvalidSource(Exception):
    pass


# Simple version of aptsources.sourceslist.SourcesList.
# No advanced logic and no backups inside.
class SourcesList(object):
    def __init__(self):
        self.files = {}  # group sources by file
        self.default_file = self._apt_cfg_file('Dir::Etc::sourcelist')

        # read sources.list if it exists
        if os.path.isfile(self.default_file):
            self.load(self.default_file)

        # read sources.list.d
        for file in glob.iglob('%s/*.list' % self._apt_cfg_dir('Dir::Etc::sourceparts')):
            self.load(file)

    def __iter__(self):
        '''Simple iterator to go over all sources. Empty, non-source, and other not valid lines will be skipped.'''
        for file, sources in self.files.items():
            for n, valid, enabled, source, comment in sources:
                if valid:
                    yield file, n, enabled, source, comment
        raise StopIteration

    def _expand_path(self, filename):
        if '/' in filename:
            return filename
        else:
            return os.path.abspath(os.path.join(self._apt_cfg_dir('Dir::Etc::sourceparts'), filename))

    def _suggest_filename(self, line):
        def _cleanup_filename(s):
            return '_'.join(re.sub('[^a-zA-Z0-9]', ' ', s).split())
        def _strip_username_password(s):
            if '@' in s:
                s = s.split('@', 1)
                s = s[-1]
            return s

        # Drop options and protocols.
        line = re.sub('\[[^\]]+\]', '', line)
        line = re.sub('\w+://', '', line)

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
            comment = line[i+1:].strip()
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

    @staticmethod
    def _apt_cfg_file(filespec):
        '''
        Wrapper for `apt_pkg` module for running with Python 2.5
        '''
        try:
            result = apt_pkg.config.find_file(filespec)
        except AttributeError:
            result = apt_pkg.Config.FindFile(filespec)
        return result

    @staticmethod
    def _apt_cfg_dir(dirspec):
        '''
        Wrapper for `apt_pkg` module for running with Python 2.5
        '''
        try:
            result = apt_pkg.config.find_dir(dirspec)
        except AttributeError:
            result = apt_pkg.Config.FindDir(dirspec)
        return result

    def load(self, file):
        group = []
        f = open(file, 'r')
        for n, line in enumerate(f):
            valid, enabled, source, comment = self._parse(line)
            group.append((n, valid, enabled, source, comment))
        self.files[file] = group

    def save(self, module):
        for filename, sources in self.files.items():
            if sources:
                d, fn = os.path.split(filename)
                fd, tmp_path = tempfile.mkstemp(prefix=".%s-" % fn, dir=d)

                # allow the user to override the default mode
                this_mode = module.params['mode']
                module.set_mode_if_different(tmp_path, this_mode, False)

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
                    except IOError, err:
                        module.fail_json(msg="Failed to write to file %s: %s" % (tmp_path, unicode(err)))
                module.atomic_move(tmp_path, filename)
            else:
                del self.files[filename]
                if os.path.exists(filename):
                    os.remove(filename)

    def dump(self):
        return '\n'.join([str(i) for i in self])

    def modify(self, file, n, enabled=None, source=None, comment=None):
        '''
        This function to be used with iterator, so we don't care of invalid sources.
        If source, enabled, or comment is None, original value from line ``n`` will be preserved.
        '''
        valid, enabled_old, source_old, comment_old = self.files[file][n][1:]
        choice = lambda new, old: old if new is None else new
        self.files[file][n] = (n, valid, choice(enabled, enabled_old), choice(source, source_old), choice(comment, comment_old))

    def _add_valid_source(self, source_new, comment_new, file):
        # We'll try to reuse disabled source if we have it.
        # If we have more than one entry, we will enable them all - no advanced logic, remember.
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

    LP_API = 'https://launchpad.net/api/1.0/~%s/+archive/%s'

    def __init__(self, module, add_ppa_signing_keys_callback=None):
        self.module = module
        self.add_ppa_signing_keys_callback = add_ppa_signing_keys_callback
        super(UbuntuSourcesList, self).__init__()

    def _get_ppa_info(self, owner_name, ppa_name):
        lp_api = self.LP_API % (owner_name, ppa_name)

        headers = dict(Accept='application/json')
        response, info = fetch_url(self.module, lp_api, headers=headers)
        if info['status'] != 200:
            self.module.fail_json(msg="failed to fetch PPA information, error was: %s" % info['msg'])
        return json.load(response)

    def _expand_ppa(self, path):
        ppa = path.split(':')[1]
        ppa_owner = ppa.split('/')[0]
        try:
            ppa_name = ppa.split('/')[1]
        except IndexError:
            ppa_name = 'ppa'

        line = 'deb http://ppa.launchpad.net/%s/%s/ubuntu %s main' % (ppa_owner, ppa_name, distro.codename)
        return line, ppa_owner, ppa_name

    def _key_already_exists(self, key_fingerprint):
        rc, out, err = self.module.run_command('apt-key export %s' % key_fingerprint, check_rc=True)
        return len(err) == 0

    def add_source(self, line, comment='', file=None):
        if line.startswith('ppa:'):
            source, ppa_owner, ppa_name = self._expand_ppa(line)

            if self.add_ppa_signing_keys_callback is not None:
                info = self._get_ppa_info(ppa_owner, ppa_name)
                if not self._key_already_exists(info['signing_key_fingerprint']):
                    command = ['apt-key', 'adv', '--recv-keys', '--keyserver', 'hkp://keyserver.ubuntu.com:80', info['signing_key_fingerprint']]
                    self.add_ppa_signing_keys_callback(command)

            file = file or self._suggest_filename('%s_%s' % (line, distro.codename))
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


def get_add_ppa_signing_key_callback(module):
    def _run_command(command):
        module.run_command(command, check_rc=True)

    if module.check_mode:
        return None
    else:
        return _run_command


def main():
    module = AnsibleModule(
        argument_spec=dict(
            repo=dict(required=True),
            state=dict(choices=['present', 'absent'], default='present'),
            mode=dict(required=False, default=0644),
            update_cache = dict(aliases=['update-cache'], type='bool', default='yes'),
            # this should not be needed, but exists as a failsafe
            install_python_apt=dict(required=False, default="yes", type='bool'),
            validate_certs = dict(default='yes', type='bool'),
        ),
        supports_check_mode=True,
    )

    params = module.params
    if params['install_python_apt'] and not HAVE_PYTHON_APT and not module.check_mode:
        install_python_apt(module)

    repo = module.params['repo']
    state = module.params['state']
    update_cache = module.params['update_cache']
    sourceslist = None

    if HAVE_PYTHON_APT:
        if isinstance(distro, aptsources_distro.UbuntuDistribution):
            sourceslist = UbuntuSourcesList(module,
                add_ppa_signing_keys_callback=get_add_ppa_signing_key_callback(module))
        elif HAVE_PYTHON_APT and \
            isinstance(distro, aptsources_distro.DebianDistribution) or isinstance(distro, aptsources_distro.Distribution):
            sourceslist = SourcesList()
    else:
        module.fail_json(msg='Module apt_repository supports only Debian and Ubuntu. ' + \
                             'You may be seeing this because python-apt is not installed, but you requested that it not be auto-installed')

    sources_before = sourceslist.dump()

    try:
        if state == 'present':
            sourceslist.add_source(repo)
        elif state == 'absent':
            sourceslist.remove_source(repo)
    except InvalidSource, err:
        module.fail_json(msg='Invalid repository string: %s' % unicode(err))

    sources_after = sourceslist.dump()
    changed = sources_before != sources_after

    if not module.check_mode and changed:
        try:
            sourceslist.save(module)
            if update_cache:
                cache = apt.Cache()
                cache.update()
        except OSError, err:
            module.fail_json(msg=unicode(err))

    module.exit_json(changed=changed, repo=repo, state=state)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

main()
