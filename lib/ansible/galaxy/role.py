########################################################################
#
# (C) 2015, Brian Coca <bcoca@ansible.com>
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
#
########################################################################

from __future__ import annotations

import errno
import datetime
import functools
import os
import tarfile
import tempfile

from collections.abc import MutableSequence
from shutil import rmtree

from ansible import context
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.galaxy.api import GalaxyAPI
from ansible.galaxy.user_agent import user_agent
from ansible.module_utils.common.text.converters import to_native, to_text
from ansible.module_utils.common.yaml import yaml_dump, yaml_load
from ansible.module_utils.compat.version import LooseVersion
from ansible.module_utils.urls import open_url
from ansible.playbook.role.requirement import RoleRequirement
from ansible.utils.display import Display
from ansible.utils.path import is_subpath, unfrackpath

display = Display()


@functools.cache
def _check_working_data_filter() -> bool:
    """
    Check if tarfile.data_filter implementation is working
    for the current Python version or not
    """

    # Implemented the following code to circumvent broken implementation of data_filter
    # in tarfile. See for more information - https://github.com/python/cpython/issues/107845
    # deprecated: description='probing broken data filter implementation' python_version='3.11'
    ret = False
    if hasattr(tarfile, 'data_filter'):
        # We explicitly check if tarfile.data_filter is broken or not
        ti = tarfile.TarInfo('docs/README.md')
        ti.type = tarfile.SYMTYPE
        ti.linkname = '../README.md'

        try:
            tarfile.data_filter(ti, '/foo')
        except tarfile.LinkOutsideDestinationError:
            pass
        else:
            ret = True
    return ret


class GalaxyRole(object):

    SUPPORTED_SCMS = set(['git', 'hg'])
    META_MAIN = (os.path.join('meta', 'main.yml'), os.path.join('meta', 'main.yaml'))
    META_INSTALL = os.path.join('meta', '.galaxy_install_info')
    META_REQUIREMENTS = (os.path.join('meta', 'requirements.yml'), os.path.join('meta', 'requirements.yaml'))
    ROLE_DIRS = ('defaults', 'files', 'handlers', 'meta', 'tasks', 'templates', 'vars', 'tests')

    def __init__(self, galaxy, api, name, src=None, version=None, scm=None, path=None):

        self._metadata = None
        self._metadata_dependencies = None
        self._requirements = None
        self._install_info = None
        self._validate_certs = not context.CLIARGS['ignore_certs']

        display.debug('Validate TLS certificates: %s' % self._validate_certs)

        self.galaxy = galaxy
        self._api = api

        self.name = name
        self.version = version
        self.src = src or name
        self.download_url = None
        self.scm = scm
        self.paths = [os.path.join(x, self.name) for x in galaxy.roles_paths]

        if path is not None:
            if not path.endswith(os.path.join(os.path.sep, self.name)):
                path = os.path.join(path, self.name)
            else:
                # Look for a meta/main.ya?ml inside the potential role dir in case
                #  the role name is the same as parent directory of the role.
                #
                # Example:
                #   ./roles/testing/testing/meta/main.yml
                for meta_main in self.META_MAIN:
                    if os.path.exists(os.path.join(path, name, meta_main)):
                        path = os.path.join(path, self.name)
                        break
            self.path = path
        else:
            # use the first path by default
            self.path = self.paths[0]

    def __repr__(self):
        """
        Returns "rolename (version)" if version is not null
        Returns "rolename" otherwise
        """
        if self.version:
            return "%s (%s)" % (self.name, self.version)
        else:
            return self.name

    def __eq__(self, other):
        return self.name == other.name

    @property
    def api(self):
        if not isinstance(self._api, GalaxyAPI):
            return self._api.api
        return self._api

    @property
    def metadata(self):
        """
        Returns role metadata
        """
        if self._metadata is None:
            for path in self.paths:
                for meta_main in self.META_MAIN:
                    meta_path = os.path.join(path, meta_main)
                    if os.path.isfile(meta_path):
                        try:
                            with open(meta_path, 'r') as f:
                                self._metadata = yaml_load(f)
                        except Exception:
                            display.vvvvv("Unable to load metadata for %s" % self.name)
                            return False
                        break

        return self._metadata

    @property
    def metadata_dependencies(self):
        """
        Returns a list of dependencies from role metadata
        """
        if self._metadata_dependencies is None:
            self._metadata_dependencies = []

            if self.metadata is not None:
                self._metadata_dependencies = self.metadata.get('dependencies') or []

        if not isinstance(self._metadata_dependencies, MutableSequence):
            raise AnsibleParserError(
                f"Expected role dependencies to be a list. Role {self} has meta/main.yml with dependencies {self._metadata_dependencies}"
            )

        return self._metadata_dependencies

    @property
    def install_info(self):
        """
        Returns role install info
        """
        if self._install_info is None:

            info_path = os.path.join(self.path, self.META_INSTALL)
            if os.path.isfile(info_path):
                try:
                    f = open(info_path, 'r')
                    self._install_info = yaml_load(f)
                except Exception:
                    display.vvvvv("Unable to load Galaxy install info for %s" % self.name)
                    return False
                finally:
                    f.close()
        return self._install_info

    @property
    def _exists(self):
        for path in self.paths:
            if os.path.isdir(path):
                return True

        return False

    def _write_galaxy_install_info(self):
        """
        Writes a YAML-formatted file to the role's meta/ directory
        (named .galaxy_install_info) which contains some information
        we can use later for commands like 'list' and 'info'.
        """

        info = dict(
            version=self.version,
            install_date=datetime.datetime.now(datetime.timezone.utc).strftime("%c"),
        )
        if not os.path.exists(os.path.join(self.path, 'meta')):
            os.makedirs(os.path.join(self.path, 'meta'))
        info_path = os.path.join(self.path, self.META_INSTALL)
        with open(info_path, 'w+') as f:
            try:
                self._install_info = yaml_dump(info, f)
            except Exception:
                return False

        return True

    def remove(self):
        """
        Removes the specified role from the roles path.
        There is a sanity check to make sure there's a meta/main.yml file at this
        path so the user doesn't blow away random directories.
        """
        if self.metadata:
            try:
                rmtree(self.path)
                return True
            except Exception:
                pass

        return False

    def fetch(self, role_data):
        """
        Downloads the archived role to a temp location based on role data
        """
        if role_data:

            # first grab the file and save it to a temp location
            if self.download_url is not None:
                archive_url = self.download_url
            elif "github_user" in role_data and "github_repo" in role_data:
                archive_url = 'https://github.com/%s/%s/archive/%s.tar.gz' % (role_data["github_user"], role_data["github_repo"], self.version)
            else:
                archive_url = self.src

            display.display("- downloading role from %s" % archive_url)

            try:
                url_file = open_url(archive_url, validate_certs=self._validate_certs, http_agent=user_agent(), timeout=60)
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                data = url_file.read()
                while data:
                    temp_file.write(data)
                    data = url_file.read()
                temp_file.close()
                return temp_file.name
            except Exception as e:
                display.error(u"failed to download the file: %s" % to_text(e))

        return False

    def install(self):

        if self.scm:
            # create tar file from scm url
            tmp_file = RoleRequirement.scm_archive_role(keep_scm_meta=context.CLIARGS['keep_scm_meta'], **self.spec)
        elif self.src:
            if os.path.isfile(self.src):
                tmp_file = self.src
            elif '://' in self.src:
                role_data = self.src
                tmp_file = self.fetch(role_data)
            else:
                role_data = self.api.lookup_role_by_name(self.src)
                if not role_data:
                    raise AnsibleError("- sorry, %s was not found on %s." % (self.src, self.api.api_server))

                if role_data.get('role_type') == 'APP':
                    # Container Role
                    display.warning("%s is a Container App role, and should only be installed using Ansible "
                                    "Container" % self.name)

                role_versions = self.api.fetch_role_related('versions', role_data['id'])
                if not self.version:
                    # convert the version names to LooseVersion objects
                    # and sort them to get the latest version. If there
                    # are no versions in the list, we'll grab the head
                    # of the master branch
                    if len(role_versions) > 0:
                        loose_versions = [v for a in role_versions if (v := LooseVersion()) and v.parse(a.get('name') or '') is None]
                        try:
                            loose_versions.sort()
                        except TypeError:
                            raise AnsibleError(
                                'Unable to compare role versions (%s) to determine the most recent version due to incompatible version formats. '
                                'Please contact the role author to resolve versioning conflicts, or specify an explicit role version to '
                                'install.' % ', '.join([v.vstring for v in loose_versions])
                            )
                        self.version = to_text(loose_versions[-1])
                    elif role_data.get('github_branch', None):
                        self.version = role_data['github_branch']
                    else:
                        self.version = 'master'
                elif self.version != 'master':
                    if role_versions and to_text(self.version) not in [a.get('name', None) for a in role_versions]:
                        raise AnsibleError("- the specified version (%s) of %s was not found in the list of available versions (%s)." % (self.version,
                                                                                                                                         self.name,
                                                                                                                                         role_versions))

                # check if there's a source link/url for our role_version
                for role_version in role_versions:
                    if role_version['name'] == self.version and 'source' in role_version:
                        self.src = role_version['source']
                    if role_version['name'] == self.version and 'download_url' in role_version:
                        self.download_url = role_version['download_url']

                tmp_file = self.fetch(role_data)

        else:
            raise AnsibleError("No valid role data found")

        if tmp_file:

            display.debug("installing from %s" % tmp_file)

            if not tarfile.is_tarfile(tmp_file):
                raise AnsibleError("the downloaded file does not appear to be a valid tar archive.")
            else:
                role_tar_file = tarfile.open(tmp_file, "r")
                # verify the role's meta file
                meta_file = None
                members = role_tar_file.getmembers()
                # next find the metadata file
                for member in members:
                    for meta_main in self.META_MAIN:
                        if meta_main in member.name:
                            # Look for parent of meta/main.yml
                            # Due to possibility of sub roles each containing meta/main.yml
                            # look for shortest length parent
                            meta_parent_dir = os.path.dirname(os.path.dirname(member.name))
                            if not meta_file:
                                archive_parent_dir = meta_parent_dir
                                meta_file = member
                            else:
                                if len(meta_parent_dir) < len(archive_parent_dir):
                                    archive_parent_dir = meta_parent_dir
                                    meta_file = member
                if not meta_file:
                    raise AnsibleError("this role does not appear to have a meta/main.yml file.")
                else:
                    try:
                        self._metadata = yaml_load(role_tar_file.extractfile(meta_file))
                    except Exception:
                        raise AnsibleError("this role does not appear to have a valid meta/main.yml file.")

                paths = self.paths
                if self.path != paths[0]:
                    # path can be passed though __init__
                    # FIXME should this be done in __init__?
                    paths[:0] = self.path
                paths_len = len(paths)
                for idx, path in enumerate(paths):
                    self.path = path
                    display.display("- extracting %s to %s" % (self.name, self.path))
                    try:
                        if os.path.exists(self.path):
                            if not os.path.isdir(self.path):
                                raise AnsibleError("the specified roles path exists and is not a directory.")
                            elif not context.CLIARGS.get("force", False):
                                raise AnsibleError("the specified role %s appears to already exist. Use --force to replace it." % self.name)
                            else:
                                # using --force, remove the old path
                                if not self.remove():
                                    raise AnsibleError("%s doesn't appear to contain a role.\n  please remove this directory manually if you really "
                                                       "want to put the role here." % self.path)
                        else:
                            os.makedirs(self.path)

                        resolved_archive = unfrackpath(archive_parent_dir, follow=False)

                        # We strip off any higher-level directories for all of the files
                        # contained within the tar file here. The default is 'github_repo-target'.
                        # Gerrit instances, on the other hand, does not have a parent directory at all.
                        for member in members:
                            # we only extract files, and remove any relative path
                            # bits that might be in the file for security purposes
                            # and drop any containing directory, as mentioned above
                            if not (member.isreg() or member.issym()):
                                continue

                            for attr in ('name', 'linkname'):
                                if not (attr_value := getattr(member, attr, None)):
                                    continue

                                if attr == 'linkname':
                                    # Symlinks are relative to the link
                                    relative_to = os.path.dirname(getattr(member, 'name', ''))
                                else:
                                    # Normalize paths that start with the archive dir
                                    attr_value = attr_value.replace(archive_parent_dir, "", 1)
                                    attr_value = os.path.join(*attr_value.split(os.sep))  # remove leading os.sep
                                    relative_to = ''

                                full_path = os.path.join(resolved_archive, relative_to, attr_value)
                                if not is_subpath(full_path, resolved_archive, real=True):
                                    err = f"Invalid {attr} for tarfile member: path {full_path} is not a subpath of the role {resolved_archive}"
                                    raise AnsibleError(err)

                                relative_path_dir = os.path.join(resolved_archive, relative_to)
                                relative_path = os.path.join(*full_path.replace(relative_path_dir, "", 1).split(os.sep))
                                setattr(member, attr, relative_path)

                            if _check_working_data_filter():
                                # deprecated: description='extract fallback without filter' python_version='3.11'
                                role_tar_file.extract(member, to_native(self.path), filter='data')  # type: ignore[call-arg]
                            else:
                                # Remove along with manual path filter once Python 3.12 is minimum supported version
                                role_tar_file.extract(member, to_native(self.path))

                        # write out the install info file for later use
                        self._write_galaxy_install_info()
                        break
                    except OSError as e:
                        if e.errno == errno.EACCES and idx < paths_len - 1:
                            continue
                        raise AnsibleError("Could not update files in %s: %s" % (self.path, to_native(e)))

                # return the parsed yaml metadata
                display.display("- %s was installed successfully" % str(self))
                if not (self.src and os.path.isfile(self.src)):
                    try:
                        os.unlink(tmp_file)
                    except (OSError, IOError) as e:
                        display.warning(u"Unable to remove tmp file (%s): %s" % (tmp_file, to_text(e)))
                return True

        return False

    @property
    def spec(self):
        """
        Returns role spec info
        {
           'scm': 'git',
           'src': 'http://git.example.com/repos/repo.git',
           'version': 'v1.0',
           'name': 'repo'
        }
        """
        return dict(scm=self.scm, src=self.src, version=self.version, name=self.name)

    @property
    def requirements(self):
        """
        Returns role requirements
        """
        if self._requirements is None:
            self._requirements = []
            for meta_requirements in self.META_REQUIREMENTS:
                meta_path = os.path.join(self.path, meta_requirements)
                if os.path.isfile(meta_path):
                    try:
                        f = open(meta_path, 'r')
                        self._requirements = yaml_load(f)
                    except Exception:
                        display.vvvvv("Unable to load requirements for %s" % self.name)
                    finally:
                        f.close()

                    break

        if not isinstance(self._requirements, MutableSequence):
            raise AnsibleParserError(f"Expected role dependencies to be a list. Role {self} has meta/requirements.yml {self._requirements}")

        return self._requirements
