# -*- coding: utf-8 -*-

import unittest

from ansible.constants import get_config
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
