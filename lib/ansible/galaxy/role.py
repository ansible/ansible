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

import datetime
import os
import subprocess
import tarfile
import tempfile
import yaml
from shutil import rmtree
from urllib2 import urlopen

from ansible import constants as C
from ansible.errors import AnsibleError

class GalaxyRole(object):

    SUPPORTED_SCMS = set(['git', 'hg'])
    META_MAIN = os.path.join('meta', 'main.yml')
    META_INSTALL = os.path.join('meta', '.galaxy_install_info')
    ROLE_DIRS = ('defaults','files','handlers','meta','tasks','templates','vars')


    def __init__(self, galaxy, name, src=None, version=None, scm=None):

        self._metadata = None
        self._install_info = None

        self.options = galaxy.options
        self.display = galaxy.display

        self.name = name
        self.version = version
        self.src = src or name
        self.scm = scm

        self.path = (os.path.join(galaxy.roles_path, self.name))

    def fetch_from_scm_archive(self):

        # this can be configured to prevent unwanted SCMS but cannot add new ones unless the code is also updated
        if scm not in self.scms:
            self.display.display("The %s scm is not currently supported" % scm)
            return False

        tempdir = tempfile.mkdtemp()
        clone_cmd = [scm, 'clone', role_url, self.name]
        with open('/dev/null', 'w') as devnull:
            try:
                self.display.display("- executing: %s" % " ".join(clone_cmd))
                popen = subprocess.Popen(clone_cmd, cwd=tempdir, stdout=devnull, stderr=devnull)
            except:
                raise AnsibleError("error executing: %s" % " ".join(clone_cmd))
            rc = popen.wait()
        if rc != 0:
            self.display.display("- command %s failed" % ' '.join(clone_cmd))
            self.display.display("  in directory %s" % tempdir)
            return False

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tar')
        if scm == 'hg':
            archive_cmd = ['hg', 'archive', '--prefix', "%s/" % self.name]
            if role_version:
                archive_cmd.extend(['-r', role_version])
            archive_cmd.append(temp_file.name)
        if scm == 'git':
            archive_cmd = ['git', 'archive', '--prefix=%s/' % self.name, '--output=%s' % temp_file.name]
            if role_version:
                archive_cmd.append(role_version)
            else:
                archive_cmd.append('HEAD')

        with open('/dev/null', 'w') as devnull:
            self.display.display("- executing: %s" % " ".join(archive_cmd))
            popen = subprocess.Popen(archive_cmd, cwd=os.path.join(tempdir, self.name),
                                     stderr=devnull, stdout=devnull)
            rc = popen.wait()
        if rc != 0:
            self.display.display("- command %s failed" % ' '.join(archive_cmd))
            self.display.display("  in directory %s" % tempdir)
            return False

        rmtree(tempdir, ignore_errors=True)

        return temp_file.name

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
                    self.display.vvvvv("Unable to load metadata for %s" % self.name)
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
                    self.display.vvvvv("Unable to load Galaxy install info for %s" % self.name)
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
        try:
            f = open(info_path, 'w+')
            self._install_info = yaml.safe_dump(info, f)
        except:
            return False
        finally:
            f.close()

        return True

    def remove(self):
        """
        Removes the specified role from the roles path. There is a
        sanity check to make sure there's a meta/main.yml file at this
        path so the user doesn't blow away random directories
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
            self.display.display("- downloading role from %s" % archive_url)

            try:
                url_file = urlopen(archive_url)
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                data = url_file.read()
                while data:
                    temp_file.write(data)
                    data = url_file.read()
                temp_file.close()
                return temp_file.name
            except:
                # TODO: better urllib2 error handling for error
                #       messages that are more exact
                self.display.error("failed to download the file.")

        return False

    def install(self, role_filename):
        # the file is a tar, so open it that way and extract it
        # to the specified (or default) roles directory

        if not tarfile.is_tarfile(role_filename):
            self.display.error("the file downloaded was not a tar.gz")
            return False
        else:
            if role_filename.endswith('.gz'):
                role_tar_file = tarfile.open(role_filename, "r:gz")
            else:
                role_tar_file = tarfile.open(role_filename, "r")
            # verify the role's meta file
            meta_file = None
            members = role_tar_file.getmembers()
            # next find the metadata file
            for member in members:
                if self.META_MAIN in member.name:
                    meta_file = member
                    break
            if not meta_file:
                self.display.error("this role does not appear to have a meta/main.yml file.")
                return False
            else:
                try:
                    self._metadata = yaml.safe_load(role_tar_file.extractfile(meta_file))
                except:
                    self.display.error("this role does not appear to have a valid meta/main.yml file.")
                    return False

            # we strip off the top-level directory for all of the files contained within
            # the tar file here, since the default is 'github_repo-target', and change it
            # to the specified role's name
            self.display.display("- extracting %s to %s" % (self.name, self.path))
            try:
                if os.path.exists(self.path):
                    if not os.path.isdir(self.path):
                        self.display.error("the specified roles path exists and is not a directory.")
                        return False
                    elif not getattr(self.options, "force", False):
                        self.display.error("the specified role %s appears to already exist. Use --force to replace it." % self.name)
                        return False
                    else:
                        # using --force, remove the old path
                        if not self.remove():
                            self.display.error("%s doesn't appear to contain a role." % self.path)
                            self.display.error("  please remove this directory manually if you really want to put the role here.")
                            return False
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
                self.display.error("Could not update files in %s: %s" % (self.path, str(e)))
                return False

            # return the parsed yaml metadata
            self.display.display("- %s was installed successfully" % self.name)
            return True

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


    @staticmethod
    def url_to_spec(roleurl):
        # gets the role name out of a repo like
        # http://git.example.com/repos/repo.git" => "repo"

        if '://' not in roleurl and '@' not in roleurl:
            return roleurl
        trailing_path = roleurl.split('/')[-1]
        if trailing_path.endswith('.git'):
            trailing_path = trailing_path[:-4]
        if trailing_path.endswith('.tar.gz'):
            trailing_path = trailing_path[:-7]
        if ',' in trailing_path:
            trailing_path = trailing_path.split(',')[0]
        return trailing_path

    @staticmethod
    def scm_archive_role(scm, role_url, role_version, role_name):
        if scm not in ['hg', 'git']:
            self.display.display("- scm %s is not currently supported" % scm)
            return False
        tempdir = tempfile.mkdtemp()
        clone_cmd = [scm, 'clone', role_url, role_name]
        with open('/dev/null', 'w') as devnull:
            try:
                self.display.display("- executing: %s" % " ".join(clone_cmd))
                popen = subprocess.Popen(clone_cmd, cwd=tempdir, stdout=devnull, stderr=devnull)
            except:
                raise AnsibleError("error executing: %s" % " ".join(clone_cmd))
            rc = popen.wait()
        if rc != 0:
            self.display.display("- command %s failed" % ' '.join(clone_cmd))
            self.display.display("  in directory %s" % tempdir)
            return False

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tar')
        if scm == 'hg':
            archive_cmd = ['hg', 'archive', '--prefix', "%s/" % role_name]
            if role_version:
                archive_cmd.extend(['-r', role_version])
            archive_cmd.append(temp_file.name)
        if scm == 'git':
            archive_cmd = ['git', 'archive', '--prefix=%s/' % role_name, '--output=%s' % temp_file.name]
            if role_version:
                archive_cmd.append(role_version)
            else:
                archive_cmd.append('HEAD')

        with open('/dev/null', 'w') as devnull:
            self.display.display("- executing: %s" % " ".join(archive_cmd))
            popen = subprocess.Popen(archive_cmd, cwd=os.path.join(tempdir, role_name),
                                     stderr=devnull, stdout=devnull)
            rc = popen.wait()
        if rc != 0:
            self.display.display("- command %s failed" % ' '.join(archive_cmd))
            self.display.display("  in directory %s" % tempdir)
            return False

        shutil.rmtree(tempdir, ignore_errors=True)

        return temp_file.name

