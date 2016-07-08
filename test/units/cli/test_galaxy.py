# (c) 2016, Adrian Likins <alikins@redhat.com>
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

from ansible.compat.six import PY3
from ansible.compat.tests import unittest

from nose.plugins.skip import SkipTest
import ansible
import os
import shutil
import tarfile

from mock import patch, call

from ansible.errors import AnsibleError

if PY3:
    raise SkipTest('galaxy is not ported to be py3 compatible yet')

from ansible.cli.galaxy import GalaxyCLI

class TestGalaxy(unittest.TestCase):
    def setUp(self):
        self.default_args = []

    def test_init(self):
        galaxy_cli = GalaxyCLI(args=self.default_args)
        self.assertTrue(isinstance(galaxy_cli, GalaxyCLI))

    def test_display_min(self):
        gc = GalaxyCLI(args=self.default_args)
        role_info = {'name': 'some_role_name'}
        display_result = gc._display_role_info(role_info)
        self.assertTrue(display_result.find('some_role_name') >-1)

    def test_display_galaxy_info(self):
        gc = GalaxyCLI(args=self.default_args)
        galaxy_info = {}
        role_info = {'name': 'some_role_name',
                     'galaxy_info': galaxy_info}
        display_result = gc._display_role_info(role_info)
        if display_result.find('\t\tgalaxy_tags:') > -1:
            self.fail('Expected galaxy_tags to be indented twice')

    def make_tarfile(self, output_file, source_dir):
        ''' used for making a tarfile from an artificial role directory for testing installation with a local tar.gz file '''
        # adding directory into a tar file
        try:
            tar = tarfile.open(output_file, "w:gz")
            tar.add(source_dir, arcname=os.path.basename(source_dir))
        except AttributeError: # tarfile obj. has no attribute __exit__ prior to python 2.7
            pass
        finally:  # ensuring closure of tarfile obj
            tar.close()

    def create_role(self):
        ''' creates a "role" directory and a requirements file; used for testing installation '''
        if os.path.exists('./delete_me'):
            shutil.rmtree('./delete_me')

        # making the directory for the role
        os.makedirs('./delete_me')
        os.makedirs('./delete_me/meta')

        # making main.yml for meta folder
        fd = open("./delete_me/meta/main.yml", "w")
        fd.write("---\ngalaxy_info:\n  author: 'shertel'\n  company: Ansible\ndependencies: []")
        fd.close()

        # making the directory into a tar file
        self.make_tarfile('./delete_me.tar.gz', './delete_me')

        # removing directory
        shutil.rmtree('./delete_me')

        # creating requirements.yml for installing the role
        fd = open("./delete_requirements.yml", "w")
        fd.write("- 'src': './delete_me.tar.gz'\n  'name': 'delete_me'\n  'path': '/etc/ansible/roles'")
        fd.close()

    def test_execute_install(self):
        ### testing insufficient information; no role name ###
        gc = GalaxyCLI(args=["install"])
        with patch('sys.argv', ["-c", "-v"]):
            galaxy_parser = gc.parse()
        with patch.object(ansible.cli.CLI, "run"):  # eliminate config file message
            self.assertRaises(AnsibleError, gc.run)

        ### tests installing a role with a local tar file ###
        # creating a tar.gz file for a fake role
        self.create_role()

        # installing role (also, removes tar.gz file)
        gc = GalaxyCLI(args=["install"])
        with patch('sys.argv', ["--offline", "-r", "delete_requirements.yml"]):
            galaxy_parser = gc.parse()
        with patch.object(ansible.utils.display.Display, "display") as mock_obj:
            super(GalaxyCLI, gc).run()
            gc.api = ansible.galaxy.api.GalaxyAPI(gc.galaxy)
            completed_task = gc.execute_install()

            # testing correct installation
            calls = [call('- extracting delete_me to /etc/ansible/roles/delete_me'), call('- delete_me was installed successfully')]
            mock_obj.assert_has_calls(calls)
            self.assertTrue(completed_task == 0)

        # deleting role
        gc.args = ["remove"]
        with patch('sys.argv', ["-c", "delete_me"]):
            galaxy_parser = gc.parse()
        with patch.object(ansible.utils.display.Display, "display") as mock_obj:
            gc.run()

        # cleaning up requirements file
        if os.path.isfile("delete_requirements.yml"):
            os.remove("delete_requirements.yml")

        # cleaning up tar.gz file
        if os.path.exists("./delete_me.tar.gz"):
            os.remove("./delete_me.tar.gz")

        ### tests downloading a role from ansible-galaxy ###
        # TODO/FIXME

