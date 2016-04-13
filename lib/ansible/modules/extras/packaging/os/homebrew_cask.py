#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Daniel Jaouen <dcj24@cornell.edu>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: homebrew_cask
author: "Daniel Jaouen (@danieljaouen)"
short_description: Install/uninstall homebrew casks.
description:
    - Manages Homebrew casks.
version_added: "1.6"
options:
    name:
        description:
            - name of cask to install/remove
        required: true
    state:
        description:
            - state of the cask
        choices: [ 'present', 'absent' ]
        required: false
        default: present
'''
EXAMPLES = '''
- homebrew_cask: name=alfred state=present
- homebrew_cask: name=alfred state=absent
'''

import os.path
import re


# exceptions -------------------------------------------------------------- {{{
class HomebrewCaskException(Exception):
    pass
# /exceptions ------------------------------------------------------------- }}}


# utils ------------------------------------------------------------------- {{{
def _create_regex_group(s):
    lines = (line.strip() for line in s.split('\n') if line.strip())
    chars = filter(None, (line.split('#')[0].strip() for line in lines))
    group = r'[^' + r''.join(chars) + r']'
    return re.compile(group)
# /utils ------------------------------------------------------------------ }}}


class HomebrewCask(object):
    '''A class to manage Homebrew casks.'''

    # class regexes ------------------------------------------------ {{{
    VALID_PATH_CHARS = r'''
        \w                  # alphanumeric characters (i.e., [a-zA-Z0-9_])
        \s                  # spaces
        :                   # colons
        {sep}               # the OS-specific path separator
        -                   # dashes
    '''.format(sep=os.path.sep)

    VALID_BREW_PATH_CHARS = r'''
        \w                  # alphanumeric characters (i.e., [a-zA-Z0-9_])
        \s                  # spaces
        {sep}               # the OS-specific path separator
        -                   # dashes
    '''.format(sep=os.path.sep)

    VALID_CASK_CHARS = r'''
        \w                  # alphanumeric characters (i.e., [a-zA-Z0-9_])
        -                   # dashes
    '''

    INVALID_PATH_REGEX        = _create_regex_group(VALID_PATH_CHARS)
    INVALID_BREW_PATH_REGEX   = _create_regex_group(VALID_BREW_PATH_CHARS)
    INVALID_CASK_REGEX        = _create_regex_group(VALID_CASK_CHARS)
    # /class regexes ----------------------------------------------- }}}

    # class validations -------------------------------------------- {{{
    @classmethod
    def valid_path(cls, path):
        '''
        `path` must be one of:
         - list of paths
         - a string containing only:
             - alphanumeric characters
             - dashes
             - spaces
             - colons
             - os.path.sep
        '''

        if isinstance(path, basestring):
            return not cls.INVALID_PATH_REGEX.search(path)

        try:
            iter(path)
        except TypeError:
            return False
        else:
            paths = path
            return all(cls.valid_brew_path(path_) for path_ in paths)

    @classmethod
    def valid_brew_path(cls, brew_path):
        '''
        `brew_path` must be one of:
         - None
         - a string containing only:
             - alphanumeric characters
             - dashes
             - spaces
             - os.path.sep
        '''

        if brew_path is None:
            return True

        return (
            isinstance(brew_path, basestring)
            and not cls.INVALID_BREW_PATH_REGEX.search(brew_path)
        )

    @classmethod
    def valid_cask(cls, cask):
        '''A valid cask is either None or alphanumeric + backslashes.'''

        if cask is None:
            return True

        return (
            isinstance(cask, basestring)
            and not cls.INVALID_CASK_REGEX.search(cask)
        )

    @classmethod
    def valid_state(cls, state):
        '''
        A valid state is one of:
            - installed
            - absent
        '''

        if state is None:
            return True
        else:
            return (
                isinstance(state, basestring)
                and state.lower() in (
                    'installed',
                    'absent',
                )
            )

    @classmethod
    def valid_module(cls, module):
        '''A valid module is an instance of AnsibleModule.'''

        return isinstance(module, AnsibleModule)
    # /class validations ------------------------------------------- }}}

    # class properties --------------------------------------------- {{{
    @property
    def module(self):
        return self._module

    @module.setter
    def module(self, module):
        if not self.valid_module(module):
            self._module = None
            self.failed = True
            self.message = 'Invalid module: {0}.'.format(module)
            raise HomebrewCaskException(self.message)

        else:
            self._module = module
            return module

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, path):
        if not self.valid_path(path):
            self._path = []
            self.failed = True
            self.message = 'Invalid path: {0}.'.format(path)
            raise HomebrewCaskException(self.message)

        else:
            if isinstance(path, basestring):
                self._path = path.split(':')
            else:
                self._path = path

            return path

    @property
    def brew_path(self):
        return self._brew_path

    @brew_path.setter
    def brew_path(self, brew_path):
        if not self.valid_brew_path(brew_path):
            self._brew_path = None
            self.failed = True
            self.message = 'Invalid brew_path: {0}.'.format(brew_path)
            raise HomebrewCaskException(self.message)

        else:
            self._brew_path = brew_path
            return brew_path

    @property
    def params(self):
        return self._params

    @params.setter
    def params(self, params):
        self._params = self.module.params
        return self._params

    @property
    def current_cask(self):
        return self._current_cask

    @current_cask.setter
    def current_cask(self, cask):
        if not self.valid_cask(cask):
            self._current_cask = None
            self.failed = True
            self.message = 'Invalid cask: {0}.'.format(cask)
            raise HomebrewCaskException(self.message)

        else:
            self._current_cask = cask
            return cask
    # /class properties -------------------------------------------- }}}

    def __init__(self, module, path=None, casks=None, state=None):
        self._setup_status_vars()
        self._setup_instance_vars(module=module, path=path, casks=casks,
                                  state=state)

        self._prep()

    # prep --------------------------------------------------------- {{{
    def _setup_status_vars(self):
        self.failed = False
        self.changed = False
        self.changed_count = 0
        self.unchanged_count = 0
        self.message = ''

    def _setup_instance_vars(self, **kwargs):
        for key, val in kwargs.iteritems():
            setattr(self, key, val)

    def _prep(self):
        self._prep_path()
        self._prep_brew_path()

    def _prep_path(self):
        if not self.path:
            self.path = ['/usr/local/bin']

    def _prep_brew_path(self):
        if not self.module:
            self.brew_path = None
            self.failed = True
            self.message = 'AnsibleModule not set.'
            raise HomebrewCaskException(self.message)

        self.brew_path = self.module.get_bin_path(
            'brew',
            required=True,
            opt_dirs=self.path,
        )
        if not self.brew_path:
            self.brew_path = None
            self.failed = True
            self.message = 'Unable to locate homebrew executable.'
            raise HomebrewCaskException('Unable to locate homebrew executable.')

        return self.brew_path

    def _status(self):
        return (self.failed, self.changed, self.message)
    # /prep -------------------------------------------------------- }}}

    def run(self):
        try:
            self._run()
        except HomebrewCaskException:
            pass

        if not self.failed and (self.changed_count + self.unchanged_count > 1):
            self.message = "Changed: %d, Unchanged: %d" % (
                self.changed_count,
                self.unchanged_count,
            )
        (failed, changed, message) = self._status()

        return (failed, changed, message)

    # checks ------------------------------------------------------- {{{
    def _current_cask_is_installed(self):
        if not self.valid_cask(self.current_cask):
            self.failed = True
            self.message = 'Invalid cask: {0}.'.format(self.current_cask)
            raise HomebrewCaskException(self.message)

        cmd = [self.brew_path, 'cask', 'list']
        rc, out, err = self.module.run_command(cmd, path_prefix=self.path[0])

        if 'nothing to list' in err:
            return False
        elif rc == 0:
            casks = [cask_.strip() for cask_ in out.split('\n') if cask_.strip()]
            return self.current_cask in casks
        else:
            self.failed = True
            self.message = err.strip()
            raise HomebrewCaskException(self.message)
    # /checks ------------------------------------------------------ }}}

    # commands ----------------------------------------------------- {{{
    def _run(self):
        if self.state == 'installed':
            return self._install_casks()
        elif self.state == 'absent':
            return self._uninstall_casks()

        if self.command:
            return self._command()

    # updated -------------------------------- {{{
    def _update_homebrew(self):
        rc, out, err = self.module.run_command([
            self.brew_path,
            'update',
        ], path_prefix=self.path[0])
        if rc == 0:
            if out and isinstance(out, basestring):
                already_updated = any(
                    re.search(r'Already up-to-date.', s.strip(), re.IGNORECASE)
                    for s in out.split('\n')
                    if s
                )
                if not already_updated:
                    self.changed = True
                    self.message = 'Homebrew updated successfully.'
                else:
                    self.message = 'Homebrew already up-to-date.'

            return True
        else:
            self.failed = True
            self.message = err.strip()
            raise HomebrewCaskException(self.message)
    # /updated ------------------------------- }}}

    # installed ------------------------------ {{{
    def _install_current_cask(self):
        if not self.valid_cask(self.current_cask):
            self.failed = True
            self.message = 'Invalid cask: {0}.'.format(self.current_cask)
            raise HomebrewCaskException(self.message)

        if self._current_cask_is_installed():
            self.unchanged_count += 1
            self.message = 'Cask already installed: {0}'.format(
                self.current_cask,
            )
            return True

        if self.module.check_mode:
            self.changed = True
            self.message = 'Cask would be installed: {0}'.format(
                self.current_cask
            )
            raise HomebrewCaskException(self.message)

        cmd = [opt
               for opt in (self.brew_path, 'cask', 'install', self.current_cask)
               if opt]

        rc, out, err = self.module.run_command(cmd, path_prefix=self.path[0])

        if self._current_cask_is_installed():
            self.changed_count += 1
            self.changed = True
            self.message = 'Cask installed: {0}'.format(self.current_cask)
            return True
        else:
            self.failed = True
            self.message = err.strip()
            raise HomebrewCaskException(self.message)

    def _install_casks(self):
        for cask in self.casks:
            self.current_cask = cask
            self._install_current_cask()

        return True
    # /installed ----------------------------- }}}

    # uninstalled ---------------------------- {{{
    def _uninstall_current_cask(self):
        if not self.valid_cask(self.current_cask):
            self.failed = True
            self.message = 'Invalid cask: {0}.'.format(self.current_cask)
            raise HomebrewCaskException(self.message)

        if not self._current_cask_is_installed():
            self.unchanged_count += 1
            self.message = 'Cask already uninstalled: {0}'.format(
                self.current_cask,
            )
            return True

        if self.module.check_mode:
            self.changed = True
            self.message = 'Cask would be uninstalled: {0}'.format(
                self.current_cask
            )
            raise HomebrewCaskException(self.message)

        cmd = [opt
               for opt in (self.brew_path, 'cask', 'uninstall', self.current_cask)
               if opt]

        rc, out, err = self.module.run_command(cmd, path_prefix=self.path[0])

        if not self._current_cask_is_installed():
            self.changed_count += 1
            self.changed = True
            self.message = 'Cask uninstalled: {0}'.format(self.current_cask)
            return True
        else:
            self.failed = True
            self.message = err.strip()
            raise HomebrewCaskException(self.message)

    def _uninstall_casks(self):
        for cask in self.casks:
            self.current_cask = cask
            self._uninstall_current_cask()

        return True
    # /uninstalled ----------------------------- }}}
    # /commands ---------------------------------------------------- }}}


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(aliases=["cask"], required=False),
            path=dict(required=False),
            state=dict(
                default="present",
                choices=[
                    "present", "installed",
                    "absent", "removed", "uninstalled",
                ],
            ),
        ),
        supports_check_mode=True,
    )

    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')

    p = module.params

    if p['name']:
        casks = p['name'].split(',')
    else:
        casks = None

    path = p['path']
    if path:
        path = path.split(':')
    else:
        path = ['/usr/local/bin']

    state = p['state']
    if state in ('present', 'installed'):
        state = 'installed'
    if state in ('absent', 'removed', 'uninstalled'):
        state = 'absent'

    brew_cask = HomebrewCask(module=module, path=path, casks=casks,
                             state=state)
    (failed, changed, message) = brew_cask.run()
    if failed:
        module.fail_json(msg=message)
    else:
        module.exit_json(changed=changed, msg=message)

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()

