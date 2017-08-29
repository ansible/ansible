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

import datetime
import os
import tarfile
import tempfile
import yaml
from distutils.version import LooseVersion
from shutil import rmtree

from ansible.errors import AnsibleError
from ansible.module_utils.urls import open_url
from ansible.playbook.role.requirement import RoleRequirement
from ansible.galaxy.api import GalaxyAPI

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class GalaxyRole(object):

    SUPPORTED_SCMS = set(['git', 'hg'])
    META_MAIN = os.path.join('meta', 'main.yml')
    META_INSTALL = os.path.join('meta', '.galaxy_install_info')
    ROLE_DIRS = ('defaults', 'files', 'handlers', 'meta', 'tasks', 'templates', 'vars', 'tests')

    def __init__(self, galaxy, name, src=None, version=None, scm=None, path=None):

        self._metadata = None
        self._install_info = None
        self._validate_certs = not galaxy.options.ignore_certs

        display.debug('Validate TLS certificates: %s' % self._validate_certs)

        self.options = galaxy.options
        self.galaxy = galaxy

        self.name = name
        self.version = version
        self.src = src or name
        self.scm = scm

        if path is not None:
            if self.name not in path:
                path = os.path.join(path, self.name)
            self.path = path
        else:
            for role_path_dir in galaxy.roles_paths:
                role_path = os.path.join(role_path_dir, self.name)
                if os.path.exists(role_path):
                    self.path = role_path
                    break
            else:
                # use the first path by default
                self.path = os.path.join(galaxy.roles_paths[0], self.name)
                # create list of possible paths
                self.paths = [x for x in galaxy.roles_paths]
                self.paths = [os.path.join(x, self.name) for x in self.paths]

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
            meta_path = os.path.join(self.path, self.META_MAIN)
            if os.path.isfile(meta_path):
                try:
                    f = open(meta_path, 'r')
                    self._metadata = yaml.safe_load(f)
                except:
                    display.vvvvv("Unable to load metadata for %s" % self.name)
                    return False
                finally:
                    f.close()

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
                except:
                    display.vvvvv("Unable to load Galaxy install info for %s" % self.name)
                    return False
                finally:
                    f.close()
        return self._install_info

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
            except:
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
            except:
                pass

        return False

    def fetch(self, role_data):
        """
        Downloads the archived role from github to a temp location
        """
        if role_data:

            # first grab the file and save it to a temp location
            if "github_user" in role_data and "github_repo" in role_data:
                archive_url = 'https://github.com/%s/%s/archive/%s.tar.gz' % (role_data["github_user"], role_data["github_repo"], self.version)
            else:
                archive_url = self.src

            display.display("- downloading role from %s" % archive_url)

            try:
                url_file = open_url(archive_url, validate_certs=self._validate_certs)
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                data = url_file.read()
                while data:
                    temp_file.write(data)
                    data = url_file.read()
                temp_file.close()
                return temp_file.name
            except Exception as e:
                display.error("failed to download the file: %s" % str(e))

        return False

    def install(self):
        # the file is a tar, so open it that way and extract it
        # to the specified (or default) roles directory
        local_file = False

        if self.scm:
            # create tar file from scm url
            tmp_file = RoleRequirement.scm_archive_role(**self.spec)
        elif self.src:
            if os.path.isfile(self.src):
                # installing a local tar.gz
                local_file = True
                tmp_file = self.src
            elif '://' in self.src:
                role_data = self.src
                tmp_file = self.fetch(role_data)
            else:
                api = GalaxyAPI(self.galaxy)
                role_data = api.lookup_role_by_name(self.src)
                if not role_data:
                    raise AnsibleError("- sorry, %s was not found on %s." % (self.src, api.api_server))

                if role_data.get('role_type') == 'APP':
                    # Container Role
                    display.warning("%s is a Container App role, and should only be installed using Ansible "
                                    "Container" % self.name)

                role_versions = api.fetch_role_related('versions', role_data['id'])
                if not self.version:
                    # convert the version names to LooseVersion objects
                    # and sort them to get the latest version. If there
                    # are no versions in the list, we'll grab the head
                    # of the master branch
                    if len(role_versions) > 0:
                        loose_versions = [LooseVersion(a.get('name', None)) for a in role_versions]
                        loose_versions.sort()
                        self.version = str(loose_versions[-1])
                    elif role_data.get('github_branch', None):
                        self.version = role_data['github_branch']
                    else:
                        self.version = 'master'
                elif self.version != 'master':
                    if role_versions and str(self.version) not in [a.get('name', None) for a in role_versions]:
                        raise AnsibleError("- the specified version (%s) of %s was not found in the list of available versions (%s)." % (self.version,
                                                                                                                                         self.name,
                                                                                                                                         role_versions))

                tmp_file = self.fetch(role_data)

        else:
            raise AnsibleError("No valid role data found")

        if tmp_file:

            display.debug("installing from %s" % tmp_file)

            if not tarfile.is_tarfile(tmp_file):
                raise AnsibleError("the file downloaded was not a tar.gz")
            else:
                if tmp_file.endswith('.gz'):
                    role_tar_file = tarfile.open(tmp_file, "r:gz")
                else:
                    role_tar_file = tarfile.open(tmp_file, "r")
                # verify the role's meta file
                meta_file = None
                members = role_tar_file.getmembers()
                # next find the metadata file
                for member in members:
                    if self.META_MAIN in member.name:
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
                    except:
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
                            elif not getattr(self.options, "force", False):
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
                                parts = member.name.replace(archive_parent_dir, "", 1).split(os.sep)
                                final_parts = []
                                for part in parts:
                                    if part != '..' and '~' not in part and '$' not in part:
                                        final_parts.append(part)
                                member.name = os.path.join(*final_parts)
                                role_tar_file.extract(member, self.path)

                        # write out the install info file for later use
                        self._write_galaxy_install_info()
                        installed = True
                    except OSError as e:
                        error = True
                        if e[0] == 13 and len(self.paths) > 1:
                            current = self.paths.index(self.path)
                            nextidx = current + 1
                            if len(self.paths) >= current:
                                self.path = self.paths[nextidx]
                                error = False
                        if error:
                            raise AnsibleError("Could not update files in %s: %s" % (self.path, str(e)))

                # return the parsed yaml metadata
                display.display("- %s was installed successfully" % str(self))
                if not local_file:
                    try:
                        os.unlink(tmp_file)
                    except (OSError, IOError) as e:
                        display.warning("Unable to remove tmp file (%s): %s" % (tmp_file, str(e)))
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
