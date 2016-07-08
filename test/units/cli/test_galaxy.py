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
from mock import patch, call

from ansible.errors import AnsibleOptionsError

from nose.plugins.skip import SkipTest
import ansible

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

    def test_parse(self):
        ''' systematically testing that the expected options parser is created '''
        # testing no action given
        gc = GalaxyCLI(args=[])
        with patch('sys.argv', ["-c"]):
            self.assertRaises(AnsibleOptionsError, gc.parse)
                                                
        # testing action that doesn't exist
        gc = GalaxyCLI(args=["NOT_ACTION"])
        with patch('sys.argv', ["-c"]):
            self.assertRaises(AnsibleOptionsError, gc.parse)

        # testing action 'delete'
        gc = GalaxyCLI(args=["delete"])    
        with patch.object(ansible.cli.SortedOptParser, "set_usage") as mocked_usage:
            with patch('sys.argv', ["-c"]):
                galaxy_parser = gc.parse()

                # tests
                self.assertTrue(galaxy_parser)
                self.assertTrue(isinstance(gc.parser, ansible.cli.SortedOptParser))
                self.assertTrue(isinstance(gc.galaxy, ansible.galaxy.Galaxy))
                calls = [call('usage: %prog [delete|import|info|init|install|list|login|remove|search|setup] [--help] [options] ...'), call('usage: %prog delete [options] github_user github_repo')]
                mocked_usage.assert_has_calls(calls)
                self.assertTrue(gc.options.verbosity==0)
        
        # testing action 'import'
        gc = GalaxyCLI(args=["import"])
        with patch.object(ansible.cli.SortedOptParser, "set_usage") as mocked_usage:
            with patch('sys.argv', ["-c"]):
                galaxy_parser = gc.parse()

                # tests
                self.assertTrue(galaxy_parser)
                self.assertTrue(isinstance(gc.parser, ansible.cli.SortedOptParser))
                self.assertTrue(isinstance(gc.galaxy, ansible.galaxy.Galaxy))                
                calls = [call('usage: %prog [delete|import|info|init|install|list|login|remove|search|setup] [--help] [options] ...'), call('usage: %prog import [options] github_user github_repo')]
                mocked_usage.assert_has_calls(calls)
                self.assertTrue(gc.options.wait==True)
                self.assertTrue(gc.options.reference==None)
                self.assertTrue(gc.options.check_status==False)
                self.assertTrue(gc.options.verbosity==0)


        # testing action 'info'
        gc = GalaxyCLI(args=["info"])
        with patch.object(ansible.cli.SortedOptParser, "set_usage") as mocked_usage:
            with patch('sys.argv', ["-c"]):
                galaxy_parser = gc.parse()

                # tests
                self.assertTrue(galaxy_parser)
                self.assertTrue(isinstance(gc.parser, ansible.cli.SortedOptParser))
                self.assertTrue(isinstance(gc.galaxy, ansible.galaxy.Galaxy))                
                calls = [call('usage: %prog [delete|import|info|init|install|list|login|remove|search|setup] [--help] [options] ...'), call('usage: %prog info [options] role_name[,version]')]
                mocked_usage.assert_has_calls(calls)
                self.assertTrue(gc.options.offline==False)

        # testing action 'init'
        gc = GalaxyCLI(args=["init"])
        with patch.object(ansible.cli.SortedOptParser, "set_usage") as mocked_usage:
            with patch('sys.argv', ["-c"]):
                galaxy_parser = gc.parse()

                # tests
                self.assertTrue(galaxy_parser)
                self.assertTrue(isinstance(gc.parser, ansible.cli.SortedOptParser))
                self.assertTrue(isinstance(gc.galaxy, ansible.galaxy.Galaxy))                
                calls = [call('usage: %prog [delete|import|info|init|install|list|login|remove|search|setup] [--help] [options] ...'), call('usage: %prog init [options] role_name')]
                mocked_usage.assert_has_calls(calls)
                self.assertTrue(gc.options.offline==False)
                self.assertTrue(gc.options.force==False)

        # testing action 'install'
        gc = GalaxyCLI(args=["install"])
        with patch.object(ansible.cli.SortedOptParser, "set_usage") as mocked_usage:
            with patch('sys.argv', ["-c"]):
                galaxy_parser = gc.parse()

                # tests
                self.assertTrue(galaxy_parser)
                self.assertTrue(isinstance(gc.parser, ansible.cli.SortedOptParser))
                self.assertTrue(isinstance(gc.galaxy, ansible.galaxy.Galaxy))                
                calls = [call('usage: %prog [delete|import|info|init|install|list|login|remove|search|setup] [--help] [options] ...'), call('usage: %prog install [options] [-r FILE | role_name(s)[,version] | scm+role_repo_url[,version] | tar_file(s)]')]
                mocked_usage.assert_has_calls(calls)
                self.assertTrue(gc.options.ignore_errors==False)
                self.assertTrue(gc.options.no_deps==False)
                self.assertTrue(gc.options.role_file==None)
                self.assertTrue(gc.options.force==False)

        # testing action 'list'
        gc = GalaxyCLI(args=["list"])
        with patch.object(ansible.cli.SortedOptParser, "set_usage") as mocked_usage:
            with patch('sys.argv', ["-c"]):
                galaxy_parser = gc.parse()

                # tests
                self.assertTrue(galaxy_parser)
                self.assertTrue(isinstance(gc.parser, ansible.cli.SortedOptParser))
                self.assertTrue(isinstance(gc.galaxy, ansible.galaxy.Galaxy))                
                calls = [call('usage: %prog [delete|import|info|init|install|list|login|remove|search|setup] [--help] [options] ...'), call('usage: %prog list [role_name]')]
                mocked_usage.assert_has_calls(calls)
                self.assertTrue(gc.options.verbosity==0)

        # testing action 'login'
        gc = GalaxyCLI(args=["login"])
        with patch.object(ansible.cli.SortedOptParser, "set_usage") as mocked_usage:
            with patch('sys.argv', ["-c"]):
                galaxy_parser = gc.parse()

                # tests
                self.assertTrue(galaxy_parser)
                self.assertTrue(isinstance(gc.parser, ansible.cli.SortedOptParser))
                self.assertTrue(isinstance(gc.galaxy, ansible.galaxy.Galaxy))                
                calls = [call('usage: %prog [delete|import|info|init|install|list|login|remove|search|setup] [--help] [options] ...'), call('usage: %prog login [options]')]
                mocked_usage.assert_has_calls(calls)
                self.assertTrue(gc.options.verbosity==0)
                self.assertTrue(gc.options.token==None)

        # testing action 'remove'
        gc = GalaxyCLI(args=["remove"])
        with patch.object(ansible.cli.SortedOptParser, "set_usage") as mocked_usage:
            with patch('sys.argv', ["-c"]):
                galaxy_parser = gc.parse()

                # tests
                self.assertTrue(galaxy_parser)
                self.assertTrue(isinstance(gc.parser, ansible.cli.SortedOptParser))
                self.assertTrue(isinstance(gc.galaxy, ansible.galaxy.Galaxy))                
                calls = [call('usage: %prog [delete|import|info|init|install|list|login|remove|search|setup] [--help] [options] ...'), call('usage: %prog remove role1 role2 ...')]
                mocked_usage.assert_has_calls(calls)
                self.assertTrue(gc.options.verbosity==0)

        # testing action 'search'
        gc = GalaxyCLI(args=["search"])
        with patch.object(ansible.cli.SortedOptParser, "set_usage") as mocked_usage:
            with patch('sys.argv', ["-c"]):
                galaxy_parser = gc.parse()

                # tests
                self.assertTrue(galaxy_parser)
                self.assertTrue(isinstance(gc.parser, ansible.cli.SortedOptParser))
                self.assertTrue(isinstance(gc.galaxy, ansible.galaxy.Galaxy))                
                calls = [call('usage: %prog [delete|import|info|init|install|list|login|remove|search|setup] [--help] [options] ...'), call('usage: %prog search [searchterm1 searchterm2] [--galaxy-tags galaxy_tag1,galaxy_tag2] [--platforms platform1,platform2] [--author username]')]
                mocked_usage.assert_has_calls(calls)
                self.assertTrue(gc.options.platforms==None)
                self.assertTrue(gc.options.tags==None)
                self.assertTrue(gc.options.author==None)

        # testing action 'setup'
        gc = GalaxyCLI(args=["setup"])
        with patch.object(ansible.cli.SortedOptParser, "set_usage") as mocked_usage:
            with patch('sys.argv', ["-c"]):
                galaxy_parser = gc.parse()

                # tests
                self.assertTrue(galaxy_parser)
                self.assertTrue(isinstance(gc.parser, ansible.cli.SortedOptParser))
                self.assertTrue(isinstance(gc.galaxy, ansible.galaxy.Galaxy))                
                calls = [call('usage: %prog [delete|import|info|init|install|list|login|remove|search|setup] [--help] [options] ...'), call('usage: %prog setup [options] source github_user github_repo secret')]
                mocked_usage.assert_has_calls(calls)
                self.assertTrue(gc.options.verbosity==0)
                self.assertTrue(gc.options.remove_id==None)
                self.assertTrue(gc.options.setup_list==False)

