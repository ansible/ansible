# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible.compat.tests import unittest

from ansible.config.manager import ConfigManager, Setting, ensure_type, resolve_path, find_ini_config_file

curdir = os.path.dirname(__file__)
cfg_file = os.path.join(curdir, 'test.cfg')
cfg_file2 = os.path.join(curdir, 'test2.cfg')

expected_ini = {'CONFIG_FILE': Setting(name='CONFIG_FILE', value=cfg_file, origin='', type='string'),
                'config_entry': Setting(name='config_entry', value=u'fromini', origin=cfg_file, type='string'),
                'config_entry_bool': Setting(name='config_entry_bool', value=False, origin=cfg_file, type='bool'),
                'config_entry_list': Setting(name='config_entry_list', value=['fromini'], origin=cfg_file, type='list'),
                'config_entry_deprecated': Setting(name='config_entry_deprecated', value=u'fromini', origin=cfg_file, type='string'),
                'config_entry_multi': Setting(name='config_entry_multi', value=u'morefromini', origin=cfg_file, type='string'),
                'config_entry_multi_deprecated': Setting(name='config_entry_multi_deprecated', value=u'morefromini', origin=cfg_file, type='string'),
                'config_entry_multi_deprecated_source': Setting(name='config_entry_multi_deprecated_source', value=u'morefromini',
                                                                origin=cfg_file, type='string')}


class TestConfigData(unittest.TestCase):

    def setUp(self):
        self.manager = ConfigManager(cfg_file, os.path.join(curdir, 'test.yml'))

    def tearDown(self):
        self.manager = None

    def test_initial_load(self):
        self.assertEquals(self.manager.data._global_settings, expected_ini)

    def test_ensure_type_list(self):
        self.assertIsInstance(ensure_type('a,b', 'list'), list)
        self.assertIsInstance(ensure_type(['a', 'b'], 'list'), list)

    def test_ensure_type_bool(self):
        self.assertIsInstance(ensure_type('yes', 'bool'), bool)
        self.assertIsInstance(ensure_type(True, 'bool'), bool)

    def test_ensure_type_int(self):
        self.assertIsInstance(ensure_type('10', 'int'), int)
        self.assertIsInstance(ensure_type(20, 'int'), int)

    def test_ensure_type_float(self):
        self.assertIsInstance(ensure_type('0.10', 'float'), float)
        self.assertIsInstance(ensure_type(0.2, 'float'), float)

    def test_find_ini_file(self):
        cur_config = os.environ['ANSIBLE_CONFIG']
        os.environ['ANSIBLE_CONFIG'] = cfg_file
        self.assertEquals(cfg_file, find_ini_config_file())
        os.environ['ANSIBLE_CONFIG'] = cur_config

    def test_resolve_path(self):
        self.assertEquals(os.path.join(curdir, 'test.yml'), resolve_path('./test.yml', cfg_file))

    def test_resolve_path_cwd(self):
        self.assertEquals(os.path.join(os.getcwd(), 'test.yml'), resolve_path('{{CWD}}/test.yml'))
        self.assertEquals(os.path.join(os.getcwd(), 'test.yml'), resolve_path('./test.yml'))

    def test_get_config_dest(self):
        pass

    def test_value_and_origin_from_ini(self):
        self.assertEquals(self.manager.get_config_value_and_origin('config_entry'), ('fromini', cfg_file))

    def test_value_from_ini(self):
        self.assertEquals(self.manager.get_config_value('config_entry'), 'fromini')

    def test_value_and_origin_from_alt_ini(self):
        self.assertEquals(self.manager.get_config_value_and_origin('config_entry', cfile=cfg_file2), ('fromini2', cfg_file2))

    def test_value_from_alt_ini(self):
        self.assertEquals(self.manager.get_config_value('config_entry', cfile=cfg_file2), 'fromini2')

    def test_value_and_origin_from_yaml(self):
        pass

    def test_value_from_yaml(self):
        pass

    def test_value_and_origin_from_alt_yaml(self):
        pass

    def test_value_from_alt_yaml(self):
        pass

    def test_config_type_bool(self):
        pass

    def test_config_type_list(self):
        pass

    def test_config_default(self):
        pass

    def test_deprecated_config(self):
        pass

    def test_deprecated_config_source(self):
        pass

    def test_multi_precedence(self):
        pass

    def test_initialize_plugin_config(self):
        pass

    def test_update_config_data(self):
        pass
