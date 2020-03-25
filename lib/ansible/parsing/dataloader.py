# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import copy
import os
import os.path
import re
import tempfile

from ansible import constants as C
from ansible.errors import AnsibleFileNotFound, AnsibleParserError
from ansible.module_utils.basic import is_executable
from ansible.module_utils.six import binary_type, text_type
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.parsing.quoting import unquote
from ansible.parsing.utils.yaml import from_yaml
from ansible.parsing.vault import VaultLib, b_HEADER, is_encrypted, is_encrypted_file, parse_vaulttext_envelope
from ansible.utils.path import unfrackpath
from ansible.utils.display import Display

display = Display()


# Tries to determine if a path is inside a role, last dir must be 'tasks'
# this is not perfect but people should really avoid 'tasks' dirs outside roles when using Ansible.
RE_TASKS = re.compile(u'(?:^|%s)+tasks%s?$' % (os.path.sep, os.path.sep))


class DataLoader:

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

        # NOTE: not effective with forks as the main copy does not get updated.
        # avoids rereading files
        self._FILE_CACHE = dict()

        # NOTE: not thread safe, also issues with forks not returning data to main proc
        #       so they need to be cleaned independantly. See WorkerProcess for example.
        # used to keep track of temp files for cleaning
        self._tempfiles = set()

        # initialize the vault stuff with an empty password
        # TODO: replace with a ref to something that can get the password
        #       a creds/auth provider
        # self.set_vault_password(None)
        self._vaults = {}
        self._vault = VaultLib()
        self.set_vault_secrets(None)

    # TODO: since we can query vault_secrets late, we could provide this to DataLoader init
    def set_vault_secrets(self, vault_secrets):
        self._vault.secrets = vault_secrets

    def load(self, data, file_name='<string>', show_content=True):
        '''Backwards compat for now'''
        return from_yaml(data, file_name, show_content, self._vault.secrets)

    def load_from_file(self, file_name, cache=True, unsafe=False):
        ''' Loads data from a file, which can contain either JSON or YAML.  '''

        file_name = self.path_dwim(file_name)
        display.debug("Loading data from %s" % file_name)

        # if the file has already been read in and cached, we'll
        # return those results to avoid more file/vault operations
        if cache and file_name in self._FILE_CACHE:
            parsed_data = self._FILE_CACHE[file_name]
        else:
            # read the file contents and load the data structure from them
            (b_file_data, show_content) = self._get_file_contents(file_name)

            file_data = to_text(b_file_data, errors='surrogate_or_strict')
            parsed_data = self.load(data=file_data, file_name=file_name, show_content=show_content)

            # cache the file contents for next time
            self._FILE_CACHE[file_name] = parsed_data

        if unsafe:
            return parsed_data
        else:
            # return a deep copy here, so the cache is not affected
            return copy.deepcopy(parsed_data)

    def path_exists(self, path):
        path = self.path_dwim(path)
        return os.path.exists(to_bytes(path, errors='surrogate_or_strict'))

    def is_file(self, path):
        path = self.path_dwim(path)
        return os.path.isfile(to_bytes(path, errors='surrogate_or_strict')) or path == os.devnull

    def is_directory(self, path):
        path = self.path_dwim(path)
        return os.path.isdir(to_bytes(path, errors='surrogate_or_strict'))

    def list_directory(self, path):
        path = self.path_dwim(path)
        return os.listdir(path)

    def is_executable(self, path):
        '''is the given path executable?'''
        path = self.path_dwim(path)
        return is_executable(path)

    def _decrypt_if_vault_data(self, b_vault_data, b_file_name=None):
        '''Decrypt b_vault_data if encrypted and return b_data and the show_content flag'''

        if not is_encrypted(b_vault_data):
            show_content = True
            return b_vault_data, show_content

        b_ciphertext, b_version, cipher_name, vault_id = parse_vaulttext_envelope(b_vault_data)
        b_data = self._vault.decrypt(b_vault_data, filename=b_file_name)

        show_content = False
        return b_data, show_content

    def _get_file_contents(self, file_name):
        '''
        Reads the file contents from the given file name

        If the contents are vault-encrypted, it will decrypt them and return
        the decrypted data

        :arg file_name: The name of the file to read.  If this is a relative
            path, it will be expanded relative to the basedir
        :raises AnsibleFileNotFound: if the file_name does not refer to a file
        :raises AnsibleParserError: if we were unable to read the file
        :return: Returns a byte string of the file contents
        '''
        if not file_name or not isinstance(file_name, (binary_type, text_type)):
            raise AnsibleParserError("Invalid filename: '%s'" % to_native(file_name))

        b_file_name = to_bytes(self.path_dwim(file_name))
        # This is what we really want but have to fix unittests to make it pass
        # if not os.path.exists(b_file_name) or not os.path.isfile(b_file_name):
        if not self.path_exists(b_file_name):
            raise AnsibleFileNotFound("Unable to retrieve file contents", file_name=file_name)

        try:
            with open(b_file_name, 'rb') as f:
                data = f.read()
                return self._decrypt_if_vault_data(data, b_file_name)
        except (IOError, OSError) as e:
            raise AnsibleParserError("an error occurred while trying to read the file '%s': %s" % (file_name, to_native(e)), orig_exc=e)

    def get_basedir(self):
        ''' returns the current basedir '''
        return self._basedir

    def set_basedir(self, basedir):
        ''' sets the base directory, used to find files when a relative path is given '''

        if basedir is not None:
            self._basedir = to_text(basedir)

    def path_dwim(self, given):
        '''
        make relative paths work like folks expect.
        '''

        given = unquote(given)
        given = to_text(given, errors='surrogate_or_strict')

        if given.startswith(to_text(os.path.sep)) or given.startswith(u'~'):
            path = given
        else:
            basedir = to_text(self._basedir, errors='surrogate_or_strict')
            path = os.path.join(basedir, given)

        return unfrackpath(path, follow=False)

    def _is_role(self, path):
        ''' imperfect role detection, roles are still valid w/o tasks|meta/main.yml|yaml|etc '''

        b_path = to_bytes(path, errors='surrogate_or_strict')
        b_upath = to_bytes(unfrackpath(path, follow=False), errors='surrogate_or_strict')

        for b_finddir in (b'meta', b'tasks'):
            for b_suffix in (b'.yml', b'.yaml', b''):
                b_main = b'main%s' % (b_suffix)
                b_tasked = os.path.join(b_finddir, b_main)

                if (
                    RE_TASKS.search(path) and
                    os.path.exists(os.path.join(b_path, b_main)) or
                    os.path.exists(os.path.join(b_upath, b_tasked)) or
                    os.path.exists(os.path.join(os.path.dirname(b_path), b_tasked))
                ):
                    return True
        return False

    def path_dwim_relative(self, path, dirname, source, is_role=False):
        '''
        find one file in either a role or playbook dir with or without
        explicitly named dirname subdirs

        Used in action plugins and lookups to find supplemental files that
        could be in either place.
        '''

        search = []
        source = to_text(source, errors='surrogate_or_strict')

        # I have full path, nothing else needs to be looked at
        if source.startswith(to_text(os.path.sep)) or source.startswith(u'~'):
            search.append(unfrackpath(source, follow=False))
        else:
            # base role/play path + templates/files/vars + relative filename
            search.append(os.path.join(path, dirname, source))
            basedir = unfrackpath(path, follow=False)

            # not told if role, but detect if it is a role and if so make sure you get correct base path
            if not is_role:
                is_role = self._is_role(path)

            if is_role and RE_TASKS.search(path):
                basedir = unfrackpath(os.path.dirname(path), follow=False)

            cur_basedir = self._basedir
            self.set_basedir(basedir)
            # resolved base role/play path + templates/files/vars + relative filename
            search.append(unfrackpath(os.path.join(basedir, dirname, source), follow=False))
            self.set_basedir(cur_basedir)

            if is_role and not source.endswith(dirname):
                # look in role's tasks dir w/o dirname
                search.append(unfrackpath(os.path.join(basedir, 'tasks', source), follow=False))

            # try to create absolute path for loader basedir + templates/files/vars + filename
            search.append(unfrackpath(os.path.join(dirname, source), follow=False))

            # try to create absolute path for loader basedir
            search.append(unfrackpath(os.path.join(basedir, source), follow=False))

            # try to create absolute path for  dirname + filename
            search.append(self.path_dwim(os.path.join(dirname, source)))

            # try to create absolute path for filename
            search.append(self.path_dwim(source))

        for candidate in search:
            if os.path.exists(to_bytes(candidate, errors='surrogate_or_strict')):
                break

        return candidate

    def path_dwim_relative_stack(self, paths, dirname, source, is_role=False):
        '''
        find one file in first path in stack taking roles into account and adding play basedir as fallback

        :arg paths: A list of text strings which are the paths to look for the filename in.
        :arg dirname: A text string representing a directory.  The directory
            is prepended to the source to form the path to search for.
        :arg source: A text string which is the filename to search for
        :rtype: A text string
        :returns: An absolute path to the filename ``source`` if found
        :raises: An AnsibleFileNotFound Exception if the file is found to exist in the search paths
        '''
        b_dirname = to_bytes(dirname)
        b_source = to_bytes(source)

        result = None
        search = []
        if source is None:
            display.warning('Invalid request to find a file that matches a "null" value')
        elif source and (source.startswith('~') or source.startswith(os.path.sep)):
            # path is absolute, no relative needed, check existence and return source
            test_path = unfrackpath(b_source, follow=False)
            if os.path.exists(to_bytes(test_path, errors='surrogate_or_strict')):
                result = test_path
        else:
            display.debug(u'evaluation_path:\n\t%s' % '\n\t'.join(paths))
            for path in paths:
                upath = unfrackpath(path, follow=False)
                b_upath = to_bytes(upath, errors='surrogate_or_strict')
                b_pb_base_dir = os.path.dirname(b_upath)

                # if path is in role and 'tasks' not there already, add it into the search
                if (is_role or self._is_role(path)) and b_pb_base_dir.endswith(b'/tasks'):
                    search.append(os.path.join(os.path.dirname(b_pb_base_dir), b_dirname, b_source))
                    search.append(os.path.join(b_pb_base_dir, b_source))
                else:
                    # don't add dirname if user already is using it in source
                    if b_source.split(b'/')[0] != dirname:
                        search.append(os.path.join(b_upath, b_dirname, b_source))
                    search.append(os.path.join(b_upath, b_source))

            # always append basedir as last resort
            # don't add dirname if user already is using it in source
            if b_source.split(b'/')[0] != dirname:
                search.append(os.path.join(to_bytes(self.get_basedir()), b_dirname, b_source))
            search.append(os.path.join(to_bytes(self.get_basedir()), b_source))

            display.debug(u'search_path:\n\t%s' % to_text(b'\n\t'.join(search)))
            for b_candidate in search:
                display.vvvvv(u'looking for "%s" at "%s"' % (source, to_text(b_candidate)))
                if os.path.exists(b_candidate):
                    result = to_text(b_candidate)
                    break

        if result is None:
            raise AnsibleFileNotFound(file_name=source, paths=[to_text(p) for p in search])

        return result

    def _create_content_tempfile(self, content):
        ''' Create a tempfile containing defined content '''
        fd, content_tempfile = tempfile.mkstemp(dir=C.DEFAULT_LOCAL_TMP)
        f = os.fdopen(fd, 'wb')
        content = to_bytes(content)
        try:
            f.write(content)
        except Exception as err:
            os.remove(content_tempfile)
            raise Exception(err)
        finally:
            f.close()
        return content_tempfile

    def get_real_file(self, file_path, decrypt=True):
        """
        If the file is vault encrypted return a path to a temporary decrypted file
        If the file is not encrypted then the path is returned
        Temporary files are cleanup in the destructor
        """

        if not file_path or not isinstance(file_path, (binary_type, text_type)):
            raise AnsibleParserError("Invalid filename: '%s'" % to_native(file_path))

        b_file_path = to_bytes(file_path, errors='surrogate_or_strict')
        if not self.path_exists(b_file_path) or not self.is_file(b_file_path):
            raise AnsibleFileNotFound(file_name=file_path)

        real_path = self.path_dwim(file_path)

        try:
            if decrypt:
                with open(to_bytes(real_path), 'rb') as f:
                    # Limit how much of the file is read since we do not know
                    # whether this is a vault file and therefore it could be very
                    # large.
                    if is_encrypted_file(f, count=len(b_HEADER)):
                        # if the file is encrypted and no password was specified,
                        # the decrypt call would throw an error, but we check first
                        # since the decrypt function doesn't know the file name
                        data = f.read()
                        if not self._vault.secrets:
                            raise AnsibleParserError("A vault password or secret must be specified to decrypt %s" % to_native(file_path))

                        data = self._vault.decrypt(data, filename=real_path)
                        # Make a temp file
                        real_path = self._create_content_tempfile(data)
                        self._tempfiles.add(real_path)

            return real_path

        except (IOError, OSError) as e:
            raise AnsibleParserError("an error occurred while trying to read the file '%s': %s" % (to_native(real_path), to_native(e)), orig_exc=e)

    def cleanup_tmp_file(self, file_path):
        """
        Removes any temporary files created from a previous call to
        get_real_file. file_path must be the path returned from a
        previous call to get_real_file.
        """
        if file_path in self._tempfiles:
            os.unlink(file_path)
            self._tempfiles.remove(file_path)

    def cleanup_all_tmp_files(self):
        """
        Removes all temporary files that DataLoader has created
        NOTE: not thread safe, forks also need special handling see __init__ for details.
        """
        for f in self._tempfiles:
            try:
                self.cleanup_tmp_file(f)
            except Exception as e:
                display.warning("Unable to cleanup temp files: %s" % to_text(e))

    def find_vars_files(self, path, name, extensions=None, allow_dir=True):
        """
        Find vars files in a given path with specified name. This will find
        files in a dir named <name>/ or a file called <name> ending in known
        extensions.
        """

        b_path = to_bytes(os.path.join(path, name))
        found = []

        if extensions is None:
            # Look for file with no extension first to find dir before file
            extensions = [''] + C.YAML_FILENAME_EXTENSIONS
        # add valid extensions to name
        for ext in extensions:

            if '.' in ext:
                full_path = b_path + to_bytes(ext)
            elif ext:
                full_path = b'.'.join([b_path, to_bytes(ext)])
            else:
                full_path = b_path

            if self.path_exists(full_path):
                if self.is_directory(full_path):
                    if allow_dir:
                        found.extend(self._get_dir_vars_files(to_text(full_path), extensions))
                    else:
                        continue
                else:
                    found.append(full_path)
                break
        return found

    def _get_dir_vars_files(self, path, extensions):
        found = []
        for spath in sorted(self.list_directory(path)):
            if not spath.startswith(u'.') and not spath.endswith(u'~'):  # skip hidden and backups

                ext = os.path.splitext(spath)[-1]
                full_spath = os.path.join(path, spath)

                if self.is_directory(full_spath) and not ext:  # recursive search if dir
                    found.extend(self._get_dir_vars_files(full_spath, extensions))
                elif self.is_file(full_spath) and (not ext or to_text(ext) in extensions):
                    # only consider files with valid extensions or no extension
                    found.append(full_spath)

        return found
