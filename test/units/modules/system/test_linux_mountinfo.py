import os
import tempfile

from ansible.compat.tests import unittest
from ansible.module_utils._text import to_bytes

from ansible.modules.system.mount import get_linux_mounts


class LinuxMountsTestCase(unittest.TestCase):

    def _create_file(self, content):
        tmp_file = tempfile.NamedTemporaryFile(prefix='ansible-test-', delete=False)
        tmp_file.write(to_bytes(content))
        tmp_file.close()
        self.addCleanup(os.unlink, tmp_file.name)
        return tmp_file.name

    def test_code_comment(self):
        path = self._create_file(
            '140 136 253:2 /rootfs / rw - ext4 /dev/sdb2 rw\n'
            '141 140 253:2 /rootfs/tmp/aaa /tmp/bbb rw - ext4 /dev/sdb2 rw\n'
        )
        mounts = get_linux_mounts(None, path)
        self.assertEqual(mounts['/tmp/bbb']['src'], '/tmp/aaa')
