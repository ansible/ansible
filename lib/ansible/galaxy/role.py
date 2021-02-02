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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import errno
import datetime
import os
import tarfile
import tempfile
import yaml
from distutils.version import LooseVersion
from shutil import rmtree

from ansible import context
from ansible.errors import AnsibleError
from ansible.galaxy.user_agent import user_agent
from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.urls import open_url
from ansible.playbook.role.requirement import RoleRequirement
from ansible.utils.display import Display

display = Display()


class GalaxyRole(object):

    SUPPORTED_SCMS = set(['git', 'hg'])
    META_MAIN = (os.path.join('meta', 'main.yml'), os.path.join('meta', 'main.yaml'))
    META_INSTALL = os.path.join('meta', '.galaxy_install_info')
    META_REQUIREMENTS = (os.path.join('meta', 'requirements.yml'), os.path.join('meta', 'requirements.yaml'))
    ROLE_DIRS = ('defaults', 'files', 'handlers', 'meta', 'tasks', 'templates', 'vars', 'tests')

    def __init__(self, galaxy, api, name, src=None, version=None, scm=None, path=None):

        self._metadata = None
        self._requirements = None
        self._install_info = None
        self._validate_certs = not context.CLIARGS['ignore_certs']

        display.debug('Validate TLS certificates: %s' % self._validate_certs)

        self.galaxy = galaxy
        self.api = api

        self.name = name
        self.version = version
        self.src = src or name
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
            self.path = os.path.join(galaxy.roles_paths[0], self.name)

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
                                self._metadata = yaml.safe_load(f)
                        except Exception:
                            display.vvvvv("Unable to load metadata for %s" % self.name)
                            return False
                        break

        return self._metadata

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
                    self._install_info = yaml.safe_load(f)
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
            install_date=datetime.datetime.utcnow().strftime("%c"),
        )
        if not os.path.exists(os.path.join(self.path, 'meta')):
            os.makedirs(os.path.join(self.path, 'meta'))
        info_path = os.path.join(self.path, self.META_INSTALL)
        with open(info_path, 'w+') as f:
            try:
                self._install_info = yaml.safe_dump(info, f)
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
            if "github_user" in role_data and "github_repo" in role_data:
                archive_url = 'https://github.com/%s/%s/archive/%s.tar.gz' % (role_data["github_user"], role_data["github_repo"], self.version)
            else:
                archive_url = self.src

            display.display("- downloading role from %s" % archive_url)

            try:
                url_file = open_url(archive_url, validate_certs=self._validate_certs, http_agent=user_agent())
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
                        loose_versions = [LooseVersion(a.get('name', None)) for a in role_versions]
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

                # check if there's a source link for our role_version
                for role_version in role_versions:
                    if role_version['name'] == self.version and 'source' in role_version:
                        self.src = role_version['source']

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
                        self._metadata = yaml.safe_load(role_tar_file.extractfile(meta_file))
                    except Exception:
                        raise AnsibleError("this role does not appear to have a valid meta/main.yml file.")

                # we strip off any higher-level directories for all of the files contained within
                # the tar file here. The default is 'github_repo-target'. Gerrit instances, on the other
                # hand, does not have a parent directory at all.
                installed = False
                while not installed:
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

                        # now we do the actual extraction to the path
                        for member in members:
                            # we only extract files, and remove any relative path
                            # bits that might be in the file for security purposes
                            # and drop any containing directory, as mentioned above
                            if member.isreg() or member.issym():
                                n_member_name = to_native(member.name)
                                n_archive_parent_dir = to_native(archive_parent_dir)
                                n_parts = n_member_name.replace(n_archive_parent_dir, "", 1).split(os.sep)
                                n_final_parts = []
                                for n_part in n_parts:
                                    # TODO if the condition triggers it produces a broken installation.
                                    # It will create the parent directory as an empty file and will
                                    # explode if the directory contains valid files.
                                    # Leaving this as is since the whole module needs a rewrite.
                                    if n_part != '..' and not n_part.startswith('~') and '$' not in n_part:
                                        n_final_parts.append(n_part)
                                member.name = os.path.join(*n_final_parts)
                                role_tar_file.extract(member, to_native(self.path))

                        # write out the install info file for later use
                        self._write_galaxy_install_info()
                        installed = True
                    except OSError as e:
                        error = True
                        if e.errno == errno.EACCES and len(self.paths) > 1:
                            current = self.paths.index(self.path)
                            if len(self.paths) > current:
                                self.path = self.paths[current + 1]
                                error = False
                        if error:
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
                        self._requirements = yaml.safe_load(f)
                    except Exception:
                        display.vvvvv("Unable to load requirements for %s" % self.name)
                    finally:
                        f.close()

                    break

        return self._requirements
