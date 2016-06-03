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
from ansible.utils.unicode import to_unicode

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

class GalaxyRole(object):

    SUPPORTED_SCMS = set(['git', 'hg'])
    META_MAIN = os.path.join('meta', 'main.yml')
    META_INSTALL = os.path.join('meta', '.galaxy_install_info')
    ROLE_DIRS = ('defaults','files','handlers','meta','tasks','templates','vars','tests')
    SKIP_INFO_KEYS = ("name", "description", "readme_html", "related",
                      "summary_fields", "average_aw_composite", "average_aw_score", "url" )

    def __init__(self, galaxy, name, src=None, version=None, scm=None, path=None, full_path=None):

        display.vvvvv("GalaxyRole __init__ galaxy=%s name=%s src=%s version=%s scm=%s path=%s full_path=%s" %
                      (galaxy, name, src, version, scm, path, full_path))
        self._metadata = None
        self._install_info = None
        self._validate_certs = not galaxy.options.ignore_certs

        display.debug('Validate TLS certificates: %s' % self._validate_certs)

        self.options = galaxy.options
        self.galaxy  = galaxy

        self.name = name
        self.version = version
        self.src = src or name
        self.scm = scm
        self.path = path
        # 'path' can be a dir from roles_path, while full_path is the
        # path to the role itself (ie, /etc/ansible/roles/someuser.somerole/)
        self.full_path = None

        self.installed = None
    #    display.vvvvv('%s' % self)

    def __eq__(self, other):
        return self.name == other.name

    def __repr__(self):
        return "GalaxyRole(galaxy=%s, name=%s, src=%s, version=%s, scm=%s, path=%s, full_path=%s" % \
            (self.galaxy, self.name, self.src, self.version, self.scm, self.path, self.full_path)

    def __str__(self):
        print('self.path=%s' % self.path)
        text = [u"", u"Role: %s" % to_unicode(self.name)]
        text.append(u"\tdescription: %s" % self.metadata.get('description', ''))

        for key, value in sorted(self.metadata.items()):
            if key in self.SKIP_INFO_KEYS:
                continue

            if isinstance(value, dict):
                text.append(u"\t%s:" % (key))
                for value_key in sorted(value.keys()):
                    if value_key in self.SKIP_INFO_KEYS:
                        continue
                    text.append(u"\t\t%s: %s" % (value_key, value[value_key]))
            else:
                text.append(u"\t%s: %s" % (key, value))

        return u'\n'.join(text)

    @classmethod
    def from_name(cls, galaxy, name):
        for role_path_dir in galaxy.roles_paths:
            role_path = os.path.join(role_path_dir, name)
            if os.path.exists(role_path):
                break
            else:
                # use the first path by default
                # if the role doesn't exist locally
                role_path = os.path.join(galaxy.roles_paths[0], name)

        role = cls(galaxy, name, path=role_path)
        return role

    @classmethod
    def from_name_and_path(cls, galaxy, name, path):
        role = cls(galaxy, name)
        role.path = path
        return role

    @classmethod
    def from_requirement(cls, galaxy, requirement):
        if 'name' not in requirement and 'scm' not in requirement:
            raise AnsibleError("Must specify name or src for role")
        role = cls(galaxy, **requirement)
        return role

    @property
    def installable_from_galaxy(self):
        if '.' not in dep_role.name and '.' not in dep_role.src and dep_role.scm is None:
            # we know we can skip this, as it's not going to
            # be found on galaxy.ansible.com
            return False
        return True

    @property
    def metadata(self):
        """
        Returns role metadata
        """
        print('self_metadata=%s' % self._metadata)
        if self._metadata is None:
            self._metadata = {}
            if not self.path:
                return self._metadata
            meta_path = os.path.join(self.path, self.META_MAIN)
            if os.path.isfile(meta_path):
                try:
                    f = open(meta_path, 'r')
                    self._metadata = yaml.safe_load(f)
                except Exception as e:
                    print('fffffffffffffffffffffff')
                    display.vvv('Exception: %s' % e)
                    display.vvvvv("Unable to load metadata for %s" % self.name)
                finally:
                    print('close')
                    f.close()

        print('self_metadata=%s' % self._metadata)
        return self._metadata

    @property
    def install_info(self):
        """
        Returns role install info
        """
        if self._install_info is None:
            if self.path is None:
                return None

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

        if self.scm:
            # create tar file from scm url
            tmp_file = RoleRequirement.scm_archive_role(**self.spec)
        elif self.src:
            if os.path.isfile(self.src):
                # installing a local tar.gz
                tmp_file = self.src
            elif '://' in self.src:
                role_data = self.src
                tmp_file = self.fetch(role_data)
            else:
                api = GalaxyAPI(self.galaxy)
                role_data = api.lookup_role_by_name(self.src)
                if not role_data:
                    raise AnsibleError("- sorry, %s was not found on %s." % (self.src, api.api_server))

                role_versions = api.fetch_role_related('versions', role_data['id'])
                if not self.version:
                    # convert the version names to LooseVersion objects
                    # and sort them to get the latest version. If there
                    # are no versions in the list, we'll grab the head
                    # of the master branch
                    if len(role_versions) > 0:
                        loose_versions = [LooseVersion(a.get('name',None)) for a in role_versions]
                        loose_versions.sort()
                        self.version = str(loose_versions[-1])
                    elif role_data.get('github_branch', None):
                        self.version = role_data['github_branch']
                    else:
                        self.version = 'master'
                elif self.version != 'master':
                    if role_versions and self.version not in [a.get('name', None) for a in role_versions]:
                        raise AnsibleError("- the specified version (%s) of %s was not found in the list of available versions (%s)." % (self.version, self.name, role_versions))

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
                        meta_file = member
                        break
                if not meta_file:
                    raise AnsibleError("this role does not appear to have a meta/main.yml file.")
                else:
                    try:
                        self._metadata = yaml.safe_load(role_tar_file.extractfile(meta_file))
                    except:
                        raise AnsibleError("this role does not appear to have a valid meta/main.yml file.")

                # we strip off the top-level directory for all of the files contained within
                # the tar file here, since the default is 'github_repo-target', and change it
                # to the specified role's name
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
                                raise AnsibleError("%s doesn't appear to contain a role.\n  please remove this directory manually if you really want to put the role here." % self.path)
                    else:
                        os.makedirs(self.path)

                    # now we do the actual extraction to the path
                    for member in members:
                        # we only extract files, and remove any relative path
                        # bits that might be in the file for security purposes
                        # and drop the leading directory, as mentioned above
                        if member.isreg() or member.issym():
                            parts = member.name.split(os.sep)[1:]
                            final_parts = []
                            for part in parts:
                                if part != '..' and '~' not in part and '$' not in part:
                                    final_parts.append(part)
                            member.name = os.path.join(*final_parts)
                            role_tar_file.extract(member, self.path)

                    # write out the install info file for later use
                    self._write_galaxy_install_info()
                except OSError as e:
                    raise AnsibleError("Could not update files in %s: %s" % (self.path, str(e)))

                # return the parsed yaml metadata
                display.display("- %s was installed successfully" % self.name)
                try:
                    os.unlink(tmp_file)
                except (OSError,IOError) as e:
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
