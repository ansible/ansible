import functools
import sys

from ansible.compat.tests import mock
from ansible.compat.tests import unittest

try:
    import ansible.modules.packaging.os.apk
except:
    # Need some more module_utils work (porting urls.py) before we can test
    # modules.  So don't error out in this case.
    if sys.version_info[0] >= 3:
        pass


class ApkInstallPackagesTestCase(unittest.TestCase):

    @mock.patch('ansible.modules.packaging.os.apk.APK_PATH', 'apkpath', create=True)
    @mock.patch('ansible.modules.packaging.os.apk.query_package')
    @mock.patch('ansible.modules.packaging.os.apk.query_latest', return_value=False)
    @mock.patch('ansible.modules.packaging.os.apk.query_virtual', return_value=False)
    def test_both_toInstall_and_toUpgrade_latest(self, _mock1, _mock2, mock_query_package):
        mock_module = mock.MagicMock()
        mock_module.check_mode = False

        def result_run_command(cmd, check_rc, mock):
            mock.cmd = cmd
            return (0, '', '')
        mock_module.run_command.side_effect = functools.partial(result_run_command, mock=mock_module)

        def result_query_package(module, name):
            if name == 'toInstall':
                return False
            return True
        mock_query_package.side_effect = result_query_package

        ansible.modules.packaging.os.apk.install_packages(mock_module, ['toInstall', 'toUpgrade'], 'latest')
        assert mock_module.cmd == 'apkpath add --upgrade toInstall toUpgrade'
