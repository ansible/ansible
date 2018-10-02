#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Daniel Jaouen <dcj24@cornell.edu>
#
# Based on macports (Jimmy Tang <jcftang@gmail.com>)
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

RETURN = ''' # '''

DOCUMENTATION = '''
---
module: homebrew_bundle
author:
    - "Daniel Jaouen (@danieljaouen)"
requirements:
   - "python >= 2.6"
short_description: Manager for Homebrew bundles
description:
    - Manages Homebrew bundles
version_added: "2.8"
options:
    state:
        description:
            - the state of the homebrew bundle
        choices: ['installed', 'dumped', 'cleanup']
        default: installed
    file_path:
        description:
            - The path of the Brewfile. Defaults to ~/.Brewfile.
        required: false
        default: ~/.Brewfile
    path:
        description:
            - "A ':' separated list of paths to search for 'brew' executable.
              Since a package (I(formula) in homebrew parlance) location is prefixed relative to the actual path of I(brew) command,
              providing an alternative I(brew) path enables managing different set of packages in an alternative location in the system."
        default: '/usr/local/bin'
    install_options:
        description:
            - options flags to install a package
        aliases: ['options']
        version_added: "1.4"
'''
EXAMPLES = '''
# Install from a Brewfile.
- homebrew_bundle:
    state: installed
    file_path: /Users/dan/Brewfile

# Dump to a Brewfile.
- homebrew_bundle:
    state: dumped
    file_path: /Users/dan

# Cleanup from a Brewfile.
- homebrew_bundle:
    state: cleanup
    file_path: /Users/dan
'''

import os.path
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems, string_types


# exceptions -------------------------------------------------------------- {{{
class HomebrewBundleException(Exception):
    pass
# /exceptions ------------------------------------------------------------- }}}


# utils ------------------------------------------------------------------- {{{
def _create_regex_group(s):
    lines = (line.strip() for line in s.split('\n') if line.strip())
    chars = filter(None, (line.split('#')[0].strip() for line in lines))
    group = r'[^' + r''.join(chars) + r']'
    return re.compile(group)
# /utils ------------------------------------------------------------------ }}}


class HomebrewBundle(object):
    '''A class to manage Homebrew packages.'''

    # class regexes ------------------------------------------------ {{{
    VALID_PATH_CHARS = r'''
        \w                  # alphanumeric characters (i.e., [a-zA-Z0-9_])
        \s                  # spaces
        :                   # colons
        {sep}               # the OS-specific path separator
        .                   # dots
        -                   # dashes
    '''.format(sep=os.path.sep)

    VALID_BREW_PATH_CHARS = r'''
        \w                  # alphanumeric characters (i.e., [a-zA-Z0-9_])
        \s                  # spaces
        {sep}               # the OS-specific path separator
        .                   # dots
        -                   # dashes
    '''.format(sep=os.path.sep)

    VALID_FILE_PATH_CHARS = r'''
        \w                  # alphanumeric characters (i.e., [a-zA-Z0-9_])
        \s                  # spaces
        {sep}               # the OS-specific path separator
        .                   # dots
        -                   # dashes
    '''.format(sep=os.path.sep)

    INVALID_PATH_REGEX = _create_regex_group(VALID_PATH_CHARS)
    INVALID_BREW_PATH_REGEX = _create_regex_group(VALID_BREW_PATH_CHARS)
    INVALID_FILE_PATH_REGEX = _create_regex_group(VALID_FILE_PATH_CHARS)
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
             - dots
             - spaces
             - colons
             - os.path.sep
        '''

        if isinstance(path, string_types):
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
             - dots
             - spaces
             - os.path.sep
        '''

        if brew_path is None:
            return True

        return (
            isinstance(brew_path, string_types)
            and not cls.INVALID_BREW_PATH_REGEX.search(brew_path)
        )

    @classmethod
    def valid_file_path(cls, file_path):
        '''
        `file_path` must be:
         - a string containing only:
             - alphanumeric characters
             - dashes
             - dots
             - spaces
             - os.path.sep
        '''

        return (
            isinstance(file_path, string_types)
            and not cls.INVALID_FILE_PATH_REGEX.search(file_path)
        )

    @classmethod
    def valid_state(cls, state):
        '''
        A valid state is one of:
            - installed
            - dumped
            - cleanup
        '''

        return (
            isinstance(state, string_types)
            and state.lower() in (
                'installed',
                'dumped',
                'cleanup',
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
            raise HomebrewBundleException(self.message)

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
            raise HomebrewBundleException(self.message)

        else:
            if isinstance(path, string_types):
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
            raise HomebrewBundleException(self.message)

        else:
            self._brew_path = brew_path
            return brew_path

    @property
    def file_path(self):
        return self._file_path

    @file_path.setter
    def file_path(self, file_path):
        if not self.valid_file_path(file_path):
            self._file_path = None
            self.failed = True
            self.message = 'Invalid file_path: {0}.'.format(file_path)
            raise HomebrewBundleException(self.message)

        else:
            self._file_path = file_path
            return file_path

    @property
    def params(self):
        return self._params

    @params.setter
    def params(self, params):
        self._params = self.module.params
        return self._params

    # /class properties -------------------------------------------- }}}

    def __init__(self, module, path, file_path, state=None,
                 install_options=None):
        if not install_options:
            install_options = list()
        self._setup_status_vars()
        self._setup_instance_vars(module=module, path=path, state=state,
                                  file_path=file_path,
                                  install_options=install_options, )

        self._prep()

    # prep --------------------------------------------------------- {{{
    def _setup_status_vars(self):
        self.failed = False
        self.changed = False
        self.changed_count = 0
        self.unchanged_count = 0
        self.message = ''

    def _setup_instance_vars(self, **kwargs):
        for key, val in iteritems(kwargs):
            setattr(self, key, val)

    def _prep(self):
        self._prep_brew_path()

    def _prep_brew_path(self):
        if not self.module:
            self.brew_path = None
            self.failed = True
            self.message = 'AnsibleModule not set.'
            raise HomebrewBundleException(self.message)

        self.brew_path = self.module.get_bin_path(
            'brew',
            required=True,
            opt_dirs=self.path,
        )
        if not self.brew_path:
            self.brew_path = None
            self.failed = True
            self.message = 'Unable to locate homebrew executable.'
            raise HomebrewBundleException('Unable to locate homebrew executable.')

        return self.brew_path

    def _status(self):
        return (self.failed, self.changed, self.message)
    # /prep -------------------------------------------------------- }}}

    def run(self):
        try:
            self._run()
        except HomebrewBundleException:
            pass

        if not self.failed and (self.changed_count + self.unchanged_count > 1):
            self.message = "Changed: %d, Unchanged: %d" % (
                self.changed_count,
                self.unchanged_count,
            )
        (failed, changed, message) = self._status()

        return (failed, changed, message)

    # commands ----------------------------------------------------- {{{
    def _run(self):
        if self.state == 'installed':
            return self._install_bundle()
        elif self.state == 'dumped':
            return self._dump_bundle()
        elif self.state == 'cleanup':
            return self._cleanup_bundle()

    # installed ---------------------------------- {{{
    def _install_bundle(self):
        if self.module.check_mode:
            self.changed = True
            self.message = 'Bundle would be installed: {0}'.format(
                self.file_path
            )
            raise HomebrewBundleException(self.message)

        opts = (
            [self.brew_path, 'bundle', 'install']
            + ['--file=' + self.file_path]
            + self.install_options
        )
        cmd = [opt for opt in opts if opt]
        rc, out, err = self.module.run_command(cmd)

        if rc == 0:
            self.changed = True
            self.message = 'Bundle installed: {0}'.format(self.file_path)
            return True
        else:
            self.failed = True
            self.message = err.strip()
            raise HomebrewBundleException(self.message)
    # /installed --------------------------------- }}}

    # dumped ------------------------------------- {{{
    def _dump_bundle(self):
        if self.module.check_mode:
            self.changed = True
            self.message = 'Bundle would be dumped: {0}'.format(
                self.file_path
            )
            raise HomebrewBundleException(self.message)

        opts = (
            [self.brew_path, 'bundle', 'dump']
            + ['--file=' + self.file_path]
            + self.install_options
        )
        cmd = [opt for opt in opts if opt]
        rc, out, err = self.module.run_command(cmd)

        if rc == 0:
            self.changed = True
            self.message = 'Bundle dumped: {0}'.format(self.file_path)
            return True
        else:
            self.failed = True
            self.message = err.strip()
            raise HomebrewBundleException(self.message)
    # /dumped ------------------------------------ }}}

    # cleanup ------------------------------------ {{{
    def _cleanup_bundle(self):
        if self.module.check_mode:
            self.changed = True
            self.message = 'Bundle would be cleaned up: {0}'.format(
                self.file_path
            )
            raise HomebrewBundleException(self.message)

        opts = (
            [self.brew_path, 'bundle', 'cleanup']
            + ['--file=' + self.file_path]
            + self.install_options
        )
        cmd = [opt for opt in opts if opt]
        rc, out, err = self.module.run_command(cmd)

        if rc == 0:
            self.changed = True
            self.message = 'Bundle cleaned up: {0}'.format(self.file_path)
            return True
        else:
            self.failed = True
            self.message = err.strip()
            raise HomebrewBundleException(self.message)
    # /cleanup ------------------------------- }}}
    # /commands ---------------------------------------------------- }}}


def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(
                default="/usr/local/bin",
                required=False,
                type='path',
            ),
            file_path=dict(
                default="~/.Brewfile",
                required=False,
                type='path',
            ),
            state=dict(
                default="installed",
                choices=[
                    "installed",
                    "dumped",
                    "cleanup",
                ],
            ),
            install_options=dict(
                default=None,
                aliases=['options'],
                type='list',
            )
        ),
        supports_check_mode=True,
    )

    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')

    p = module.params

    path = p['path']
    if path:
        path = path.split(':')

    file_path = p['file_path']

    state = p['state']

    p['install_options'] = p['install_options'] or []
    install_options = ['--{0}'.format(install_option)
                       for install_option in p['install_options']]

    brew_bundle = HomebrewBundle(module=module, path=path, file_path=file_path,
                                 state=state, install_options=install_options)
    (failed, changed, message) = brew_bundle.run()
    if failed:
        module.fail_json(msg=message)
    else:
        module.exit_json(changed=changed, msg=message)


if __name__ == '__main__':
    main()
