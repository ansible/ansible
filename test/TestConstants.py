# -*- coding: utf-8 -*-

import unittest

from ansible.constants import get_config, combine_config, shell_expand_path
import ConfigParser
import random
import string
import os


def random_string(length):
    return ''.join(random.choice(string.ascii_uppercase) for x in range(6))

p = ConfigParser.ConfigParser()
p.read(os.path.join(os.path.dirname(__file__), 'ansible.cfg'))

class TestConstants(unittest.TestCase):

    #####################################
    ### get_config unit tests

    
    def test_configfile_and_env_both_set(self):
        r = random_string(6)
        env_var = 'ANSIBLE_TEST_%s' % r
        os.environ[env_var] = r

        res = get_config(p, 'defaults', 'test_key', env_var, 'default')
        del os.environ[env_var]

        assert res == r


    def test_configfile_set_env_not_set(self):
        r = random_string(6)
        env_var = 'ANSIBLE_TEST_%s' % r
        assert env_var not in os.environ
        
        res = get_config(p, 'defaults', 'test_key', env_var, 'default')

        print res
        assert res == 'test_value'


    def test_configfile_not_set_env_set(self):
        r = random_string(6)
        env_var = 'ANSIBLE_TEST_%s' % r
        os.environ[env_var] = r

        res = get_config(p, 'defaults', 'doesnt_exist', env_var, 'default')
        del os.environ[env_var]

        assert res == r


    def test_configfile_not_set_env_not_set(self):
        r = random_string(6)
        env_var = 'ANSIBLE_TEST_%s' % r
        assert env_var not in os.environ
        
        res = get_config(p, 'defaults', 'doesnt_exist', env_var, 'default')

        assert res == 'default'


    def test_combine_paths_all_set(self):
        r = random_string(6)
        env_var = 'ANSIBLE_TEST_%s' % r
        os.environ[env_var] = r
        
        res = combine_config(p, 'defaults', 'test_key', env_var, 'default')
        del os.environ[env_var]
        assert res == os.pathsep.join([r, 'test_value', 'default'])


    def test_combine_paths_configfile_set_env_var_not_set(self):
        r = random_string(6)
        env_var = 'ANSIBLE_TEST_%s' % r
        assert env_var not in os.environ
        
        res = combine_config(p, 'defaults', 'test_key', env_var, 'default')
        assert res == os.pathsep.join(['test_value', 'default'])


    def test_combine_paths_configfile_not_set_env_var_set(self):
        r = random_string(6)
        env_var = 'ANSIBLE_TEST_%s' % r
        os.environ[env_var] = r
        
        res = combine_config(p, 'defaults', 'doesnt_exist', env_var, 'default')
        del os.environ[env_var]
        assert res == os.pathsep.join([r, 'default'])


    def test_combine_paths_configfile_not_set_env_var_not_set(self):
        r = random_string(6)
        env_var = 'ANSIBLE_TEST_%s' % r
        assert env_var not in os.environ
        
        res = combine_config(p, 'defaults', 'doesnt_exist', env_var, 'default')
        assert res == 'default'


    def test_combine_paths_nothing_set(self):
        r = random_string(6)
        env_var = 'ANSIBLE_TEST_%s' % r
        assert env_var not in os.environ
        
        res = combine_config(p, 'defaults', 'doesnt_exist', env_var)
        assert res == ''


    def test_shell_expand_path_expands_multiple_diretories(self):
        p = shell_expand_path(os.pathsep.join(['hello', '~/test', 'goodbye']))

        assert p == 'hello' + os.pathsep + os.path.expanduser('~/test') + os.pathsep + 'goodbye'
