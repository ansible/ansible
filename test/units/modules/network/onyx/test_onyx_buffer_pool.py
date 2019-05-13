#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_buffer_pool
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxBufferPoolModule(TestOnyxModule):

    module = onyx_buffer_pool
    buffer_pool_configured = False

    def setUp(self):
        super(TestOnyxBufferPoolModule, self).setUp()
        self.mock_get_buffer_pool_config = patch.object(
            onyx_buffer_pool.OnyxBufferPoolModule, "_show_traffic_pool")
        self.get_buffer_pool_config = self.mock_get_buffer_pool_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxBufferPoolModule, self).tearDown()
        self.mock_get_buffer_pool_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        buffer_pool_config_file = 'onyx_buffer_pool.cfg'
        self.get_buffer_pool_config.return_value = None

        if self.buffer_pool_configured is True:
            buffer_pool_data = load_fixture(buffer_pool_config_file)
            self.get_buffer_pool_config.return_value = buffer_pool_data

        self.load_config.return_value = None

    def test_buffer_pool_no_change(self):
        self.buffer_pool_configured = True
        set_module_args(dict(name="roce", pool_type="lossless",
                             memory_percent=50.0, switch_priority=3))
        self.execute_module(changed=False)

    def test_buffer_pool_with_change(self):
        set_module_args(dict(name="roce", pool_type="lossless",
                             memory_percent=50.0, switch_priority=3))
        commands = ["traffic pool roce type lossless",
                    "traffic pool roce memory percent 50.0",
                    "traffic pool roce map switch-priority 3"
                    ]
        self.execute_module(changed=True, commands=commands)

    def test_memory_percent_with_change(self):
        self.buffer_pool_configured = True
        set_module_args(dict(name="roce", pool_type="lossless",
                             memory_percent=60.0, switch_priority=3))
        commands = ["traffic pool roce memory percent 60.0"]
        self.execute_module(changed=True, commands=commands)

    def test_switch_priority_with_change(self):
        self.buffer_pool_configured = True
        set_module_args(dict(name="roce", pool_type="lossless",
                             memory_percent=50.0, switch_priority=5))
        commands = ["traffic pool roce map switch-priority 5"]
        self.execute_module(changed=True, commands=commands)

    def test_pool_type_with_change(self):
        self.buffer_pool_configured = True
        set_module_args(dict(name="roce", memory_percent=50.0, switch_priority=3))
        commands = ["traffic pool roce type lossy"]
        self.execute_module(changed=True, commands=commands)
