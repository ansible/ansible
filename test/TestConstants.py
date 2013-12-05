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


    #####################################
    ### load_constants unit tests

    def test_configfile_load_expansion(self):
        import ansible.constants as C
        r = 'TEST_C' + random_string(6)
        v = '~/path'
        table = "%s   test  TEST  %s  X" % (r ,v)
        C.load_constants(table)
        assert C.__dict__[r] != v
        assert C.__dict__[r].endswith('/path')

    def test_configfile_load_envflag(self):
        import ansible.constants as C
        r = 'TEST_C' + random_string(6)
        v = 'newstuff'
        C.__dict__['ANSIBLE_'+r] = v
        table = "%s   test  TEST  %s  G" % (r ,'ANSIBLE_'+r)
        C.load_constants(table)
        assert C.__dict__[r] == v

    #####################################
    ### reload_config unit tests

    def test_configfile_reload(self):
        import ansible.constants as C 
        assert C.DEFAULT_HOST_LIST == '/etc/ansible/hosts'
        C.reload_config(os.path.dirname(__file__))
        assert C.DEFAULT_HOST_LIST == './ansible_hosts'

