# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import tempfile

from ansible.compat.tests import unittest
from ansible.module_utils.six.moves import configparser

from ansible.config import manager


class TestConfigManager(unittest.TestCase):
    def tearDown(self):
        os.unlink(self.tmp_file.name)

    def _config_file(self, contents=None):

        self.tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.cfg')
        ini_config = configparser.ConfigParser()
        for item in contents:
            ini_config.add_section(item['section'])
            ini_config.set('defaults', item['name'], item['value'])

        ini_config.write(self.tmp_file)
        self.tmp_file.close()
        return self.tmp_file

    def test_hostfile(self):
        _cfg_file = self._config_file(contents=[{'section': 'defaults',
                                                 'name': 'hostfile',
                                                 'value': '/dev/null/a.yml'}])
        cm = manager.ConfigManager(conf_file=_cfg_file.name)
        hostfile = cm.data.get_setting('DEFAULT_HOST_LIST')
        self.assertEqual(hostfile.value, ['/dev/null/a.yml'])

    def test_inventory_ignore_patterns(self):
        _cfg_file = self._config_file(contents=[{'section': 'defaults',
                                                 'name': 'inventory_ignore_patterns',
                                                 'value': '/dev/null/foo,/dev/null/bar'}])
        cm = manager.ConfigManager(conf_file=_cfg_file.name)
        inventory_patterns = cm.data.get_setting('INVENTORY_IGNORE_PATTERNS')
        self.assertEqual(inventory_patterns.value, ['/dev/null/foo', '/dev/null/bar'])
