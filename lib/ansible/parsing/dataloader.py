# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import copy
import os
import os.path
import pathlib
import re
import tempfile
import typing as t

from ansible import constants as C
from ansible.errors import AnsibleFileNotFound, AnsibleParserError
from ansible._internal._errors import _error_utils
from ansible.module_utils.basic import is_executable
from ansible._internal._datatag._tags import Origin, TrustedAsTemplate, SourceWasEncrypted
from ansible.module_utils._internal._datatag import AnsibleTagHelper
from ansible.module_utils.common.text.converters import to_bytes, to_text
from ansible.parsing.quoting import unquote
from ansible.parsing.utils.yaml import from_yaml
from ansible.parsing.vault import VaultLib, is_encrypted, is_encrypted_file, PromptVaultSecret
from ansible.utils.path import unfrackpath
from ansible.utils.display import Display

display = Display()


# Tries to determine if a path is inside a role, last dir must be 'tasks'
# this is not perfect but people should really avoid 'tasks' dirs outside roles when using Ansible.
RE_TASKS = re.compile('(?:^|%s)+tasks%s?$' % (os.path.sep, os.path.sep))


class DataLoader:

    """
    The DataLoader class is used to load and parse YAML or JSON content,
    either from a given file name or from a string that was previously
    read in through other means. A Vault password can be specified, and
    any vault-encrypted files will be decrypted.

    Data read from files will also be cached, so the file will never be
    read from disk more than once.

    Usage:

        dl = DataLoader()
        # optionally: dl.set_vault_secrets([('default', ansible.parsing.vault.PromptVaultSecret(...),)])
        ds = dl.load('...')
        ds = dl.load_from_file('/path/to/file')
    """

    def __init__(self) -> None:

        self._basedir: str = os.path.abspath('.')

        # NOTE: not effective with forks as the main copy does not get updated.
        # avoids rereading files
        self._FILE_CACHE: dict[str, object] = {}

        # NOTE: not thread safe, also issues with forks not returning data to main proc
        #       so they need to be cleaned independently. See WorkerProcess for example.
        # used to keep track of temp files for cleaning
        self._tempfiles: set[str] = set()

        # initialize the vault stuff with an empty password
        # TODO: replace with a ref to something that can get the password
        #       a creds/auth provider
        self._vault = VaultLib()
        self.set_vault_secrets(None)

    # TODO: since we can query vault_secrets late, we could provide this to DataLoader init
    def set_vault_secrets(self, vault_secrets: list[tuple[str, PromptVaultSecret]] | None) -> None:
        self._vault.secrets = vault_secrets

    def load(
            self,
            data: str,
            file_name: str | None = None,  # DTFIX-FUTURE: consider deprecating this in favor of tagging Origin on data
            show_content: bool = True,  # DTFIX-FUTURE: consider future deprecation, but would need RedactAnnotatedSourceContext public
            json_only: bool = False,
    ) -> t.Any:
        """Backwards compat for now"""
        with _error_utils.RedactAnnotatedSourceContext.when(not show_content):
            return from_yaml(data=data, file_name=file_name, json_only=json_only)

    def load_from_file(self, file_name: str, cache: str = 'all', unsafe: bool = False, json_only: bool = False, trusted_as_template: bool = False) -> t.Any:
        """
        Loads data from a file, which can contain either JSON or YAML.

        :param file_name: The name of the file to load data from.
        :param cache: Options for caching: none|all|vaulted
        :param unsafe: If True, returns the parsed data as-is without deep copying.
        :param json_only: If True, only loads JSON data from the file.
        :return: The loaded data, optionally deep-copied for safety.
        """

        # Resolve the file name
        file_name = self.path_dwim(file_name)

        # Log the file being loaded
        display.debug("Loading data from %s" % file_name)

        # Check if the file has been cached and use the cached data if available
        if cache != 'none' and file_name in self._FILE_CACHE:
            parsed_data = self._FILE_CACHE[file_name]
        else:
            file_data = self.get_text_file_contents(file_name)

            if trusted_as_template:
                file_data = TrustedAsTemplate().tag(file_data)

            parsed_data = self.load(data=file_data, file_name=file_name, json_only=json_only)

            # only tagging the container, used by include_vars to determine if vars should be shown or not
            # this is a temporary measure until a proper data senitivity system is in place
            if SourceWasEncrypted.is_tagged_on(file_data):
                parsed_data = SourceWasEncrypted().tag(parsed_data)

            # Cache the file contents for next time based on the cache option
            if cache == 'all':
                self._FILE_CACHE[file_name] = parsed_data
            elif cache == 'vaulted' and SourceWasEncrypted.is_tagged_on(file_data):
                self._FILE_CACHE[file_name] = parsed_data

        # Return the parsed data, optionally deep-copied for safety
        if unsafe:
            return parsed_data
        else:
            return copy.deepcopy(parsed_data)

    def path_exists(self, path: str) -> bool:
        path = self.path_dwim(path)
        return os.path.exists(path)

    def is_file(self, path: str) -> bool:
        path = self.path_dwim(path)
        return os.path.isfile(path) or path == os.devnull

    def is_directory(self, path: str) -> bool:
        path = self.path_dwim(path)
        return os.path.isdir(path)

    def list_directory(self, path: str) -> list[str]:
        path = self.path_dwim(path)
        return os.listdir(path)

    def is_executable(self, path: str) -> bool:
        """is the given path executable?"""
        path = self.path_dwim(path)
        return is_executable(path)

    def _decrypt_if_vault_data(self, b_data: bytes) -> tuple[bytes, bool]:
        """Decrypt b_vault_data if encrypted and return b_data and the show_content flag"""

        if encrypted_source := is_encrypted(b_data):
            b_data = self._vault.decrypt(b_data)

        return b_data, not encrypted_source

    def get_text_file_contents(self, file_name: str, encoding: str | None = None) -> str:
        """
        Returns an `Origin` tagged string with the content of the specified (DWIM-expanded for relative) file path, decrypting if necessary.
        Callers must only specify `encoding` when the user can configure it, as error messages in that case will imply configurability.
        If `encoding` is not specified, UTF-8 will be used.
        """
        bytes_content, source_was_plaintext = self._get_file_contents(file_name)

        if encoding is None:
            encoding = 'utf-8'
            help_text = 'This file must be UTF-8 encoded.'
        else:
            help_text = 'Ensure the correct encoding was specified.'

        try:
            str_content = bytes_content.decode(encoding=encoding, errors='strict')
        except UnicodeDecodeError:
            str_content = bytes_content.decode(encoding=encoding, errors='surrogateescape')

            display.deprecated(
                msg=f"File {file_name!r} could not be decoded as {encoding!r}. Invalid content has been escaped.",
                version="2.23",
                # obj intentionally omitted since there's no value in showing its contents
                help_text=help_text,
            )

        if not source_was_plaintext:
            str_content = SourceWasEncrypted().tag(str_content)

        return AnsibleTagHelper.tag_copy(bytes_content, str_content)

    def _get_file_contents(self, file_name: str) -> tuple[bytes, bool]:
        """
        Reads the file contents from the given file name

        If the contents are vault-encrypted, it will decrypt them and return
        the decrypted data

        :arg file_name: The name of the file to read.  If this is a relative
            path, it will be expanded relative to the basedir
        :raises AnsibleFileNotFound: if the file_name does not refer to a file
        :raises AnsibleParserError: if we were unable to read the file
        :return: Returns a byte string of the file contents
        """
        if not file_name or not isinstance(file_name, str):
            raise TypeError(f"Invalid filename {file_name!r}.")

        file_name = self.path_dwim(file_name)

        try:
            data = pathlib.Path(file_name).read_bytes()
        except FileNotFoundError as ex:
            # DTFIX-FUTURE: why not just let the builtin one fly?
            raise AnsibleFileNotFound("Unable to retrieve file contents.", file_name=file_name) from ex
        except OSError as ex:
            raise AnsibleParserError(f"An error occurred while trying to read the file {file_name!r}.") from ex

        data = Origin(path=file_name).tag(data)

        return self._decrypt_if_vault_data(data)

    def get_basedir(self) -> str:
        """ returns the current basedir """
        return self._basedir

    def set_basedir(self, basedir: str) -> None:
        """ sets the base directory, used to find files when a relative path is given """
        self._basedir = os.path.abspath(basedir)

    def path_dwim(self, given: str) -> str:
        """
        make relative paths work like folks expect.
        """

        given = unquote(given)

        if given.startswith(os.path.sep) or given.startswith('~'):
            path = given
        else:
            path = os.path.join(self._basedir, given)

        return unfrackpath(path, follow=False)

    def _is_role(self, path: str) -> bool:
        """ imperfect role detection, roles are still valid w/o tasks|meta/main.yml|yaml|etc """

        path_dirname = os.path.dirname(path)
        upath = unfrackpath(path, follow=False)

        untasked_paths = (
            os.path.join(path, 'main.yml'),
            os.path.join(path, 'main.yaml'),
            os.path.join(path, 'main'),
        )
        tasked_paths = (
            os.path.join(upath, 'tasks/main.yml'),
            os.path.join(upath, 'tasks/main.yaml'),
            os.path.join(upath, 'tasks/main'),
            os.path.join(upath, 'meta/main.yml'),
            os.path.join(upath, 'meta/main.yaml'),
            os.path.join(upath, 'meta/main'),
            os.path.join(path_dirname, 'tasks/main.yml'),
            os.path.join(path_dirname, 'tasks/main.yaml'),
            os.path.join(path_dirname, 'tasks/main'),
            os.path.join(path_dirname, 'meta/main.yml'),
            os.path.join(path_dirname, 'meta/main.yaml'),
            os.path.join(path_dirname, 'meta/main'),
        )

        exists_untasked = map(os.path.exists, untasked_paths)
        exists_tasked = map(os.path.exists, tasked_paths)
        if RE_TASKS.search(path) and any(exists_untasked) or any(exists_tasked):
            return True

        return False

    def path_dwim_relative(self, path: str, dirname: str, source: str, is_role: bool = False) -> str:
        """
        find one file in either a role or playbook dir with or without
        explicitly named dirname subdirs

        Used in action plugins and lookups to find supplemental files that
        could be in either place.
        """

        search = []

        # I have full path, nothing else needs to be looked at
        if source.startswith(os.path.sep) or source.startswith('~'):
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
            if os.path.exists(candidate):
                break

        return candidate

    def path_dwim_relative_stack(self, paths: list[str], dirname: str | None, source: str | None, is_role: bool = False) -> str:
        """
        find one file in first path in stack taking roles into account and adding play basedir as fallback

        :arg paths: A list of text strings which are the paths to look for the filename in.
        :arg dirname: A text string representing a directory.  The directory
            is prepended to the source to form the path to search for.
        :arg source: A text string which is the filename to search for
        :rtype: A text string
        :returns: An absolute path to the filename ``source`` if found
        :raises: An AnsibleFileNotFound Exception if the file is found to exist in the search paths
        """
        source_root = None
        if source:
            source_root = source.split('/')[0]
        basedir = self.get_basedir()
        result = None
        search = []
        if source is None:
            display.warning('Invalid request to find a file that matches a "null" value')
        elif source and (source.startswith('~') or source.startswith(os.path.sep)):
            # path is absolute, no relative needed, check existence and return source
            test_path = unfrackpath(source, follow=False)
            if os.path.exists(test_path):
                result = test_path
        else:
            display.debug('evaluation_path:\n\t%s' % '\n\t'.join(paths))
            for path in paths:
                upath = unfrackpath(path, follow=False)
                pb_base_dir = os.path.dirname(upath)

                # if path is in role and 'tasks' not there already, add it into the search
                if (is_role or self._is_role(path)) and pb_base_dir.endswith('/tasks'):
                    if dirname:
                        search.append(os.path.join(os.path.dirname(pb_base_dir), dirname, source))
                    search.append(os.path.join(pb_base_dir, source))
                # don't add dirname if user already is using it in source
                if dirname and source_root != dirname:
                    search.append(os.path.join(upath, dirname, source))
                search.append(os.path.join(upath, source))

            # always append basedir as last resort
            # don't add dirname if user already is using it in source
            if dirname and source_root != dirname:
                search.append(os.path.join(basedir, dirname, source))
            search.append(os.path.join(basedir, source))

            display.debug('search_path:\n\t%s' % '\n\t'.join(search))
            for candidate in search:
                display.vvvvv('looking for "%s" at "%s"' % (source, candidate))
                if os.path.exists(candidate):
                    result = candidate
                    break

        if result is None:
            raise AnsibleFileNotFound(file_name=source, paths=search)

        return result

    def _create_content_tempfile(self, content: str | bytes) -> str:
        """ Create a tempfile containing defined content """
        fd, content_tempfile = tempfile.mkstemp(dir=C.DEFAULT_LOCAL_TMP)
        with os.fdopen(fd, 'wb') as f:
            try:
                f.write(to_bytes(content))
            except Exception as err:
                os.remove(content_tempfile)
                raise Exception(err)
        return content_tempfile

    def get_real_file(self, file_path: str, decrypt: bool = True) -> str:
        """
        If the file is vault encrypted return a path to a temporary decrypted file
        If the file is not encrypted then the path is returned
        Temporary files are cleanup in the destructor
        """

        if not self.path_exists(file_path) or not self.is_file(file_path):
            raise AnsibleFileNotFound(file_name=file_path)

        real_path = self.path_dwim(file_path)

        try:
            if decrypt:
                with open(real_path, 'rb') as f:
                    # Limit how much of the file is read since we do not know
                    # whether this is a vault file and therefore it could be very
                    # large.
                    if is_encrypted_file(f):
                        # if the file is encrypted and no password was specified,
                        # the decrypt call would throw an error, but we check first
                        # since the decrypt function doesn't know the file name
                        data = Origin(path=real_path).tag(f.read())
                        if not self._vault.secrets:
                            raise AnsibleParserError("A vault password or secret must be specified to decrypt %s" % file_path)

                        data = self._vault.decrypt(data)
                        # Make a temp file
                        real_path = self._create_content_tempfile(data)
                        self._tempfiles.add(real_path)

            return real_path

        except OSError as ex:
            raise AnsibleParserError(f"an error occurred while trying to read the file {real_path!r}.") from ex

    def cleanup_tmp_file(self, file_path: str) -> None:
        """
        Removes any temporary files created from a previous call to
        get_real_file. file_path must be the path returned from a
        previous call to get_real_file.
        """
        if file_path in self._tempfiles:
            os.unlink(file_path)
            self._tempfiles.remove(file_path)

    def cleanup_all_tmp_files(self) -> None:
        """
        Removes all temporary files that DataLoader has created
        NOTE: not thread safe, forks also need special handling see __init__ for details.
        """
        for f in list(self._tempfiles):
            try:
                self.cleanup_tmp_file(f)
            except Exception as e:
                display.warning("Unable to cleanup temp files: %s" % to_text(e))

    def find_vars_files(self, path: str, name: str, extensions: list[str] | None = None, allow_dir: bool = True) -> list[str]:
        """
        Find vars files in a given path with specified name. This will find
        files in a dir named <name>/ or a file called <name> ending in known
        extensions.
        """

        jpath = os.path.join(path, name)
        found: list[str] = []

        if extensions is None:
            # Look for file with no extension first to find dir before file
            extensions = [''] + C.YAML_FILENAME_EXTENSIONS
        # add valid extensions to name
        for ext in extensions:

            if '.' in ext:
                full_path = jpath + ext
            elif ext:
                full_path = '.'.join([jpath, ext])
            else:
                full_path = jpath

            if self.path_exists(full_path):
                if self.is_directory(full_path):
                    if allow_dir:
                        found.extend(self._get_dir_vars_files(full_path, extensions))
                    else:
                        continue
                else:
                    found.append(full_path)
                break
        return found

    def _get_dir_vars_files(self, path: str, extensions: list[str]) -> list[str]:
        found = []
        for spath in sorted(self.list_directory(path)):
            if not spath.startswith('.') and not spath.endswith('~'):  # skip hidden and backups

                ext = os.path.splitext(spath)[-1]
                full_spath = os.path.join(path, spath)

                if self.is_directory(full_spath) and not ext:  # recursive search if dir
                    found.extend(self._get_dir_vars_files(full_spath, extensions))
                elif self.is_file(full_spath) and (not ext or ext in extensions):
                    # only consider files with valid extensions or no extension
                    found.append(full_spath)

        return found
