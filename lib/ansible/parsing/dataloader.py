# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import copy
import os
import json
import subprocess
from yaml import YAMLError
from ansible.compat.six import text_type, string_types

from ansible.errors import AnsibleFileNotFound, AnsibleParserError, AnsibleError
from ansible.errors.yaml_strings import YAML_SYNTAX_ERROR
from ansible.parsing.vault import VaultLib
from ansible.parsing.quoting import unquote
from ansible.parsing.yaml.loader import AnsibleLoader
from ansible.parsing.yaml.objects import AnsibleBaseYAMLObject, AnsibleUnicode
from ansible.module_utils.basic import is_executable
from ansible.utils.path import unfrackpath
from ansible.utils.unicode import to_unicode, to_bytes

class DataLoader():

    '''
    The DataLoader class is used to load and parse YAML or JSON content,
    either from a given file name or from a string that was previously
    read in through other means. A Vault password can be specified, and
    any vault-encrypted files will be decrypted.

    Data read from files will also be cached, so the file will never be
    read from disk more than once.

    Usage:

        dl = DataLoader()
        # optionally: dl.set_vault_password('foo')
        ds = dl.load('...')
        ds = dl.load_from_file('/path/to/file')
    '''

    def __init__(self):
        self._basedir = '.'
        self._FILE_CACHE = dict()

        # initialize the vault stuff with an empty password
        self.set_vault_password(None)

    def set_vault_password(self, vault_password):
        self._vault_password = vault_password
        self._vault = VaultLib(password=vault_password)

    def load(self, data, file_name='<string>', show_content=True):
        '''
        Creates a python datastructure from the given data, which can be either
        a JSON or YAML string.
        '''
        new_data = None
        try:
            # we first try to load this data as JSON
            new_data = json.loads(data)
        except:
            # must not be JSON, let the rest try
            if isinstance(data, AnsibleUnicode):
                # The PyYAML's libyaml bindings use PyUnicode_CheckExact so
                # they are unable to cope with our subclass.
                # Unwrap and re-wrap the unicode so we can keep track of line
                # numbers
                in_data = text_type(data)
            else:
                in_data = data
            try:
                new_data = self._safe_load(in_data, file_name=file_name)
            except YAMLError as yaml_exc:
                self._handle_error(yaml_exc, file_name, show_content)

            if isinstance(data, AnsibleUnicode):
                new_data = AnsibleUnicode(new_data)
                new_data.ansible_pos = data.ansible_pos

        return new_data

    def load_from_file(self, file_name):
        ''' Loads data from a file, which can contain either JSON or YAML.  '''

        file_name = self.path_dwim(file_name)

        # if the file has already been read in and cached, we'll
        # return those results to avoid more file/vault operations
        if file_name in self._FILE_CACHE:
            parsed_data = self._FILE_CACHE[file_name]
        else:
            # read the file contents and load the data structure from them
            (file_data, show_content) = self._get_file_contents(file_name)
            parsed_data = self.load(data=file_data, file_name=file_name, show_content=show_content)

            # cache the file contents for next time
            self._FILE_CACHE[file_name] = parsed_data

        # return a deep copy here, so the cache is not affected
        return copy.deepcopy(parsed_data)

    def path_exists(self, path):
        path = self.path_dwim(path)
        return os.path.exists(to_bytes(path, errors='strict'))

    def is_file(self, path):
        path = self.path_dwim(path)
        return os.path.isfile(to_bytes(path, errors='strict')) or path == os.devnull

    def is_directory(self, path):
        path = self.path_dwim(path)
        return os.path.isdir(to_bytes(path, errors='strict'))

    def list_directory(self, path):
        path = self.path_dwim(path)
        return os.listdir(path)

    def is_executable(self, path):
        '''is the given path executable?'''
        path = self.path_dwim(path)
        return is_executable(path)

    def _safe_load(self, stream, file_name=None):
        ''' Implements yaml.safe_load(), except using our custom loader class. '''

        loader = AnsibleLoader(stream, file_name)
        try:
            return loader.get_single_data()
        finally:
            try:
                loader.dispose()
            except AttributeError:
                pass # older versions of yaml don't have dispose function, ignore

    def _get_file_contents(self, file_name):
        '''
        Reads the file contents from the given file name, and will decrypt them
        if they are found to be vault-encrypted.
        '''
        if not file_name or not isinstance(file_name, string_types):
            raise AnsibleParserError("Invalid filename: '%s'" % str(file_name))

        if not self.path_exists(file_name) or not self.is_file(file_name):
            raise AnsibleFileNotFound("the file_name '%s' does not exist, or is not readable" % file_name)

        show_content = True
        try:
            with open(file_name, 'rb') as f:
                data = f.read()
                if self._vault.is_encrypted(data):
                    data = self._vault.decrypt(data)
                    show_content = False

            data = to_unicode(data, errors='strict')
            return (data, show_content)

        except (IOError, OSError) as e:
            raise AnsibleParserError("an error occurred while trying to read the file '%s': %s" % (file_name, str(e)))

    def _handle_error(self, yaml_exc, file_name, show_content):
        '''
        Optionally constructs an object (AnsibleBaseYAMLObject) to encapsulate the
        file name/position where a YAML exception occurred, and raises an AnsibleParserError
        to display the syntax exception information.
        '''

        # if the YAML exception contains a problem mark, use it to construct
        # an object the error class can use to display the faulty line
        err_obj = None
        if hasattr(yaml_exc, 'problem_mark'):
            err_obj = AnsibleBaseYAMLObject()
            err_obj.ansible_pos = (file_name, yaml_exc.problem_mark.line + 1, yaml_exc.problem_mark.column + 1)

        raise AnsibleParserError(YAML_SYNTAX_ERROR, obj=err_obj, show_content=show_content)

    def get_basedir(self):
        ''' returns the current basedir '''
        return self._basedir

    def set_basedir(self, basedir):
        ''' sets the base directory, used to find files when a relative path is given '''

        if basedir is not None:
            self._basedir = to_unicode(basedir)

    def path_dwim(self, given):
        '''
        make relative paths work like folks expect.
        '''

        given = unquote(given)
        given = to_unicode(given, errors='strict')

        if given.startswith(u"/"):
            return os.path.abspath(given)
        elif given.startswith(u"~"):
            return os.path.abspath(os.path.expanduser(given))
        else:
            basedir = to_unicode(self._basedir, errors='strict')
            return os.path.abspath(os.path.join(basedir, given))

    def path_dwim_relative(self, path, dirname, source):
        '''
        find one file in either a role or playbook dir with or without
        explicitly named dirname subdirs

        Used in action plugins and lookups to find supplemental files that
        could be in either place.
        '''

        search = []
        isrole = False

        # I have full path, nothing else needs to be looked at
        if source.startswith('~') or source.startswith('/'):
            search.append(self.path_dwim(source))
        else:
            # base role/play path + templates/files/vars + relative filename
            search.append(os.path.join(path, dirname, source))

            basedir = unfrackpath(path)

            # is it a role and if so make sure you get correct base path
            if path.endswith('tasks') and os.path.exists(to_bytes(os.path.join(path,'main.yml'), errors='strict')) \
                or os.path.exists(to_bytes(os.path.join(path,'tasks/main.yml'), errors='strict')):
                isrole = True
                if path.endswith('tasks'):
                    basedir = unfrackpath(os.path.dirname(path))

            cur_basedir = self._basedir
            self.set_basedir(basedir)
            # resolved base role/play path + templates/files/vars + relative filename
            search.append(self.path_dwim(os.path.join(basedir, dirname, source)))
            self.set_basedir(cur_basedir)

            if isrole and not source.endswith(dirname):
                # look in role's tasks dir w/o dirname
                search.append(self.path_dwim(os.path.join(basedir, 'tasks', source)))

            # try to create absolute path for loader basedir + templates/files/vars + filename
            search.append(self.path_dwim(os.path.join(dirname,source)))
            search.append(self.path_dwim(os.path.join(basedir, source)))

            # try to create absolute path for loader basedir + filename
            search.append(self.path_dwim(source))

        for candidate in search:
            if os.path.exists(to_bytes(candidate, errors='strict')):
                break

        return candidate

    def read_vault_password_file(self, vault_password_file):
        """
        Read a vault password from a file or if executable, execute the script and
        retrieve password from STDOUT
        """

        this_path = os.path.realpath(to_bytes(os.path.expanduser(vault_password_file), errors='strict'))
        if not os.path.exists(to_bytes(this_path, errors='strict')):
            raise AnsibleFileNotFound("The vault password file %s was not found" % this_path)

        if self.is_executable(this_path):
            try:
                # STDERR not captured to make it easier for users to prompt for input in their scripts
                p = subprocess.Popen(this_path, stdout=subprocess.PIPE)
            except OSError as e:
                raise AnsibleError("Problem running vault password script %s (%s). If this is not a script, remove the executable bit from the file." % (' '.join(this_path), e))
            stdout, stderr = p.communicate()
            self.set_vault_password(stdout.strip('\r\n'))
        else:
            try:
                f = open(this_path, "rb")
                self.set_vault_password(f.read().strip())
                f.close()
            except (OSError, IOError) as e:
                raise AnsibleError("Could not read vault password file %s: %s" % (this_path, e))
