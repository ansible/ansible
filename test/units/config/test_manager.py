# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible.compat.tests import unittest

from ansible.config.manager import ConfigManager, Setting

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
        self.manager = ConfigManager(os.path.join(curdir, 'test.cfg'), os.path.join(curdir, 'test.yml'))

    def tearDown(self):
        self.manager = None

    def test_initial_load(self):
        self.assertEquals(self.manager.data._global_settings, expected_ini)

    def test_value_and_origin_from_ini(self):
        self.assertEquals(self.manager.get_config_value_and_origin('config_entry'), ('fromini', cfg_file))

    def test_value_from_ini(self):
        self.assertEquals(self.manager.get_config_value('config_entry'), 'fromini')

    def test_value_and_origin_from_alt_ini(self):
        self.assertEquals(self.manager.get_config_value_and_origin('config_entry', cfile=cfg_file2), ('fromini2', cfg_file2))

    def test_value_from_alt_ini(self):
        self.assertEquals(self.manager.get_config_value('config_entry', cfile=cfg_file2), 'fromini2')
